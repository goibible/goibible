# GOI English KJV/WEBUS Name Scrub

Deterministic review queue comparing GOI English name renderings with KJV and WEBUS for each source-name occurrence.

- Source-name occurrences audited: 42322
- Flagged occurrences: 5482
- OK occurrences: 36840
- Active `no_goi_form` occurrences: 0
- Documented `no_goi_form` closures: 8
- Accepted grammatical-equivalence occurrences: 605
- CSV: `/home/albert/projects/bible/Meta_Bible_Data/staging/source_names/goi_en_kjv_webus_name_scrub.csv`
- Grouped `diff_both_refs_agree` decisions: `/home/albert/projects/bible/Meta_Bible_Data/staging/source_names/goi_en_kjv_webus_diff_both_refs_agree_groups.csv`

## Status counts

| Status | Count |
|---|---:|
| `diff_both_refs_agree` | 2141 |
| `diff_kjv_only` | 753 |
| `diff_webus_only` | 261 |
| `diff_both_refs_disagree` | 78 |
| `no_goi_form` | 8 |
| `no_ref_form` | 2241 |
| `ok` | 36840 |

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
| `diff_both_refs_agree` | 961 |
| `diff_kjv_only` | 186 |
| `diff_webus_only` | 42 |
| `diff_both_refs_disagree` | 34 |
| `no_goi_form` | 7 |
| `no_ref_form` | 67 |
| `ok` | 12522 |

## Grouped reference-consensus decisions

- Active rendering groups: 277
- Accepted grammatical-equivalence groups: 31
- Total grouped decisions: 308

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

