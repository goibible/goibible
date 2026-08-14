# GOI English KJV/WEBUS Name Scrub

Deterministic review queue comparing GOI English name renderings with KJV and WEBUS for each source-name occurrence.

- Source-name occurrences audited: 42322
- Flagged occurrences: 5459
- OK occurrences: 36863
- Active review occurrences: 0
- Active `no_goi_form` occurrences: 0
- Documented `no_goi_form` closures: 8
- Accepted policy occurrences: 5451
- CSV: `/home/albert/projects/bible/Meta_Bible_Data/staging/source_names/goi_en_kjv_webus_name_scrub.csv`
- Grouped `diff_both_refs_agree` decisions: `/home/albert/projects/bible/Meta_Bible_Data/staging/source_names/goi_en_kjv_webus_diff_both_refs_agree_groups.csv`

## Status counts

| Status | Count |
|---|---:|
| `diff_both_refs_agree` | 2118 |
| `diff_kjv_only` | 753 |
| `diff_webus_only` | 263 |
| `diff_both_refs_disagree` | 76 |
| `no_goi_form` | 8 |
| `no_ref_form` | 2241 |
| `ok` | 36863 |

## Person/place proper names

| Status | Count |
|---|---:|
| `diff_both_refs_agree` | 1180 |
| `diff_kjv_only` | 567 |
| `diff_webus_only` | 219 |
| `diff_both_refs_disagree` | 44 |
| `no_goi_form` | 1 |
| `no_ref_form` | 2174 |
| `ok` | 24318 |

## Divine names and titles

| Status | Count |
|---|---:|
| `diff_both_refs_agree` | 938 |
| `diff_kjv_only` | 186 |
| `diff_webus_only` | 44 |
| `diff_both_refs_disagree` | 32 |
| `no_goi_form` | 7 |
| `no_ref_form` | 67 |
| `ok` | 12545 |

## Grouped reference-consensus decisions

- Active rendering groups: 0
- Accepted policy groups: 305
- Total grouped decisions: 305

## No-GOI-form review

| Source ref | Strong's | Disposition |
|---|---|---|
| ACT 4:6 | G2419 | Jerusalem is present in ACT 4:5. |
| ACT 9:29 | G2424 | Lord Jesus is present in ACT 9:28. |
| ACT 9:29 | G2962 | Lord Jesus is present in ACT 9:28. |
| ACT 13:33 | G2316 | God/Jesus clause is present in ACT 13:32. |
| ACT 13:33 | G2424 | God/Jesus clause is present in ACT 13:32. |
| 1TI 3:16 | G2316 | Use 'He who was revealed', not TR 'God'. |
| 1JN 3:16 | G2316 | Use shorter/main reading without optional 'of God'. |
| 1JN 5:7 | G4151 | Use shorter early text; Spirit appears in 1JN 5:8. |

## Top flagged rows

Rows are prioritized with `diff_both_refs_agree` first. Differences where the references disagree remain review-only.

No active flagged rows.

## Interpretation

KJV and WEBUS are deterministic reference witnesses, not final source authority. This audit does not edit verses or decide that a flagged rendering is wrong.

Comparison ignores a leading grammatical `O` or `the` and normalizes dash typography. Core capitalization remains significant, including `LORD` versus `Lord`.

`diff_both_refs_agree` is the highest-priority review class. `diff_both_refs_disagree` must remain review-only.
