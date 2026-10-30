#!/usr/bin/env python3
"""Find edition names that are *assembled*, which plain grep cannot see.

Python files are parsed: every string-building expression (f-string, +, %, .format, .join,
os.path.join, Path / ...) is folded into a template where non-constant parts become {} and
case/replace transforms on them are recorded. Templates are then matched against the old
naming shapes. Other languages get a token-level scan.

usage: bcp47_composite_scan.py [ROOT ...]   (default: repo root and the Bible_Noun_Extraction submodule)
Exit 1 if anything is flagged. See Meta_Bible_Data/docs/bcp47_naming.md.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", "build", "dist", ".gradle", "logs",
             "reports_archive", "sweep_history", "legacy_backup", "archive", "local_backups"}
# Deliberate alias tables mapping old IDs to new ones; their literals are expected.
ALLOW = {"Apps/GOIBible_desktop/goibible/state.py", "Apps/GOIBible_desktop/goibible/paths.py", "Apps/GOIBible_android/app/src/main/java/com/example/goibible/data/BibleRepo.kt",
         "Meta_Bible_Data/full_bible/generate_markdown_bible.py", "tools/bcp47_composite_scan.py", "tools/bcp47_tripwire.py"}
# Files whose standalone fragments ('Hans', 'English', ...) were read by hand on 2026-10-28: display names,
# substring tests on the suffix, or loops over the new GOI_zh-{ed} form. Re-review if they change.
REVIEWED = {"Meta_Bible_Data/Bible_Noun_Extraction/checks_en.py", "Meta_Bible_Data/Bible_Noun_Extraction/checks_zh.py",
            "Meta_Bible_Data/Bible_Noun_Extraction/zh/verify_current_artifacts.py",
            "Meta_Bible_Data/Bible_Noun_Extraction/zh/apply_reviewed_cleanup.py",
            "Meta_Bible_Data/Bible_Noun_Extraction/zh/verify_script_pair.py"}

OLD_LITERAL = re.compile(r"GOI_Bible_(English|Chinese)|GOI_Zh_|Chinese_Han[st]|\bzh_han[st]\b")
SHAPES = [
    (re.compile(r"GOI_Bible_\{[^}]*(capitalize|title|upper)"), "case transform on a tag in a dir name (BCP 47 dir is exact case)"),
    (re.compile(r"GOI_\{[^}]*(capitalize|title|upper)"), "case transform on a tag in an edition ID/suffix"),
    (re.compile(r"GOI_(Bible_)?\{[^}]*\}_\{"), "two parts joined by '_' after GOI_ (lang + script composite)"),
    (re.compile(r"GOI_(Bible_)?\{[^}]*replace\(-,_"), "tag hyphen replaced by underscore"),
    (re.compile(r"GOI_(Bible_)?(Chinese|English|Zh)(_|\{|$)"), "old name prefix with a variable tail"),
    (re.compile(r"(^|[^A-Za-z])(Chinese|Zh)_$"), "fragment ending in Chinese_/Zh_ (old composite prefix)"),
]


def fold(node: ast.AST) -> str:
    """Render a string-building expression as a template; unknown parts become {...}."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(fold(v) for v in node.values)
    if isinstance(node, ast.FormattedValue):
        return "{" + hint(node.value) + "}"
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Div)):
        sep = "/" if isinstance(node.op, ast.Div) else ""
        return fold(node.left) + sep + fold(node.right)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
        return re.sub(r"%[sdr]", "{}", node.left.value)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "format" and isinstance(node.func.value, ast.Constant) and isinstance(node.func.value.value, str):
            return re.sub(r"\{[^}]*\}", "{}", node.func.value.value)
        if node.func.attr == "join" and node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
            sep = node.func.value.value if isinstance(node.func.value, ast.Constant) and isinstance(node.func.value.value, str) else "/"
            return sep.join(fold(e) for e in node.args[0].elts)
        if node.func.attr in {"join", "joinpath"}:  # os.path.join(a, b), p.joinpath(a)
            return "/".join(fold(a) for a in node.args)
    return "{" + hint(node) + "}"


def hint(node: ast.AST) -> str:
    """Name the transforms applied to a non-constant part (capitalize, replace(-,_), ...)."""
    out = []
    while isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        name = node.func.attr
        if name == "replace" and len(node.args) == 2 and all(isinstance(a, ast.Constant) for a in node.args):
            name = f"replace({node.args[0].value},{node.args[1].value})"
        out.append(name)
        node = node.func.value
    return ".".join(reversed(out))


