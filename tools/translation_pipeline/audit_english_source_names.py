#!/usr/bin/env python3
"""First-pass GOI English audit against source Strong's name occurrences."""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sqlite3
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
META = ROOT / "Meta_Bible_Data"
SOURCE_DB = META / "staging" / "source_names" / "biblical_source_names.sqlite3"
EN_DIR = ROOT / "GOI_Bible" / "GOI_Bible_English"
OUT_CSV = META / "staging" / "source_names" / "goi_en_source_name_audit.csv"
SUMMARY = META / "staging" / "source_names" / "goi_en_source_name_audit_summary.md"
REALIGNMENT_MAP = META / "logs" / "2026-06-09_goi_english_ot_kjv_realign_map.csv"
HEBREW_STRONGS = META / "sources" / "strongs" / "hebrew" / "StrongHebrewG.xml"
GREEK_STRONGS = META / "sources" / "strongs" / "greek" / "StrongsGreekDictionaryXML_1.4" / "strongsgreek.xml"
OSIS_NS = {"osis": "http://www.bibletechnologies.net/2003/OSIS/namespace"}

DIVINE_FORMS = {
    "H136": ["Lord", "O Lord", "lords"],
    "H410": ["God", "god", "gods", "mighty", "mighty ones", "mighty mountains", "lords", "Asahel"],
    "H430": ["God", "god", "gods", "angels", "judges", "mighty", "divine", "divine beings", "divine fire"],
    "H433": ["God", "god", "gods"],
    "H3068": ["LORD", "Lord", "O LORD"],
    "H3069": ["GOD", "Lord GOD", "Lord Jehovah", "my Lord Jehovah", "my Lord the LORD", "LORD my Lord", "Lord the LORD", "Lord", "LORD"],
    "H5945": ["Most High", "Almighty", "highest", "exalted", "upper", "upward", "nobles"],
    "H7706": ["Almighty", "Shaddai"],
    "G2316": ["God"],
    "G2424": ["Jesus"],
    "G2962": ["Lord", "lords", "owner", "owners", "master", "masters", "Sir", "Sirs"],
    "G5547": ["Christ", "Messiah"],
    "G4151": ["Spirit", "Holy Spirit"],
}

