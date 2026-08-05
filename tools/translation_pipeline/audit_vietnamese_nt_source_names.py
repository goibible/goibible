#!/usr/bin/env python3
"""Audit GOI Vietnamese NT source-name coverage against canonical source names."""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parents[2]
META = ROOT / "Meta_Bible_Data"
SOURCE_DB = META / "staging" / "source_names" / "biblical_source_names.sqlite3"
GREEK_NOUN_DB = META / "Bible_Noun_Extraction" / "greek_noun.sqlite3"
VI_DIR = ROOT / "GOI_Bible" / "GOI_Bible_vi"
OUT_CSV = META / "staging" / "source_names" / "goi_vi_nt_source_name_audit.csv"
SUMMARY = META / "staging" / "source_names" / "goi_vi_nt_source_name_audit_summary.md"

BOOK_NUMS = {
    "MAT": 40, "MRK": 41, "LUK": 42, "JHN": 43, "ACT": 44, "ROM": 45,
    "1CO": 46, "2CO": 47, "GAL": 48, "EPH": 49, "PHP": 50, "COL": 51,
    "1TH": 52, "2TH": 53, "1TI": 54, "2TI": 55, "TIT": 56, "PHM": 57,
    "HEB": 58, "JAS": 59, "1PE": 60, "2PE": 61, "1JN": 62, "2JN": 63,
    "3JN": 64, "JUD": 65, "REV": 66,
}

SOURCE_NAME_AUDIT_SUPPRESSIONS = {
    ("ACT", 4, 6, "G2419"): "Jerusalem is present in ACT 4:5.",
    ("ACT", 9, 29, "G2424"): "Lord Jesus is present in ACT 9:28.",
    ("ACT", 9, 29, "G2962"): "Lord Jesus is present in ACT 9:28.",
    ("ACT", 13, 33, "G2316"): "God/Jesus clause is present in ACT 13:32.",
    ("ACT", 13, 33, "G2424"): "God/Jesus clause is present in ACT 13:32.",
    ("1TI", 3, 16, "G2316"): "Use older critical reading: He who was revealed.",
    ("1JN", 3, 16, "G2316"): "Use shorter/main reading without optional 'of God'.",
    ("1JN", 5, 7, "G4151"): "Use shorter early text; Spirit appears in 1JN 5:8.",
}

VI_FORM_OVERRIDES = {
    "G2316": ["Đức Chúa Trời", "Chúa Trời", "thần", "các thần"],
    "G2424": ["Chúa Giê-xu", "Đức Chúa Giê-xu", "Đức Chúa Jêsus", "Giê-xu", "Jêsus", "Jesus"],
    "G2962": ["Chúa", "Chủ", "chủ"],
    "G5547": ["Đấng Christ", "Christ"],
    "G4151": ["Thánh Linh", "Đức Thánh Linh", "linh"],
    "G11": ["Áp-ra-ham", "Ápraham"],
    "G76": ["A-đam"],
    "G256": ["An-phê"],
    "G367": ["A-na-nia"],
    "G452": ["An-ne"],
    "G707": ["A-ri-ma-thê"],
    "G897": ["Ba-by-lôn", "Ba-bylon"],
    "G912": ["Ba-ra-ba"],
    "G918": ["Ba-thê-lê-my"],
    "G920": ["con Giô-na", "Ba-giô-na"],
    "G921": ["Ba-na-ba"],
    "G954": ["Bê-ên-xê-bun", "Bê-ên-xê-bút"],
    "G955": ["Bê-li-an", "Bê-li-ăn"],
    "G965": ["Bết-lê-hem"],
    "G966": ["Bết-sai-đa"],
    "G1116": ["Gô-mô-rơ"],
    "G1138": ["Đa-vít"],
    "G1682": ["Ê-lôi"],
    "G1697": ["Hê-mô"],
    "G2188": ["Ép-pha-tha"],
    "G2241": ["Ê-li"],
    "G2243": ["Ê-li", "Ê-li-a"],
    "G2268": ["Ê-sai"],
    "G2381": ["Thô-ma"],
    "G2384": ["Gia-cốp"],
    "G2484": ["Y-tu-rê"],
    "G2410": ["Giê-ri-cô"],
    "G2414": ["Giê-ru-sa-lem"],
    "G2419": ["Giê-ru-sa-lem"],
    "G2455": ["Giu-đa"],
    "G2474": ["Y-sơ-ra-ên", "Y-sơ-ra-el"],
    "G2491": ["Giăng", "Giăng Báp-tít"],
    "G2501": ["Giô-sép"],
    "G2584": ["Ca-bê-na-um", "Ca-phác-na-um"],
    "G2786": ["Sê-pha"],
    "G2878": ["Cô-ban", "Corban"],
    "G2976": ["La-xa-rơ"],
    "G3092": ["Ma-át"],
    "G3137": ["Ma-ri"],
    "G3198": ["Mên-chi-xê-đéc", "Mên-chi-xê-đê"],
    "G3475": ["Môi-se"],
    "G3478": ["Na-xa-rét"],
    "G3575": ["Nô-ê"],
    "G3957": ["Lễ Vượt Qua", "lễ Vượt Qua", "Vượt Qua"],
    "G4461": ["Ra-bi", "Rabi", "Thầy", "thầy"],
    "G4469": ["Raca"],
    "G4567": ["Sa-tan"],
    "G4565": ["Sa-rôn"],
    "G4613": ["Si-môn"],
    "G4611": ["Si-lô-am", "Silo-am"],
    "G4622": ["Si-ôn"],
    "G4670": ["Sô-đôm"],
    "G4672": ["Sa-lô-môn"],
    "G4966": ["Si-chem"],
    "G5323": ["Pha-nu-ên"],
    "G5328": ["Pha-ra-ôn"],
    "G5330": ["Pha-ri-si"],
}