| Status | Category | Source ref | Checked ref | Strong's | GOI | KJV | WEBUS | Label |
|---|---|---|---|---|---|---|---|---|
| diff_both_refs_agree | divine_name_or_title | GEN 2:7 | GEN 2:7 | H3068 | Jehovah | the LORD | The LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 2:8 | GEN 2:8 | H3068 | Jehovah | the LORD | The LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 2:15 | GEN 2:15 | H3068 | Jehovah | the LORD | The LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 2:16 | GEN 2:16 | H3068 | the Lord | the LORD | The LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 3:21 | GEN 3:21 | H3068 | Jehovah | the LORD | The LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 6:6 | GEN 6:6 | H3068 | Jehovah | the LORD | The LORD | Yᵉhôvâh |
| diff_both_refs_agree | person_or_place | GEN 9:18 | GEN 9:18 | H8035 | Sem | Shem | Shem | Shêm |
| diff_both_refs_agree | person_or_place | GEN 10:4 | GEN 10:4 | H3794 | Chittim | Kittim | Kittim | Kittîy |
| diff_both_refs_agree | person_or_place | GEN 10:6 | GEN 10:6 | H4714 | Egypt | Mizraim | Mizraim | Mitsrayim |
| diff_both_refs_agree | person_or_place | GEN 10:7 | GEN 10:7 | H5454 | Sabta | Sabtah | Sabtah | Çabtâʼ |
| diff_both_refs_agree | divine_name_or_title | GEN 11:6 | GEN 11:6 | H3068 | Jehovah | the LORD | The LORD | Yᵉhôvâh |
| diff_both_refs_agree | person_or_place | GEN 11:26 | GEN 11:26 | H8646 | Tarah | Terah | Terah | Terach |
| diff_both_refs_agree | person_or_place | GEN 11:28 | GEN 11:28 | H3778 | Chaldeans | Chaldees | Chaldees | Kasdîy |
| diff_both_refs_agree | person_or_place | GEN 11:31 | GEN 11:31 | H3778 | Chaldeans | Chaldees | Chaldees | Kasdîy |
| diff_both_refs_agree | person_or_place | GEN 11:31 | GEN 11:31 | H8646 | Tarah | Terah | Terah | Terach |
| diff_both_refs_agree | divine_name_or_title | GEN 12:1 | GEN 12:1 | H3068 | The Lord | the LORD | the LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 12:4 | GEN 12:4 | H3068 | Jehovah | the LORD | the LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 15:2 | GEN 15:2 | H3069 | Lord God | Lord GOD | Lord GOD | Yᵉhôvih |
| diff_both_refs_agree | person_or_place | GEN 15:7 | GEN 15:7 | H3778 | Chaldeans | Chaldees | Chaldees | Kasdîy |
| diff_both_refs_agree | divine_name_or_title | GEN 18:1 | GEN 18:1 | H3068 | Jehovah | the LORD | The LORD | Yᵉhôvâh |
| diff_both_refs_agree | person_or_place | GEN 19:37 | GEN 19:37 | H4124 | Moab | Moabites | Moabites | Môwʼâb |
| diff_both_refs_agree | person_or_place | GEN 19:37 | GEN 19:37 | H4124 | Moab | Moabites | Moabites | Môwʼâb |
| diff_both_refs_agree | person_or_place | GEN 23:10 | GEN 23:10 | H2845 | Hethites | Hittite | Hittite | Chêth |
| diff_both_refs_agree | person_or_place | GEN 23:10 | GEN 23:10 | H2845 | Hethites | Hittite | Hittite | Chêth |
| diff_both_refs_agree | person_or_place | GEN 24:10 | GEN 24:10 | H763 | Aram-naharaim | Mesopotamia | Mesopotamia | ʼĂram Nahărayim |
| diff_both_refs_agree | person_or_place | GEN 24:10 | GEN 24:10 | H763 | Aram-naharaim | Mesopotamia | Mesopotamia | ʼĂram Nahărayim |
| diff_both_refs_agree | divine_name_or_title | GEN 24:31 | GEN 24:31 | H3068 | Jehovah | the LORD | the LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 24:40 | GEN 24:40 | H3068 | the Lord | The LORD | The LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 24:48 | GEN 24:48 | H3068 | Jehovah | the LORD | the LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 24:48 | GEN 24:48 | H3068 | Jehovah | the LORD | the LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 26:24 | GEN 26:24 | H3068 | Jehovah | the LORD | The LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 26:28 | GEN 26:28 | H3068 | the Lord | the LORD | the LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 28:12 | GEN 28:12 | H430 | God | angels | angels | ʼĕlôhîym |
| diff_both_refs_agree | divine_name_or_title | GEN 28:16 | GEN 28:16 | H3068 | the Lord | the LORD | the LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 29:31 | GEN 29:31 | H3068 | Jehovah | the LORD | The LORD | Yᵉhôvâh |
| diff_both_refs_agree | divine_name_or_title | GEN 31:30 | GEN 31:30 | H430 | god | gods | gods | ʼĕlôhîym |
| diff_both_refs_agree | person_or_place | GEN 36:4 | GEN 36:4 | H7467 | Raguel | Reuel | Reuel | Rᵉʻûwʼêl |
| diff_both_refs_agree | person_or_place | GEN 36:9 | GEN 36:9 | H123 | Edom | Edomites | Edomites | ʼĔdôm |
| diff_both_refs_agree | person_or_place | GEN 36:23 | GEN 36:23 | H5935 | Alian | Alvan | Alvan | ʻAlvân |
| diff_both_refs_agree | person_or_place | GEN 36:23 | GEN 36:23 | H8195 | Shephi | Shepho | Shepho | Shᵉphôw |
| diff_both_refs_agree | person_or_place | GEN 36:26 | GEN 36:26 | H1789 | Dishan | Dishon | Dishon | Dîyshân |
| diff_both_refs_agree | person_or_place | GEN 36:39 | GEN 36:39 | H4105 | Mehetabeel | Mehetabel | Mehetabel | Mᵉhêyṭabʼêl |
| diff_both_refs_agree | person_or_place | GEN 36:43 | GEN 36:43 | H123 | Edom | Edomites | Edomites | ʼĔdôm |
| diff_both_refs_agree | person_or_place | GEN 36:43 | GEN 36:43 | H123 | Edom | Edomites | Edomites | ʼĔdôm |
| diff_both_refs_agree | person_or_place | GEN 41:56 | GEN 41:56 | H4713 | of Egypt | Egyptians | Egyptians | Mitsrîy |
| diff_both_refs_agree | person_or_place | GEN 41:56 | GEN 41:56 | H4714 | Egypt | Egyptians | Egyptians | Mitsrayim |
| diff_both_refs_agree | person_or_place | GEN 46:8 | GEN 46:8 | H3478 | sons of Israel | children of Israel | children of Israel | Yisrâʼêl |
| diff_both_refs_agree | person_or_place | GEN 46:10 | GEN 46:10 | H7586 | Saul | Shaul | Shaul | Shâʼûwl |
| diff_both_refs_agree | person_or_place | EXO 1:7 | EXO 1:7 | H3478 | sons of Israel | children of Israel | children of Israel | Yisrâʼêl |
| diff_both_refs_agree | person_or_place | EXO 1:12 | EXO 1:12 | H3478 | Israel | children of Israel | children of Israel | Yisrâʼêl |

## Interpretation

KJV and WEBUS are deterministic reference witnesses, not final source authority. This audit does not edit verses or decide that a flagged rendering is wrong.

Comparison ignores a leading grammatical `O` or `the` and normalizes dash typography. Core capitalization remains significant, including `LORD` versus `Lord`.

`diff_both_refs_agree` is the highest-priority review class. `diff_both_refs_disagree` must remain review-only.