ENGLISH_FORM_OVERRIDES = {
    "G107": ["Azor"],
    "G256": ["Alphaeus"],
    "G707": ["Arimathea"],
    "G768": ["Asher"],
    "G918": ["Bartholomew"],
    "G924": ["Bartimaeus"],
    "G954": ["Beelzebul", "Beelzebub"],
    "G955": ["Beliar"],
    "G1007": ["Beor"],
    "G1086": ["Gergesene", "Gergesenes"],
    "G1116": ["Gomorrah"],
    "G1639": ["Elamite", "Elamites"],
    "G1665": ["Elizabeth", "Elisabeth"],
    "G1666": ["Elisha"],
    "G1697": ["Hamor", "Emmor"],
    "G2074": ["Hezron", "Esrom"],
    "G2195": ["Zacchaeus"],
    "G2194": ["Zebulun"],
    "G2216": ["Zerubbabel"],
    "G2243": ["Elijah", "Elias"],
    "G2268": ["Isaiah", "Esaias"],
    "G2384": ["Jacob"],
    "G2401": ["Idumaea"],
    "G2403": ["Jezebel"],
    "G2455": ["Judah", "Judas", "Jude"],
    "G2484": ["Ituraea"],
    "G2495": ["Jonah", "Jonas", "Bar-jona"],
    "G2498": ["Jehoshaphat"],
    "G2501": ["Joseph", "parents"],
    "G2832": ["Clopas", "Cleophas"],
    "G2879": ["Korah"],
    "G3099": ["Midian"],
    "G3103": ["Methuselah"],
    "G3121": ["Mahalaleel"],
    "G3190": ["Melea"],
    "G3370": ["Mede", "Medes"],
    "G3476": ["Nahshon"],
    "G3477": ["Naggai", "Nagge"],
    "G3486": ["Nahum"],
    "G3493": ["Nahor"],
    "G3508": ["Naphtali"],
    "G3535": ["Nineveh"],
    "G3575": ["Noah"],
    "G3774": ["Uriah"],
    "G4477": ["Rahab"],
    "G4565": ["Sharon"],
    "G4590": ["Shem"],
    "G4613": ["Simeon"],
    "G4614": ["Sinai"],
    "G4622": ["Zion", "Sion"],
    "G4966": ["Shechem"],
    "G5090": ["Timaeus"],
    "G5466": ["Chaldean", "Chaldeans"],
    "G5617": ["Hosea"],
    "G5329": ["Perez", "Phares"],
    "G5330": ["Pharisee", "Pharisees"],
    "G2316": ["gods", "godly"],
    "H26": ["Abigail"],
    "H350": ["Ichabod"],
    "H445": ["Elhanan"],
    "H528": ["Amon"],
    "H549": ["Abana"],
    "H669": ["Ephraimite"],
    "H758": ["Arameans", "Syrian"],
    "H64": ["Abel Keramim", "plain of the vineyards"],
    "H1044": ["Beth-Eked", "shearing house"],
    "H1041": ["Bethazmaveth"],
    "H1130": ["Ben-hadad"],
    "H1144": ["Benjaminites", "Benjaminite"],
    "H1168": ["Baals"],
    "H1212": ["Bezalel"],
    "H1269": ["Birzoth", "Birzaith"],
    "H1403": ["Gabriel"],
    "H1410": ["Gadites"],
    "H1662": ["Gath-hepher", "Gittah-hepher"],
    "H1689": ["Diblah"],
    "H1721": ["Rodanim"],
    "H187": ["Uzal"],
    "H1939": ["Hodaviah"],
    "H2038": ["Harmon"],
    "H2051": ["Vedan"],
    "H2140": ["Zabbai"],
    "H2139": ["Zabbud"],
    "H2128": ["Ziphites"],
    "H2361": ["Hiram"],
    "H2349": ["Huphamite"],
    "H2463": ["Helbon"],
    "H2478": ["Halahul"],
    "H2605": ["Hanan"],
    "H2712": ["Hukkokah"],
    "H3050": ["LORD", "Yah", "hallelujah"],
    "H3171": ["Jehuel"],
    "H3241": ["Janim"],
    "H3265": ["Jaare-Oregim", "Jaare–Oregim"],
    "H3260": ["Iddo"],
    "H3328": ["Izhar"],
    "H3672": ["Kinneroth"],
    "H3691": ["Chislev"],
    "H3810": ["Lo-debar"],
    "H3778": ["Chaldea"],
    "H3881": ["Levites", "Levi"],
    "H3919": ["Laishah"],
    "H4076": ["Medes"],
    "H4122": ["Maher-shalal-hash-baz"],
    "H1408": ["Gad", "troop"],
    "H2052": ["Vaheb", "Waheb"],
    "H2335": ["Chozai", "seers"],
    "H2845": ["Hethites", "Hittite"],
    "H3429": ["Josheb-basshebeth", "that sat in the seat"],
    "H3063": ["Judahites"],
    "H1471": ["nations", "Gentiles"],
    "H1662": ["Gath-hepher", "Gittah-hepher"],
    "H1835": ["Dan", "Danites"],
    "H2518": ["Hilkiah", "Hilkias"],
    "H3003": ["Jabesh", "Jabesh-gilead"],
    "H3087": ["Jehozadak"],
    "H3390": ["Jerusalem"],
    "H3575": ["Cuthah"],
    "H3478": ["Israelites", "Israelite", "children of Israel", "sons of Israel"],
    "H4080": ["Midianites"],
    "H4124": ["Moabites"],
    "H5436": ["Sabaeans"],
    "H5321": ["Naphtalite"],
    "H5804": ["Ayyah"],
    "H5832": ["Azarel"],
    "H5841": ["Gazites"],
    "H5853": ["Ataroth-addar"],
    "H6002": ["Amalekites"],
    "H6278": ["Ittah-kazin"],
    "H3878": ["Levite", "Levites"],
    "H4363": ["Michmash", "Michmas"],
    "H4601": ["Maacah", "Maachah", "Maachathite", "Maachathites"],
    "H4709": ["Mizpah", "Mizpeh"],
    "H4723": ["drove", "gathering place"],
    "H4713": ["Egyptians", "Egyptian", "Egypt"],
    "H4847": ["Merarites"],
    "H6252": ["Ashtaroth"],
    "H6549": ["Pharaoh Necho", "Pharaoh Neco", "Pharaoh-neco", "Pharaohnecho"],
    "H1648": ["Gershonites"],
    "H6583": ["Pashhur"],
    "H6714": ["Izhar"],
    "H672": ["Ephrathah", "Ephrathite", "Ephrathites"],
    "H6815": ["Zaanannim"],
    "H6955": ["Kohathites"],
    "H7141": ["Korahites"],
    "H763": ["Aram-naharaim", "Aram Naharaim"],
    "H795": ["Ashdod"],
    "H7157": ["Kiriath-jearim"],
    "H7205": ["Reubenites"],
    "H7384": ["Diphath"],
    "H7497": ["giants"],
    "H8019": ["Shelomoth"],
    "H8197": ["Shuphamite"],
    "H8234": ["Shapher"],
    "H8412": ["Tamar"],
    "H842": ["groves", "Asherah", "Asherim", "idols"],
    "H884": ["Beer-sheba"],
    "H894": ["Babylonians"],
    "H980": ["Bahurite"],
    "H3064": ["Jewish"],
    "H2983": ["Jebusites"],
    "H5109": ["Nobai"],
    "H6689": ["Zif"],
    "H5964": ["Almuth"],
    "H4610": ["Akrabbim"],
    "H1036": ["Beth-le-aphrah", "Beth Ophrah"],
    "H2099": ["Ziv"],
    "H4519": ["Manassites"],
    "H6483": ["Happizzez"],
    "H8445": ["Tokhath"],
}