def scan_python(path: Path, rel: str, src: str) -> list[str]:
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:  # e.g. vendored Python 2; only matters if it names GOI editions
        return [f"{rel}:{exc.lineno}: cannot parse ({exc.msg}); scan by hand"] if "GOI" in src else []
    hits = []
    seen = set()
    docstrings = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
    for node in ast.walk(tree):
        # decomposition: a filename split apart and its pieces compared (['GOI','Zh',ed], len(x.split('_')) == 7)
        if isinstance(node, (ast.List, ast.Tuple)) and any(isinstance(e, ast.Constant) and e.value == "GOI" for e in node.elts):
            hits.append(f"{rel}:{node.lineno}: decomposed suffix literal (compare '_'.join(parts) to the edition ID instead): {ast.unparse(node)[:100]!r}")
        if isinstance(node, ast.Compare):
            consts = [c.value for c in [node.left, *node.comparators] if isinstance(c, ast.Constant)]
            if any(c in {"Zh", "Zh_", "Chinese", "English"} for c in consts):
                hits.append(f"{rel}:{node.lineno}: compares against an old name fragment: {ast.unparse(node)[:100]!r}")
            text = ast.unparse(node)
            if "split('_')" in text and re.search(r"len\(", text) and any(isinstance(c, int) and c >= 6 for c in consts):
                hits.append(f"{rel}:{node.lineno}: filename part-count check (breaks when a suffix changes shape): {text[:100]!r}")
        if not isinstance(node, (ast.JoinedStr, ast.BinOp, ast.Call, ast.Constant)) or id(node) in docstrings:
            continue
        tmpl = fold(node)
        line = getattr(node, "lineno", 0)
        for rx, why in [(OLD_LITERAL, "old name literal")] + SHAPES:
            if rx.search(tmpl) and (line, why) not in seen:
                seen.add((line, why))
                hits.append(f"{rel}:{line}: {why}: {tmpl[:120]!r}")
    # composite across statements: a GOI_ literal plus standalone script/lang fragments in the same file
    consts = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    if rel not in REVIEWED and any(c.startswith("GOI_") or "GOI_Bible" in c for c in consts):
        frags = sorted(c for c in consts if c in {"Hans", "Hant", "Chinese", "English", "Zh", "Zh_"})
        if frags:
            hits.append(f"{rel}: GOI_ literal plus standalone fragments {frags}; check how they combine")
    return hits


OTHER = [
    (OLD_LITERAL, "old name literal"),
    (re.compile(r"GOI_(Bible_)?\$\{?\w+\}?_\$"), "two variables joined by '_' after GOI_"),
    (re.compile(r"GOI_(Bible_)?(\$|\{\$|\"\s*\.\s*\$|\"\s*\+)\s*\w*\s*\.?\s*(ucfirst|capitalize|replaceFirstChar|capitalized|toUpperCase|\^)"), "case transform on a tag"),
    (re.compile(r"ucfirst\(\s*\$\w*(lang|tag|edition)|\$\{\w+\^\}"), "case transform on a tag"),
    (re.compile(r"[\"'](Chinese|Zh)_[\"']"), "old composite prefix fragment"),
]


def scan_other(rel: str, src: str) -> list[str]:
    hits = []
    for i, line in enumerate(src.splitlines(), 1):
        for rx, why in OTHER:
            if rx.search(line):
                hits.append(f"{rel}:{i}: {why}: {line.strip()[:120]!r}")
    return hits


def main() -> int:
    roots = [Path(p).resolve() for p in sys.argv[1:]] or [ROOT]
    hits = []
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(root).parts):
                continue
            rel = str(path.relative_to(ROOT if path.is_relative_to(ROOT) else root))
            if rel in ALLOW:
                continue
            if path.suffix == ".py":
                hits += scan_python(path, rel, path.read_text(encoding="utf-8", errors="replace"))
            elif path.suffix in {".sh", ".php", ".kt", ".kts", ".swift", ".js", ".ps1", ".nsi"}:
                hits += scan_other(rel, path.read_text(encoding="utf-8", errors="replace"))
    print("\n".join(hits) if hits else "no composite or partial edition names found")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