def normalize(text: str) -> str:
    return text.replace("{", "").replace("}", "").replace("[", "").replace("]", "")


def contains_form(text: str, form: str) -> bool:
    text = normalize(text)
    return re.search(rf"(?<![A-Za-zÀ-ỹĐđ]){re.escape(form)}(?![A-Za-zÀ-ỹĐđ])", text, flags=re.IGNORECASE) is not None


def load_vi_forms() -> dict[str, list[str]]:
    forms: dict[str, list[str]] = {}
    conn = sqlite3.connect(f"file:{GREEK_NOUN_DB}?mode=ro", uri=True)
    for strongs_num, rendering in conn.execute(
        "SELECT strongs_num, rendering FROM strongs_lang_renderings WHERE lang='vi'"
    ):
        if rendering:
            forms.setdefault(f"G{strongs_num}", []).append(rendering)
    conn.close()
    for strongs, values in VI_FORM_OVERRIDES.items():
        forms.setdefault(strongs, []).extend(values)
    return {k: unique(v) for k, v in forms.items()}


def unique(values: list[str]) -> list[str]:
    seen = set()
    out = []
    for value in values:
        value = value.strip()
        key = value.casefold()
        if value and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=pathlib.Path, default=SOURCE_DB)
    parser.add_argument("--vi-dir", type=pathlib.Path, default=VI_DIR)
    parser.add_argument("--csv", type=pathlib.Path, default=OUT_CSV)
    parser.add_argument("--summary", type=pathlib.Path, default=SUMMARY)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    forms = load_vi_forms()
    conn = sqlite3.connect(args.db)
    rows = conn.execute(
        """
        SELECT o.book_num, o.book, o.chapter, o.verse, o.strongs,
               e.canonical_label, e.entity_type
        FROM source_name_occurrences o
        JOIN source_name_entities e USING(entity_key)
        WHERE o.testament = 'NT'
        ORDER BY o.book_num, o.chapter, o.verse, o.strongs
        """
    ).fetchall()
    conn.close()

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    counts = {
        "checked": 0,
        "pass": 0,
        "closed": 0,
        "missing": 0,
        "no_form": 0,
        "missing_file": 0,
    }
    findings = []
    with args.csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["status", "book", "chapter", "verse", "strongs", "entity_type", "canonical_label", "expected_forms", "vietnamese"])
        for book_num, book, chapter, verse, strongs, label, entity_type in rows:
            if (book, chapter, verse, strongs) in SOURCE_NAME_AUDIT_SUPPRESSIONS:
                counts["closed"] += 1
                continue
            expected = forms.get(strongs, [])
            path = args.vi_dir / f"{book_num:03d}_{book}_{chapter:03d}_{verse:03d}_GOI_vi.txt"
            if not path.exists():
                counts["missing_file"] += 1
                status = "missing_file"
                text = ""
            elif not expected:
                counts["no_form"] += 1
                status = "no_form"
                text = path.read_text(encoding="utf-8").strip()
            else:
                text = path.read_text(encoding="utf-8").strip()
                counts["checked"] += 1
                status = "pass" if any(contains_form(text, form) for form in expected) else "missing"
                counts[status] += 1
            if status != "pass":
                row = (status, book, chapter, verse, strongs, entity_type, label, "; ".join(expected), text)
                findings.append(row)
                writer.writerow(row)

    args.summary.write_text(
        "\n".join(
            [
                "# GOI Vietnamese NT Source-Name Audit",
                "",
                "Exact-form first pass against canonical NT source-name occurrences.",
                "",
                f"- checked occurrences: {counts['checked']}",
                f"- pass: {counts['pass']}",
                f"- closed textual/boundary suppressions: {counts['closed']}",
                f"- missing expected form: {counts['missing']}",
                f"- no Vietnamese form available from profile: {counts['no_form']}",
                f"- missing Vietnamese verse files: {counts['missing_file']}",
                "",
                "CSV: `{}`".format(args.csv),
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(counts)
    print(f"CSV: {args.csv}")
    print(f"Summary: {args.summary}")


if __name__ == "__main__":
    main()
