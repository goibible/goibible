# AGENTS.md — rules for every agent and tool in this repository

## DEFINITIVE SOURCE

There are exactly **two** definitive source texts. Everything else is derived.

| Testament | Definitive source | Where | Morphology / Strong's |
|---|---|---|---|
| Old Testament | **Westminster Leningrad Codex (WLC)**, Hebrew/Aramaic | `Reference_Bible/Hebrew_Bible_WLC/SOURCE/` (original XML); `One_Directory_WLC_KJV/` = the same text placed on the project's verse numbering | `Meta_Bible_Data/sources/morphhb/` |
| New Testament | **Textus Receptus 1550 (TR1550)**, Greek | `Reference_Bible/Greek_Bible_TR1550/SOURCE/`; `One_Directory_TR1550/` = per-verse files | Strong's tags in `greek_noun.sqlite3` |

Rules that follow from this:

1. **Meaning is decided by the definitive source.** A defect is a deviation from the Hebrew (OT) or Greek (NT), never from a reference translation.
2. **Exactly three roles exist.** `source` = the two texts above. `reference` = historical translations used only for corroboration, never copied (KJV, WEBUS, LSG1910, RV1909, RIV1927, VanDyck, CUV, and so on). `target` = every generated GOI edition (`GOI_Bible/GOI_Bible_*`). Nothing generated is ever a source.
3. **No other source-like text is to be added.** No Greek OT (Septuagint), no Hebrew NT, no modern Hebrew or modern Greek Bible may be placed under `Reference_Bible/` or presented as a spine. If one is ever added it is a `target` edition (or a clearly labelled `reference` with its own role), and only on the owner's explicit decision. Owner decision 2026-10-05: hold off on all of these.
4. **Never promote a generated or reference text to source**, and never "fix" the source to match a translation. Source texts are read-only.
5. **Language tags matter.** Biblical Hebrew is `hbo` and Ancient Greek is `grc`; Modern Hebrew is `he` and Modern Greek is `el`. KNOWN MISMATCH: `Meta_Bible_Data/sqlite/editions.json` currently tags WLC as `he` and TR1550 as `el`. Do not rely on those tags to tell a source from a modern edition; use the role above. Change the tags only after checking `verify_editions.py` and CI.

## TWO SPINES — never confuse them

- **Coordinate spine:** the verse files `NNN_BOOK_CCC_VVV_<EDITION>.txt`, numbered the way the repo numbers verses (KJV numbering, with Hebrew placed on it in `One_Directory_WLC_KJV`). It decides *which file* a verse lives in.
- **Anchor spine:** the Hebrew and Greek noun anchors read from the source morphology (`source_noun` in `grammar_tables.sqlite3`; `ot_noun_occurrences` in the per-language Hebrew databases). It decides *what meaning must be present*.

**Do not move text between coordinates to match another edition's verse division.** Before moving or splitting any text across verses, check the source verse for that coordinate (the WLC line in `ot_verses.wlc_text`, or the TR1550 verse file) and follow it. Incident 2026-10-05: text was moved in 1KI 18:33-34 and PSA 51/52/60 to match the KJV's split; the Hebrew spine places it where the original GOI had it, and the moves were reverted (`en/revert_spine_rewrite.tsv`).

## Related rules

- Translation execution guardrails: `Meta_Bible_Data/Bible_Noun_Extraction/AGENTS.md`.
- Divine-name policy for English (YHWH = Yahweh, Adonai = Lord, Yah = LORD, set by the owner 2026-10-05): see `FIXED` in `Meta_Bible_Data/Bible_Noun_Extraction/en/gen_en_ot_renderings.py` and the ledger `en/yahweh_rewrite.tsv`; applied in `GOI_Bible/GOI_Bible_English`.
