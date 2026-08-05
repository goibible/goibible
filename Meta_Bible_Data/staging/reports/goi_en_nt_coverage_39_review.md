# GOI English NT Coverage Review: 39 Missing Noun Tokens

Date: 2026-08-03

Result: all 39 former `missing` noun-coverage rows were resolved without
additional flatfile verse edits. The review found no confirmed English verse
losses in this batch. Resolution was by either textual-policy suppression or by
teaching the coverage checker accepted contextual renderings already present in
the English text.

## Textual-Policy Suppressions

These TR-only tokens are intentionally absent from the main text because GOI's
documented textual policy uses the preferred/shorter critical reading.

| Ref | Token | Disposition |
| --- | --- | --- |
| ROM 12:11 | time | Suppressed; GOI intentionally reads "serving the Lord." |
| GAL 3:1 | truth | Suppressed; shorter critical text omits the phrase. |
| 1TI 3:16 | God | Suppressed; GOI intentionally reads "He who was revealed." |
| 1JN 5:7 | heaven, Father, word, Spirit | Suppressed; Comma Johanneum phrase omitted from main text. |
| 1JN 5:8 | earth | Suppressed; "in earth" phrase omitted from shorter main text. |
| REV 1:11 | Alpha, Omega | Suppressed; shorter critical text omits this phrase here. |

## Accepted Contextual Renderings

These were already represented in the English, but the checker was too literal.

| Ref | Expected | Accepted English Rendering |
| --- | --- | --- |
| MAT 9:16 | fullness | patch / piece / fill idea |
| MAT 9:16 | division | tear / rent / hole idea |
| LUK 1:45 | perfection | fulfillment / completion |
| LUK 8:54 | servant | child / maid sense of `pais` |
| ACT 17:31 | faith | assurance / proof |
| ACT 19:24 | builder | craftsmen |
| ACT 19:38 | builder | craftsmen |
| ACT 19:38 | word | case / matter |
| ACT 20:36 | knee | knelt / kneeled |
| ACT 24:23 | relief | liberty / privileges |
| ACT 27:5 | depth | open sea / sea |
| 1CO 3:3 | zeal | jealousy / envy |
| 1CO 6:4 | court | judgments / case / court |
| 2CO 8:4 | comfort | entreaty / begged / appeal |
| 2CO 12:20 | zeal | jealousies |
| 2CO 12:20 | swelling | conceits / proud thoughts |
| EPH 4:19 | profit | working / business |
| 1TI 3:1 | visitation | office of overseer |
| 1TI 4:3 | taking | receiving |
| 1TI 5:14 | railing | reproach / insulting |
| 2TI 1:14 | that which is committed to | deposit / committed |
| HEB 9:2 | purpose | showbread / bread of presentation |
| HEB 11:19 | parable | figure / figuratively |
| HEB 12:20 | dart | arrows / shot through |
| JAS 1:11 | grace | beauty |
| JAS 1:11 | journey | pursuits / ways |
| JAS 3:4 | assault | impulse / desire / will |
| 1PE 3:3 | world | adornment / adorning |
| REV 22:14 | authority | right |

## Verification

`python3 tools/validate.py --lang en` now passes all 13 checks.