SOURCE_NAME_AUDIT_SUPPRESSIONS = {
    # Source verse-boundary differences. The expected names are present in the
    # GOI English translation, but not in the same verse number as this TR parse.
    ("ACT", 4, 6, "G2419"): "Jerusalem is present in ACT 4:5.",
    ("ACT", 9, 29, "G2424"): "Lord Jesus is present in ACT 9:28.",
    ("ACT", 9, 29, "G2962"): "Lord Jesus is present in ACT 9:28.",
    ("ACT", 13, 33, "G2316"): "God/Jesus clause is present in ACT 13:32.",
    ("ACT", 13, 33, "G2424"): "God/Jesus clause is present in ACT 13:32.",
    # Project textual policy follows the older critical reading here.
    ("1TI", 3, 16, "G2316"): "Use 'He who was revealed', not TR 'God'.",
    ("1JN", 3, 16, "G2316"): "Use shorter/main reading without optional 'of God'.",
    ("1JN", 5, 7, "G4151"): "Use shorter early text; Spirit appears in 1JN 5:8.",
}

WLC_BOOK_IDS = {
    "GEN": "Gen",
    "EXO": "Exod",
    "LEV": "Lev",
    "NUM": "Num",
    "DEU": "Deut",
    "JOS": "Josh",
    "JDG": "Judg",
    "RUT": "Ruth",
    "1SA": "1Sam",
    "2SA": "2Sam",
    "1KI": "1Kgs",
    "2KI": "2Kgs",
    "1CH": "1Chr",
    "2CH": "2Chr",
    "EZR": "Ezra",
    "NEH": "Neh",
    "EST": "Esth",
    "JOB": "Job",
    "PSA": "Ps",
    "PRO": "Prov",
    "ECC": "Eccl",
    "SNG": "Song",
    "ISA": "Isa",
    "JER": "Jer",
    "LAM": "Lam",
    "EZK": "Ezek",
    "DAN": "Dan",
    "HOS": "Hos",
    "JOL": "Joel",
    "AMO": "Amos",
    "OBA": "Obad",
    "JON": "Jonah",
    "MIC": "Mic",
    "NAM": "Nah",
    "HAB": "Hab",
    "ZEP": "Zeph",
    "HAG": "Hag",
    "ZEC": "Zech",
    "MAL": "Mal",
}

BOOK_NUMS = {
    "GEN": 1,
    "EXO": 2,
    "LEV": 3,
    "NUM": 4,
    "DEU": 5,
    "JOS": 6,
    "JDG": 7,
    "RUT": 8,
    "1SA": 9,
    "2SA": 10,
    "1KI": 11,
    "2KI": 12,
    "1CH": 13,
    "2CH": 14,
    "EZR": 15,
    "NEH": 16,
    "EST": 17,
    "JOB": 18,
    "PSA": 19,
    "PRO": 20,
    "ECC": 21,
    "SNG": 22,
    "ISA": 23,
    "JER": 24,
    "LAM": 25,
    "EZK": 26,
    "DAN": 27,
    "HOS": 28,
    "JOL": 29,
    "AMO": 30,
    "OBA": 31,
    "JON": 32,
    "MIC": 33,
    "NAM": 34,
    "HAB": 35,
    "ZEP": 36,
    "HAG": 37,
    "ZEC": 38,
    "MAL": 39,
}


