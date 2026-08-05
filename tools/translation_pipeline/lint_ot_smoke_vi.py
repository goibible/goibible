#!/usr/bin/env python3
"""Lint staged Vietnamese OT smoke output into red/orange/yellow/green queues."""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parents[2]
META = ROOT / "Meta_Bible_Data"
sys.path.insert(0, str(ROOT / "scripts"))

from translate_ot_smoke_vi import BOOK_NUMBERS, DEFAULT_OUT_DIR, DEFAULT_REFS, VIE1934_DIR, WLC_DIR, load_refs

DEFAULT_CSV = META / "staging" / "ot_smoke" / "GOI_vi_ot_smoke_lint.csv"
DEFAULT_MD = META / "staging" / "ot_smoke" / "GOI_vi_ot_smoke_lint.md"

SEVERITY_RANK = {"green": 0, "yellow": 1, "orange": 2, "red": 3}

RED_PATTERNS = [
    ("malformed_token", r"\bBấyng\b"),
    ("malformed_token", r"\btrần trụ\b"),
    ("wrong_word", r"\blàm cho bẩn\b"),
    ("wrong_word", r"\bnhạo lác\b"),
    ("wrong_word", r"\blinh hồn Ngài\b"),
    ("wrong_word", r"\bngầm từ chối Đức Giê-hô-va\b"),
    ("unwanted_english", r"\b(?:Satan|LORD|God|Lord|Jehovah)\b"),
    ("markdown_or_commentary", r"```|^[-*]\s|^Here is\b|^Translation\b"),
]

YELLOW_PATTERNS = [
    ("archaic_register", r"\bNầy\b"),
    ("archaic_register", r"\bsanh\b"),
    ("archaic_register", r"\bchúng nó\b"),
    ("archaic_register", r"\btừng trời\b"),
    ("archaic_register", r"\bchổi dậy\b"),
    ("awkward_register", r"\bsiêu cao\b"),
    ("awkward_register", r"\bngày được tạo nên\b"),
    ("awkward_register", r"\bĐức Giê-hô-va tôi ôi\b"),
    ("awkward_register", r"\bthần linh rộng rãi\b"),
    ("awkward_register", r"\bphỉ báng Ngài trước mặt\b"),
    ("awkward_register", r"\btrở về đó\b"),
]

NAME_VARIANTS = {
    "Sa-tan": re.compile(r"\bSa-tan\b"),
    "Sa-tăng": re.compile(r"\bSa-tăng\b"),
    "Satan": re.compile(r"\bSatan\b"),
}

VERSE_REQUIREMENTS = {
    "001_GEN_004_004": {
        "required": ["A-bên"],
        "forbidden": ["Hê-nên"],
        "note": "Abel must remain A-bên in Cain/Abel offering context.",
    },
    "001_GEN_005_005": {
        "required": ["A-đam", "chín trăm ba mươi"],
        "forbidden": ["Đức Chúa Trời sống"],
        "note": "Genealogy death-age verse must keep A-đam as the subject.",
    },
    "001_GEN_005_008": {
        "required": ["Sết", "chín trăm mười hai"],
        "forbidden": ["Mạt-thu-sê-la", "năm trăm tám mươi"],
        "note": "Seth total-age verse must not borrow Methuselah or another genealogy formula.",
    },
    "001_GEN_005_011": {
        "required": ["Ê-nót", "chín trăm lẻ năm"],
        "forbidden": ["Ê-nốt"],
        "note": "Enosh name/age consistency.",
    },
    "001_GEN_005_013": {
        "required": ["Kê-nan", "Ma-ha-la-le", "tám trăm bốn mươi"],
        "forbidden": ["bốn mươi năm và tám trăm năm"],
        "note": "Kenan post-begetting age must be 840.",
    },
    "001_GEN_005_017": {
        "required": ["Ma-ha-la-le", "tám trăm chín mươi lăm"],
        "forbidden": ["Ma-ha-la-ên", "chín mươi lăm năm và tám trăm"],
        "note": "Mahalalel total-age verse must be 895.",
    },
    "001_GEN_005_018": {
        "required": ["Giê-rết", "một trăm sáu mươi hai", "Hê-nóc"],
        "forbidden": ["Ê-rẹc", "hai trăm sáu mươi hai"],
        "note": "Jared begets Enoch at 162.",
    },
    "001_GEN_005_025": {
        "required": ["Mê-tu-sê-la", "một trăm tám mươi bảy", "Lê-méc"],
        "forbidden": ["bảy mươi hai năm và một trăm"],
        "note": "Methuselah begets Lamech at 187.",
    },
    "001_GEN_005_027": {
        "required": ["Mê-tu-sê-la", "chín trăm sáu mươi chín"],
        "forbidden": ["Mê-tu-sa-ên"],
        "note": "Methuselah total-age verse must be 969.",
    },
    "001_GEN_005_031": {
        "required": ["Lê-méc", "bảy trăm bảy mươi bảy"],
        "forbidden": ["Ê-nóc", "bảy trăm hai mươi"],
        "note": "Lamech total-age verse must be 777.",
    },
}

@dataclass
class Finding:
    severity: str
    category: str
    note: str


def bump(current: str, candidate: str) -> str:
    return candidate if SEVERITY_RANK[candidate] > SEVERITY_RANK[current] else current


