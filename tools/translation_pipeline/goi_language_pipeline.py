#!/usr/bin/env python3
"""GOI language pipeline orchestration.

This wraps the repeatable parts of a language build so new editions follow the
same naming, validation, SQL, and download staging conventions.

Examples:
  python3 tools/translation_pipeline/goi_language_pipeline.py status GOI_vi
  python3 tools/translation_pipeline/goi_language_pipeline.py generate-nt GOI_vi --language-name Vietnamese --reference-dir Reference_Bible/Vietnamese_Bible_VIE1934/One_Directory_VIE1934
  python3 tools/translation_pipeline/goi_language_pipeline.py stage GOI_vi
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
META = ROOT / "Meta_Bible_Data"
CATALOG = META / "sqlite" / "editions.json"
NT_BOOKS = "MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB JAS 1PE 2PE 1JN 2JN 3JN JUD REV".split()


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def load_catalog() -> dict[str, dict[str, object]]:
    with CATALOG.open(encoding="utf-8") as handle:
        return {entry["edition_id"]: entry for entry in json.load(handle)}


def edition_config(edition_id: str) -> dict[str, object]:
    catalog = load_catalog()
    if edition_id not in catalog:
        raise SystemExit(f"unknown edition_id {edition_id!r}; add it to {CATALOG.relative_to(ROOT)}")
    return catalog[edition_id]


def corpus_dir(config: dict[str, object]) -> Path:
    return ROOT / str(config["flatfile_dir"])


def filename_suffix(config: dict[str, object]) -> str:
    return str(config.get("filename_suffix") or config["edition_id"])


def expected_count(config: dict[str, object]) -> int:
    template = str(config.get("template_edition") or config["edition_id"])
    if template in {"TR1550", "GOI_vi"}:
        return 7957
    if template == "WLC":
        return 23145
    return 31102


def flatfile_paths(config: dict[str, object]) -> list[Path]:
    return sorted(corpus_dir(config).glob("*.txt"))


def status(args: argparse.Namespace) -> None:
    config = edition_config(args.edition_id)
    files = flatfile_paths(config)
    suffix = filename_suffix(config)
    bad = [
        path.name
        for path in files
        if not re.fullmatch(rf"\d{{3}}_[123]?[A-Z]{{2,3}}_\d{{3}}_\d{{3}}_{re.escape(suffix)}\.txt", path.name)
    ]
    empty = [path for path in files if path.stat().st_size == 0]
    print(f"edition_id: {config['edition_id']}")
    print(f"display_name: {config['display_name']}")
    print(f"bcp47_tag: {config['bcp47_tag']}")
    print(f"corpus_dir: {corpus_dir(config).relative_to(ROOT)}")
    print(f"filename_suffix: {suffix}")
    print(f"files: {len(files)} / expected {expected_count(config)}")
    print(f"empty_files: {len(empty)}")
    print(f"bad_filenames: {len(bad)}")
    if bad[:10]:
        for name in bad[:10]:
            print(f"  {name}")


def check_flatfiles(args: argparse.Namespace) -> None:
    config = edition_config(args.edition_id)
    files = flatfile_paths(config)
    expected = expected_count(config)
    suffix = filename_suffix(config)
    if len(files) != expected:
        raise SystemExit(f"{args.edition_id}: expected {expected} files, got {len(files)}")
    empty = [path for path in files if path.stat().st_size == 0]
    if empty:
        raise SystemExit(f"{args.edition_id}: {len(empty)} zero-byte files")
    bad = [
        path.name
        for path in files
        if not re.fullmatch(rf"\d{{3}}_[123]?[A-Z]{{2,3}}_\d{{3}}_\d{{3}}_{re.escape(suffix)}\.txt", path.name)
    ]
    if bad:
        raise SystemExit(f"{args.edition_id}: {len(bad)} malformed filenames, first: {bad[0]}")
    print(f"{args.edition_id}: flatfiles OK ({len(files)} files)")


def normalize(args: argparse.Namespace) -> None:
    config = edition_config(args.edition_id)
    run(["python3", "tools/normalize_corpus.py", "--dir", str(corpus_dir(config).relative_to(ROOT))])


def readiness(args: argparse.Namespace) -> None:
    config = edition_config(args.edition_id)
    run(["python3", "Meta_Bible_Data/Bible_Noun_Extraction/language_readiness.py", "--lang", str(config["language_subtag"])])


def coverage(args: argparse.Namespace) -> None:
    config = edition_config(args.edition_id)
    lang = str(config["language_subtag"])
    suffix = filename_suffix(config)
    report_arg = getattr(args, "report", None)
    report = Path(report_arg) if report_arg else META / "staging" / "reports" / f"{args.edition_id}_coverage_missing.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "python3",
            "Meta_Bible_Data/Bible_Noun_Extraction/verify_coverage.py",
            "--lang",
            lang,
            "--output-dir",
            str(corpus_dir(config).relative_to(ROOT)),
            "--filename-suffix",
            suffix,
        ]
    )
    with report.open("w", encoding="utf-8") as handle:
        subprocess.run(
            [
                "python3",
                "Meta_Bible_Data/Bible_Noun_Extraction/verify_coverage.py",
                "--lang",
                lang,
                "--output-dir",
                str(corpus_dir(config).relative_to(ROOT)),
                "--filename-suffix",
                suffix,
                "--missing-only",
            ],
            cwd=ROOT,
            stdout=handle,
            check=True,
        )
    print(f"wrote {report.relative_to(ROOT)}")


def build_sql(args: argparse.Namespace) -> None:
    run(["python3", "Meta_Bible_Data/sqlite/build_buffet.py", args.edition_id])


def build_download(args: argparse.Namespace) -> None:
    run(["bash", "Meta_Bible_Data/sqlite/build_shell.sh"])
    run(["python3", "Meta_Bible_Data/goi_db_download/build_downloads.py", args.edition_id])


def stage(args: argparse.Namespace) -> None:
    check_flatfiles(args)
    normalize(args)
    if not args.skip_readiness:
        readiness(args)
    if not args.skip_coverage:
        coverage(args)
    build_sql(args)
    build_download(args)
    print(f"{args.edition_id}: staged SQL and download DB")


def generate_nt(args: argparse.Namespace) -> None:
    config = edition_config(args.edition_id)
    lang = str(config["language_subtag"])
    suffix = filename_suffix(config)
    out_dir = str(corpus_dir(config).relative_to(ROOT))
    reference_args: list[str] = []
    for ref in args.reference_dir:
        reference_args.extend(["--reference-dir", ref])
    for book in NT_BOOKS:
        attempt = 1
        while True:
            print(f"=== {args.edition_id} {book} attempt {attempt} ===", flush=True)
            cmd = [
                "python3",
                "Meta_Bible_Data/Bible_Noun_Extraction/translate_verses.py",
                "--lang",
                lang,
                "--language-name",
                args.language_name,
                "--output-dir",
                out_dir,
                "--filename-suffix",
                suffix,
                "--book",
                book,
                "--timeout",
                str(args.timeout),
                *reference_args,
            ]
            rc = subprocess.run(cmd, cwd=ROOT).returncode
            if rc == 0:
                print(f"=== {args.edition_id} {book} complete ===", flush=True)
                break
            if attempt >= args.max_attempts:
                raise SystemExit(rc)
            print(f"WARN: {book} failed with rc={rc}; retrying and skipping existing files", flush=True)
            attempt += 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    for name, func in [
        ("status", status),
        ("check-flatfiles", check_flatfiles),
        ("normalize", normalize),
        ("readiness", readiness),
        ("coverage", coverage),
        ("build-sql", build_sql),
        ("build-download", build_download),
        ("stage", stage),
    ]:
        p = sub.add_parser(name)
        p.add_argument("edition_id")
        p.set_defaults(func=func)

    p = sub.choices["coverage"]
    p.add_argument("--report")

    p = sub.choices["stage"]
    p.add_argument("--skip-readiness", action="store_true")
    p.add_argument("--skip-coverage", action="store_true")

    p = sub.add_parser("generate-nt")
    p.add_argument("edition_id")
    p.add_argument("--language-name", required=True)
    p.add_argument("--reference-dir", action="append", default=[])
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--max-attempts", type=int, default=5)
    p.set_defaults(func=generate_nt)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
