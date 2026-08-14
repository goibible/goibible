#!/usr/bin/env python3
"""Audit GOI English name renderings against KJV and WEBUS.

This is a deterministic review-queue generator.  It reads the canonical
source-name occurrences and the three English editions, but never mutates any
of them.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
import pathlib
import re
import sqlite3

from audit_english_source_names import (
    DIVINE_FORMS,
    ENGLISH_FORM_OVERRIDES,
    SOURCE_NAME_AUDIT_SUPPRESSIONS,
    load_greek_english_forms,
    load_hebrew_english_forms,
    unique,
)


ROOT = pathlib.Path(__file__).resolve().parents[2]
META = ROOT / "Meta_Bible_Data"
SOURCE_DB = META / "staging" / "source_names" / "biblical_source_names.sqlite3"
BIBLE_DB = META / "local_backups" / "GOI_bible.sqlite3"
OUT_CSV = META / "staging" / "source_names" / "goi_en_kjv_webus_name_scrub.csv"
GROUPED_CSV = META / "staging" / "source_names" / "goi_en_kjv_webus_diff_both_refs_agree_groups.csv"
SUMMARY = META / "staging" / "source_names" / "goi_en_kjv_webus_name_scrub_summary.md"
EDITIONS = ("GOI_En", "KJV", "WEBUS")
STATUS_ORDER = (
    "diff_both_refs_agree",
    "diff_kjv_only",
    "diff_webus_only",
    "diff_both_refs_disagree",
    "no_goi_form",
    "no_ref_form",
    "ok",
)
FLAGGED_STATUSES = set(STATUS_ORDER) - {"ok"}
# H3050 (Yah) is tagged as a proper name in the current source-name database,
# but it is the shortened divine name and belongs in the divine summary.
DIVINE_CATEGORY_OVERRIDES = {"H3050"}

# These sets contain grammatical ways of referring to the same named entity,
# not competing spellings. Keep them narrow and explicit so spelling changes
# such as Hillkiah/Hilkiah remain in the review queue.
GRAMMATICAL_EQUIVALENCE_GROUPS = {
    "H123": ({"Edom", "Edomite", "Edomites"},),
    "H669": ({"Ephraim", "Ephraimite", "Ephraimites"},),
    "H804": ({"Assyria", "Assyrian", "Assyrians"},),
    "H1568": ({"Gilead", "Gileadite", "Gileadites"},),
    "H3478": ({"Israel", "Israelite", "Israelites", "children of Israel", "sons of Israel"},),
    "H3878": ({"Levi", "Levite", "Levites"},),
    "H4074": ({"Media", "Mede", "Medes"},),
    "H4080": ({"Midian", "Midianite", "Midianites"},),
    "H4124": ({"Moab", "Moabite", "Moabites"},),
    "H4713": ({"Egypt", "Egyptian", "Egyptians", "of Egypt"},),
    "H4714": ({"Egypt", "Egyptian", "Egyptians"},),
    "H5983": ({"Ammon", "Ammonite", "Ammonites"},),
    "H6002": ({"Amalek", "Amalekite", "Amalekites"},),
    "H894": ({"Babylon", "Babylonian", "Babylonians"},),
}


@dataclass(frozen=True)
class Occurrence:
    testament: str
    book_num: int
    book: str
    chapter: int
    verse: int
    strongs: str
    surface_text: str
    morphology: str
    canonical_label: str
    entity_type: str
    mapped_book: str
    mapped_chapter: int | None
    mapped_verse: int | None
    source_note: str

    @property
    def check_ref(self) -> tuple[str, int, int]:
        if self.mapped_book and self.mapped_chapter is not None and self.mapped_verse is not None:
            return self.mapped_book, self.mapped_chapter, self.mapped_verse
        return self.book, self.chapter, self.verse

    @property
    def category(self) -> str:
        if self.entity_type == "name_of_god" or self.strongs in DIVINE_CATEGORY_OVERRIDES:
            return "divine_name_or_title"
        return "person_or_place"


def readonly_connection(path: pathlib.Path) -> sqlite3.Connection:
    """Open an existing SQLite database without permitting writes."""
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro&immutable=1", uri=True)


def load_candidate_forms() -> dict[str, list[str]]:
    forms: dict[str, list[str]] = {}
    forms.update(load_hebrew_english_forms())
    forms.update(load_greek_english_forms())
    for strongs, values in ENGLISH_FORM_OVERRIDES.items():
        forms[strongs] = unique([*forms.get(strongs, []), *values])
    # Keep this explicit: these are part of the audit contract even if a
    # dictionary loader already incorporated most of them.
    for strongs, values in DIVINE_FORMS.items():
        forms[strongs] = unique([*forms.get(strongs, []), *values])
    return forms


def load_occurrences(path: pathlib.Path) -> list[Occurrence]:
    with readonly_connection(path) as conn:
        rows = conn.execute(
            """
            SELECT o.testament, o.book_num, o.book, o.chapter, o.verse,
                   o.strongs, o.surface_text, o.morphology,
                   e.canonical_label, e.entity_type,
                   o.mapped_book, o.mapped_chapter, o.mapped_verse, o.source_note
            FROM source_name_occurrences o
            JOIN source_name_entities e USING (entity_key)
            ORDER BY o.book_num, o.chapter, o.verse, o.strongs,
                     o.surface_text, o.morphology
            """
        ).fetchall()
    return [Occurrence(*row) for row in rows]


def load_verses(path: pathlib.Path) -> dict[tuple[str, str, int, int], str]:
    placeholders = ",".join("?" for _ in EDITIONS)
    with readonly_connection(path) as conn:
        rows = conn.execute(
            f"""
            SELECT edition_id, book, chapter, verse, COALESCE(verse_text, '')
            FROM verses
            WHERE edition_id IN ({placeholders})
            """,
            EDITIONS,
        ).fetchall()
    present = {row[0] for row in rows}
    missing = set(EDITIONS) - present
    if missing:
        raise RuntimeError(f"Bible database lacks required editions: {', '.join(sorted(missing))}")
    return {(edition, book, chapter, verse): text for edition, book, chapter, verse, text in rows}


def match_form(text: str, forms: list[str]) -> str | None:
    """Return the actual, longest candidate spelling found in a verse."""
    matches: list[tuple[int, int, str]] = []
    for form in forms:
        # Treat the three common horizontal dash glyphs as typography, not as
        # different name renderings (for example Jaare-Oregim).
        pattern = "".join(r"[\-–—]" if char in "-–—" else re.escape(char) for char in form)
        match = re.search(
            rf"(?<![A-Za-z]){pattern}(?![A-Za-z])",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            matches.append((len(match.group(0)), -match.start(), match.group(0)))
    return max(matches)[2] if matches else None


def comparable(form: str) -> str:
    """Normalize typography and grammatical wrappers used around names.

    A leading vocative ``O`` or definite article ``the`` belongs to the
    sentence rather than to the name rendering.  Core capitalization remains
    significant so that ``LORD`` and ``Lord`` are not silently conflated.
    """
    value = re.sub(r"\s+", " ", form.replace("–", "-").replace("—", "-")).strip()
    return re.sub(r"^(?:O|the)\s+", "", value, flags=re.IGNORECASE)


def grammatical_equivalence_note(
    strongs: str,
    goi: str | None,
    kjv: str | None,
    webus: str | None,
) -> str:
    """Return an accepted-policy note when all forms are one grammar group."""
    if not goi or not kjv or not webus:
        return ""
    values = {comparable(value).casefold() for value in (goi, kjv, webus)}
    for group in GRAMMATICAL_EQUIVALENCE_GROUPS.get(strongs, ()):
        normalized_group = {comparable(value).casefold() for value in group}
        if values <= normalized_group:
            return "Accepted grammatical forms of the same named entity."
    return ""


def classify(goi: str | None, kjv: str | None, webus: str | None) -> str:
    if goi is None:
        return "no_goi_form"
    if kjv is None or webus is None:
        return "no_ref_form"

    goi_value = comparable(goi)
    kjv_value = comparable(kjv)
    webus_value = comparable(webus)
    if goi_value == kjv_value == webus_value:
        return "ok"
    if goi_value == webus_value and goi_value != kjv_value:
        return "diff_kjv_only"
    if goi_value == kjv_value and goi_value != webus_value:
        return "diff_webus_only"
    if kjv_value == webus_value:
        return "diff_both_refs_agree"
    return "diff_both_refs_disagree"


def markdown_cell(value: object, limit: int = 100) -> str:
    text = str(value).replace("|", "\\|").replace("\n", " ")
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def summary_table(counts: Counter[str]) -> list[str]:
    lines = ["| Status | Count |", "|---|---:|"]
    lines.extend(f"| `{status}` | {counts[status]} |" for status in STATUS_ORDER)
    return lines


def write_grouped_queue(path: pathlib.Path, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Collapse the reference-consensus queue into rendering decisions."""
    grouped: dict[tuple[object, ...], dict[str, object]] = {}
    for row in rows:
        if row["status"] != "diff_both_refs_agree":
            continue
        key = (
            row["review_state"], row["category"], row["strongs"], row["canonical_label"],
            row["goi_form"], row["kjv_form"], row["webus_form"],
        )
        if key not in grouped:
            grouped[key] = {
                "decision": row["review_state"],
                "category": row["category"],
                "strongs": row["strongs"],
                "canonical_label": row["canonical_label"],
                "goi_form": row["goi_form"],
                "kjv_form": row["kjv_form"],
                "webus_form": row["webus_form"],
                "occurrence_count": 0,
                "refs": [],
                "review_note": row["review_note"],
            }
        group = grouped[key]
        group["occurrence_count"] = int(group["occurrence_count"]) + 1
        refs = group["refs"]
        assert isinstance(refs, list)
        if row["source_ref"] not in refs:
            refs.append(row["source_ref"])

    decision_order = {"active_review": 0, "accepted_policy": 1}
    groups = sorted(
        grouped.values(),
        key=lambda group: (
            decision_order.get(str(group["decision"]), 2),
            -int(group["occurrence_count"]),
            str(group["strongs"]), str(group["goi_form"]),
        ),
    )
    fieldnames = [
        "decision", "category", "strongs", "canonical_label", "goi_form", "kjv_form",
        "webus_form", "occurrence_count", "unique_target_count", "sample_refs", "review_note",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for group in groups:
            refs = group.pop("refs")
            assert isinstance(refs, list)
            writer.writerow(
                {
                    **group,
                    "unique_target_count": len(refs),
                    "sample_refs": "; ".join(str(ref) for ref in refs[:12]),
                }
            )
            group["refs"] = refs
    return groups


def write_summary(
    path: pathlib.Path,
    csv_path: pathlib.Path,
    total: int,
    counts: Counter[str],
    category_counts: dict[str, Counter[str]],
    flagged: list[dict[str, object]],
    grouped_path: pathlib.Path,
    decision_groups: list[dict[str, object]],
) -> None:
    no_goi_rows = [row for row in flagged if row["status"] == "no_goi_form"]
    documented_no_goi = [row for row in no_goi_rows if row["review_note"]]
    active_no_goi = [row for row in no_goi_rows if not row["review_note"]]
    review_states = Counter(str(row["review_state"]) for row in flagged)
    group_decisions = Counter(str(group["decision"]) for group in decision_groups)
    lines = [
        "# GOI English KJV/WEBUS Name Scrub",
        "",
        "Deterministic review queue comparing GOI English name renderings with KJV and WEBUS for each source-name occurrence.",
        "",
        f"- Source-name occurrences audited: {total}",
        f"- Flagged occurrences: {sum(counts[s] for s in FLAGGED_STATUSES)}",
        f"- OK occurrences: {counts['ok']}",
        f"- Active `no_goi_form` occurrences: {len(active_no_goi)}",
        f"- Documented `no_goi_form` closures: {len(documented_no_goi)}",
        f"- Accepted grammatical-equivalence occurrences: {review_states['accepted_policy']}",
        f"- CSV: `{csv_path}`",
        f"- Grouped `diff_both_refs_agree` decisions: `{grouped_path}`",
        "",
        "## Status counts",
        "",
        *summary_table(counts),
    ]
    category_titles = {
        "person_or_place": "Person/place proper names",
        "divine_name_or_title": "Divine names and titles",
    }
    for category in ("person_or_place", "divine_name_or_title"):
        lines.extend(["", f"## {category_titles[category]}", "", *summary_table(category_counts[category])])

    lines.extend(
        [
            "",
            "## Grouped reference-consensus decisions",
            "",
            f"- Active rendering groups: {group_decisions['active_review']}",
            f"- Accepted grammatical-equivalence groups: {group_decisions['accepted_policy']}",
            f"- Total grouped decisions: {len(decision_groups)}",
        ]
    )

    lines.extend(["", "## No-GOI-form review", ""])
    if no_goi_rows:
        lines.extend(
            [
                "| Source ref | Strong's | Disposition |",
                "|---|---|---|",
            ]
        )
        for row in no_goi_rows:
            disposition = row["review_note"] or "Active review"
            lines.append(
                "| " + " | ".join(
                    markdown_cell(value) for value in (row["source_ref"], row["strongs"], disposition)
                ) + " |"
            )
    else:
        lines.append("No `no_goi_form` rows.")

    lines.extend(
        [
            "",
            "## Top flagged rows",
            "",
            "Rows are prioritized with `diff_both_refs_agree` first. Differences where the references disagree remain review-only.",
            "",
        ]
    )
    if flagged:
        lines.extend(
            [
                "| Status | Category | Source ref | Checked ref | Strong's | GOI | KJV | WEBUS | Label |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for row in flagged[:50]:
            values = (
                row["status"], row["category"], row["source_ref"], row["checked_ref"],
                row["strongs"], row["goi_form"], row["kjv_form"], row["webus_form"],
                row["canonical_label"],
            )
            lines.append("| " + " | ".join(markdown_cell(value) for value in values) + " |")
    else:
        lines.append("No flagged rows.")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "KJV and WEBUS are deterministic reference witnesses, not final source authority. This audit does not edit verses or decide that a flagged rendering is wrong.",
            "",
            "Comparison ignores a leading grammatical `O` or `the` and normalizes dash typography. Core capitalization remains significant, including `LORD` versus `Lord`.",
            "",
            "`diff_both_refs_agree` is the highest-priority review class. `diff_both_refs_disagree` must remain review-only.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-db", type=pathlib.Path, default=SOURCE_DB)
    parser.add_argument("--bible-db", type=pathlib.Path, default=BIBLE_DB)
    parser.add_argument("--csv", type=pathlib.Path, default=OUT_CSV)
    parser.add_argument("--grouped-csv", type=pathlib.Path, default=GROUPED_CSV)
    parser.add_argument("--summary", type=pathlib.Path, default=SUMMARY)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    forms = load_candidate_forms()
    occurrences = load_occurrences(args.source_db)
    verses = load_verses(args.bible_db)

    fieldnames = [
        "status", "category", "testament", "source_ref", "checked_ref", "strongs",
        "surface_text", "morphology", "entity_type", "canonical_label", "expected_forms",
        "goi_form", "kjv_form", "webus_form", "goi_text", "kjv_text", "webus_text",
        "source_note", "review_state", "review_note",
    ]
    output_rows_with_ref: list[tuple[int, int, int, dict[str, object]]] = []
    counts: Counter[str] = Counter()
    category_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for occurrence in occurrences:
        book, chapter, verse = occurrence.check_ref
        texts = {
            edition: verses.get((edition, book, chapter, verse), "")
            for edition in EDITIONS
        }
        expected = forms.get(occurrence.strongs, [])
        matched = {edition: match_form(texts[edition], expected) for edition in EDITIONS}
        source_ref_tuple = (occurrence.book, occurrence.chapter, occurrence.verse)
        used_direct_fallback = False
        # A MorphHB verse can map only partly to the noted KJV verse (Psalm
        # 13:6 is split between KJV 13:5 and 13:6). If the mapped verse has no
        # candidate in any witness, use the direct verse shared by all three
        # English editions rather than manufacturing a three-way absence.
        if occurrence.check_ref != source_ref_tuple and not any(matched.values()):
            direct_texts = {
                edition: verses.get((edition, *source_ref_tuple), "")
                for edition in EDITIONS
            }
            direct_matched = {
                edition: match_form(direct_texts[edition], expected)
                for edition in EDITIONS
            }
            if any(direct_matched.values()):
                book, chapter, verse = source_ref_tuple
                texts = direct_texts
                matched = direct_matched
                used_direct_fallback = True
        status = classify(matched["GOI_En"], matched["KJV"], matched["WEBUS"])
        suppression_note = SOURCE_NAME_AUDIT_SUPPRESSIONS.get(
            (occurrence.book, occurrence.chapter, occurrence.verse, occurrence.strongs),
            "",
        )
        equivalence_note = grammatical_equivalence_note(
            occurrence.strongs, matched["GOI_En"], matched["KJV"], matched["WEBUS"]
        )
        if suppression_note:
            review_state = "documented_closure"
            review_note = suppression_note
        elif status != "ok" and equivalence_note:
            review_state = "accepted_policy"
            review_note = equivalence_note
        elif status != "ok":
            review_state = "active_review"
            review_note = ""
        else:
            review_state = "informational" if used_direct_fallback else "ok"
            review_note = (
                "Used direct verse because the mapped verse contained no candidate in any witness."
                if used_direct_fallback else ""
            )
        source_ref = f"{occurrence.book} {occurrence.chapter}:{occurrence.verse}"
        checked_ref = f"{book} {chapter}:{verse}"
        row: dict[str, object] = {
            "status": status,
            "category": occurrence.category,
            "testament": occurrence.testament,
            "source_ref": source_ref,
            "checked_ref": checked_ref,
            "strongs": occurrence.strongs,
            "surface_text": occurrence.surface_text,
            "morphology": occurrence.morphology,
            "entity_type": occurrence.entity_type,
            "canonical_label": occurrence.canonical_label,
            "expected_forms": "; ".join(expected),
            "goi_form": matched["GOI_En"] or "",
            "kjv_form": matched["KJV"] or "",
            "webus_form": matched["WEBUS"] or "",
            "goi_text": texts["GOI_En"],
            "kjv_text": texts["KJV"],
            "webus_text": texts["WEBUS"],
            "source_note": occurrence.source_note,
            "review_state": review_state,
            "review_note": review_note,
        }
        output_rows_with_ref.append(
            (occurrence.book_num, occurrence.chapter, occurrence.verse, row)
        )
        counts[status] += 1
        category_counts[occurrence.category][status] += 1

    priority = {status: index for index, status in enumerate(STATUS_ORDER)}
    output_rows = [
        row for _book_num, _chapter, _verse, row in sorted(
            output_rows_with_ref,
            key=lambda item: (
                priority[str(item[3]["status"])], item[0], item[1], item[2],
                item[3]["strongs"], item[3]["surface_text"],
            ),
        )
    ]
    flagged = [row for row in output_rows if row["status"] != "ok"]

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    decision_groups = write_grouped_queue(args.grouped_csv, output_rows)
    write_summary(
        args.summary, args.csv, len(output_rows), counts, category_counts, flagged,
        args.grouped_csv, decision_groups,
    )

    print(f"Audited {len(output_rows)} source-name occurrences; flagged {len(flagged)}.")
    print("Status counts: " + ", ".join(f"{status}={counts[status]}" for status in STATUS_ORDER))
    print(f"CSV: {args.csv}")
    print(f"Grouped CSV: {args.grouped_csv}")
    print(f"Summary: {args.summary}")


if __name__ == "__main__":
    main()