def read_text(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def lint_file(path: pathlib.Path, stem: str, text: str, wlc: str, all_smoke_text: str) -> list[Finding]:
    findings: list[Finding] = []

    if not text:
        return [Finding("red", "empty", "Output file is missing or empty.")]

    if "\n" in text:
        findings.append(Finding("red", "format", "Verse output must be exactly one line."))

    if re.match(r"^\s*\d+[:.]\d+", text):
        findings.append(Finding("red", "format", "Verse includes a leading verse reference."))

    for category, pattern in RED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            findings.append(Finding("red", category, f"Matched red pattern: {pattern}"))

    for category, pattern in YELLOW_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            findings.append(Finding("yellow", category, f"Matched yellow pattern: {pattern}"))

    if "יהוה" in wlc and "Đức Giê-hô-va" not in text:
        findings.append(Finding("orange", "divine_name", "WLC has יהוה but output lacks Đức Giê-hô-va."))

    if stem == "023_ISA_052_015" and not re.search(r"\bvảy rửa\b|\brảy rửa\b|\blàm kinh ngạc\b", text, re.IGNORECASE):
        findings.append(
            Finding(
                "orange",
                "messianic_semantics",
                "ISA 52:15 needs reviewed wording for Hebrew yazzeh; it must not become defile/make dirty.",
            )
        )

    if stem == "019_PSA_022_016" and not re.search(r"\bđâm\b.*\btay\b.*\bchân\b|\btay\b.*\bchân\b.*\bđâm\b", text, re.IGNORECASE):
        findings.append(
            Finding(
                "orange",
                "messianic_semantics",
                "PSA 22:16 needs reviewed wording around hands/feet.",
            )
        )

    requirement = VERSE_REQUIREMENTS.get(stem)
    if requirement:
        for required in requirement["required"]:
            if required not in text:
                findings.append(
                    Finding(
                        "red",
                        "verse_requirement",
                        f"Missing required text {required!r}. {requirement['note']}",
                    )
                )
        for forbidden in requirement["forbidden"]:
            if forbidden in text:
                findings.append(
                    Finding(
                        "red",
                        "verse_requirement",
                        f"Contains forbidden text {forbidden!r}. {requirement['note']}",
                    )
                )

    present_satan_variants = [name for name, pattern in NAME_VARIANTS.items() if pattern.search(all_smoke_text)]
    local_satan_variants = [name for name, pattern in NAME_VARIANTS.items() if pattern.search(text)]
    if local_satan_variants and len(present_satan_variants) > 1:
        findings.append(
            Finding(
                "orange",
                "proper_name_consistency",
                f"Satan name variants appear in smoke set: {', '.join(present_satan_variants)}.",
            )
        )

    if re.search(r"\s{2,}", text):
        findings.append(Finding("yellow", "spacing", "Verse contains repeated spaces."))

    if not re.search(r"[.!?;:]$|[.!?;:][\"”]$", text):
        findings.append(Finding("yellow", "punctuation", "Verse does not end with sentence punctuation."))

    return findings or [Finding("green", "clean", "No lint findings.")]


def write_markdown(rows: list[dict[str, str]], path: pathlib.Path) -> None:
    grouped = {"red": [], "orange": [], "yellow": [], "green": []}
    for row in rows:
        grouped[row["severity"]].append(row)

    lines = [
        "# GOI Vietnamese OT Smoke Lint",
        "",
        "| Severity | Count |",
        "| --- | ---: |",
    ]
    for severity in ("red", "orange", "yellow", "green"):
        lines.append(f"| {severity} | {len(grouped[severity])} |")
    lines.append("")

    for severity in ("red", "orange", "yellow"):
        lines.extend([f"## {severity}", ""])
        for row in grouped[severity]:
            lines.extend(
                [
                    f"### {row['book']} {row['chapter']}:{row['verse']} - {row['categories']}",
                    "",
                    row["note"],
                    "",
                    f"- GOI_vi: {row['goi_vi']}",
                    f"- VIE1934: {row['vie1934']}",
                    f"- WLC: {row['wlc']}",
                    "",
                ]
            )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refs", type=pathlib.Path, default=DEFAULT_REFS)
    parser.add_argument("--output-dir", type=pathlib.Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--csv", type=pathlib.Path, default=DEFAULT_CSV)
    parser.add_argument("--markdown", type=pathlib.Path, default=DEFAULT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    refs = load_refs(args.refs)
    all_smoke_text = "\n".join(
        read_text(args.output_dir / f"{ref.stem}_GOI_vi.txt") for ref in refs
    )
    rows: list[dict[str, str]] = []

    for ref in refs:
        out = args.output_dir / f"{ref.stem}_GOI_vi.txt"
        wlc_path = WLC_DIR / f"{ref.stem}_WLC.txt"
        vie_path = VIE1934_DIR / f"{ref.stem}_VIE1934.txt"
        goi = read_text(out)
        wlc = read_text(wlc_path)
        vie1934 = read_text(vie_path)
        findings = lint_file(out, ref.stem, goi, wlc, all_smoke_text)
        severity = "green"
        for finding in findings:
            severity = bump(severity, finding.severity)
        notes = [f"{finding.severity}:{finding.category}: {finding.note}" for finding in findings]
        categories = sorted({finding.category for finding in findings if finding.category != "clean"})
        rows.append(
            {
                "book": ref.book,
                "chapter": str(ref.chapter),
                "verse": str(ref.verse),
                "stem": ref.stem,
                "severity": severity,
                "categories": ";".join(categories) or "clean",
                "note": " | ".join(notes),
                "goi_vi": goi,
                "vie1934": vie1934,
                "wlc": wlc,
            }
        )

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "book",
                "chapter",
                "verse",
                "stem",
                "severity",
                "categories",
                "note",
                "goi_vi",
                "vie1934",
                "wlc",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    write_markdown(rows, args.markdown)
    counts = {severity: 0 for severity in ("red", "orange", "yellow", "green")}
    for row in rows:
        counts[row["severity"]] += 1
    print(json.dumps(counts, ensure_ascii=False, sort_keys=True))
    print(f"CSV: {args.csv}")
    print(f"Markdown: {args.markdown}")


if __name__ == "__main__":
    main()