def text_content(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def strong_key(prefix: str, number: str) -> str:
    return f"{prefix}{int(number)}"


def load_hebrew_english_forms() -> dict[str, list[str]]:
    root = ET.parse(HEBREW_STRONGS).getroot()
    forms: dict[str, list[str]] = {}
    for div in root.findall(".//osis:div[@type='entry']", OSIS_NS):
        n = div.attrib.get("n", "")
        if not n:
            continue
        key = strong_key("H", n)
        values: list[str] = []
        for note in div.findall(".//osis:note[@type='translation']", OSIS_NS):
            text = text_content(note).strip(" .;:")
            if text:
                values.extend(split_forms(text))
        if key in DIVINE_FORMS:
            values.extend(DIVINE_FORMS[key])
        if values:
            forms[key] = unique(values)
    return forms


def load_greek_english_forms() -> dict[str, list[str]]:
    root = ET.parse(GREEK_STRONGS).getroot()
    forms: dict[str, list[str]] = {}
    for entry in root.findall(".//entry"):
        n = text_content(entry.find("strongs"))
        if not n:
            continue
        key = strong_key("G", n)
        values = []
        kjv = text_content(entry.find("kjv_def")).replace(":--", "").replace("--", "").strip(" .;:")
        if kjv:
            values.extend(split_forms(kjv))
        if key in DIVINE_FORMS:
            values.extend(DIVINE_FORMS[key])
        if values:
            forms[key] = unique(values)
    return forms


def split_forms(text: str) -> list[str]:
    text = re.split(r"\bCompare\b", text, maxsplit=1)[0]
    text = re.sub(r"\([^)]*\)", "", text)
    pieces = re.split(r"[,;/.]", text)
    forms = []
    for piece in pieces:
        piece = piece.strip(" .;:-")
        if not piece or piece.startswith("[") or " " in piece and piece.lower() == piece:
            continue
        piece = piece.replace("X ", "").strip()
        if piece and not any(ch in piece for ch in "*?"):
            forms.append(piece)
    return forms


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


def contains_form(text: str, form: str) -> bool:
    return re.search(rf"(?<![A-Za-z]){re.escape(form)}(?![A-Za-z])", text, flags=re.IGNORECASE) is not None


def load_realignment_map(path: pathlib.Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    source_to_targets: dict[str, list[str]] = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            target = row["target_ref"]
            for source in row["source_refs"].split(";"):
                source = source.strip()
                if source:
                    source_to_targets.setdefault(source, []).append(target)
    return source_to_targets


def english_path(english_dir: pathlib.Path, book: str, chapter: int, verse: int) -> pathlib.Path:
    return english_dir / f"{BOOK_NUMS[book]:03d}_{book}_{chapter:03d}_{verse:03d}_GOI_En.txt"


def mapped_texts(
    english_dir: pathlib.Path,
    source_to_targets: dict[str, list[str]],
    book: str,
    chapter: int,
    verse: int,
) -> list[tuple[str, str]]:
    source_book = WLC_BOOK_IDS.get(book)
    if not source_book:
        return []
    source_ref = f"{source_book}.{chapter}.{verse}"
    texts = []
    for target in source_to_targets.get(source_ref, []):
        target_book, target_cv = target.split(" ", 1)
        target_chapter, target_verse = [int(part) for part in target_cv.split(":", 1)]
        path = english_path(english_dir, target_book, target_chapter, target_verse)
        if path.exists():
            texts.append((target, path.read_text(encoding="utf-8").strip()))
    return texts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=pathlib.Path, default=SOURCE_DB)
    parser.add_argument("--english-dir", type=pathlib.Path, default=EN_DIR)
    parser.add_argument("--csv", type=pathlib.Path, default=OUT_CSV)
    parser.add_argument("--summary", type=pathlib.Path, default=SUMMARY)
    parser.add_argument("--realignment-map", type=pathlib.Path, default=REALIGNMENT_MAP)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    forms = {}
    forms.update(load_hebrew_english_forms())
    forms.update(load_greek_english_forms())
    for strongs, values in ENGLISH_FORM_OVERRIDES.items():
        forms[strongs] = unique([*forms.get(strongs, []), *values])
    source_to_targets = load_realignment_map(args.realignment_map)
    conn = sqlite3.connect(args.db)
    rows = conn.execute(
        """
        SELECT o.testament, o.source_language, o.book_num, o.book, o.chapter, o.verse,
               o.strongs, e.canonical_label, e.entity_type,
               o.mapped_book, o.mapped_chapter, o.mapped_verse, o.source_note
        FROM source_name_occurrences o
        JOIN source_name_entities e USING(entity_key)
        ORDER BY o.book_num, o.chapter, o.verse, o.strongs
        """
    ).fetchall()

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    counts = {
        "checked": 0,
        "pass": 0,
        "suppressed": 0,
        "mapped_checked": 0,
        "mapped_pass": 0,
        "missing": 0,
        "mapped_missing": 0,
        "no_form": 0,
        "missing_file": 0,
    }
    findings = []
    with args.csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["status", "testament", "book", "chapter", "verse", "strongs", "entity_type", "canonical_label", "expected_forms", "english"])
        for (
            testament,
            language,
            book_num,
            book,
            chapter,
            verse,
            strongs,
            label,
            entity_type,
            mapped_book,
            mapped_chapter,
            mapped_verse,
            source_note,
        ) in rows:
            if (book, chapter, verse, strongs) in SOURCE_NAME_AUDIT_SUPPRESSIONS:
                counts["suppressed"] += 1
                continue
            expected = forms.get(strongs, [])
            candidates: list[tuple[str, pathlib.Path]] = []
            direct_path = args.english_dir / f"{book_num:03d}_{book}_{chapter:03d}_{verse:03d}_GOI_En.txt"
            candidates.append((f"{book} {chapter}:{verse}", direct_path))
            if mapped_book and mapped_chapter and mapped_verse:
                mapped_book_num = BOOK_NUMS.get(mapped_book, book_num)
                mapped_path = args.english_dir / f"{mapped_book_num:03d}_{mapped_book}_{mapped_chapter:03d}_{mapped_verse:03d}_GOI_En.txt"
                mapped_ref = f"{mapped_book} {mapped_chapter}:{mapped_verse}"
                if mapped_path != direct_path:
                    candidates.append((mapped_ref, mapped_path))
            existing = [(ref, path) for ref, path in candidates if path.exists()]
            if not existing:
                counts["missing_file"] += 1
                status = "missing_file"
                english = ""
            elif not expected:
                counts["no_form"] += 1
                status = "no_form"
                english = " || ".join(f"{ref}: {path.read_text(encoding='utf-8').strip()}" for ref, path in existing)
            else:
                ref_texts = [(ref, path.read_text(encoding="utf-8").strip()) for ref, path in existing]
                english = " || ".join(f"{ref}: {text}" for ref, text in ref_texts)
                counts["checked"] += 1
                status = "pass" if any(contains_form(text, form) for _ref, text in ref_texts for form in expected) else "missing"
                counts[status] += 1
            if status not in {"pass", "mapped_pass"}:
                findings.append((status, testament, book, chapter, verse, strongs, entity_type, label, "; ".join(expected), english))
                writer.writerow(findings[-1])

    by_status = {}
    for finding in findings:
        by_status[finding[0]] = by_status.get(finding[0], 0) + 1
    args.summary.write_text(
        "\n".join(
            [
                "# GOI English Source-Name Audit",
                "",
                "First-pass exact-form audit against source Strong's name occurrences.",
                "",
                f"- checked occurrences: {counts['checked']}",
                f"- mapped checked occurrences: {counts['mapped_checked']}",
                f"- pass: {counts['pass']}",
                f"- closed textual/boundary suppressions: {counts['suppressed']}",
                f"- mapped pass: {counts['mapped_pass']}",
                f"- missing expected form: {counts['missing']}",
                f"- mapped missing expected form: {counts['mapped_missing']}",
                f"- no English form available from dictionary/profile: {counts['no_form']}",
                f"- missing English verse files: {counts['missing_file']}",
                "",
                "This is a review queue, not a final semantic verdict. It is intentionally strict and can flag pronouns, titles, or defensible alternate renderings.",
                "",
                f"CSV: `{args.csv}`",
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
