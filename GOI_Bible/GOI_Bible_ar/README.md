# GOI Arabic Translation

**Status: partial Arabic translation draft; not released.**

The September 28, 2026 checkpoint contains all four Gospels (3,779 verses)
and Acts 1:1–12:9 (423 verses), for 4,202 Arabic draft verses. Gospel
noun/Strong's coverage is 12,021/12,021 after reconciliation. Coordinate,
single-line, Arabic-script, and original noun-span checks pass. Noun-number
alignment and full semantic release review remain pending.

The Arabic cube includes all 4,202 verses. SQL, sparse vectors, and all
178,046 dense vectors are synchronized and pass target preflight. The Acts
12:10 prison/guard-post mismatch is corrected in the source ledger, prompt,
and cube. The worker resumed on September 28 with a 20-minute heartbeat. A later
Acts 12:18 daylight-anchor mismatch was corrected, and the worker restarted
on September 29. See the [live run checkpoint](../../Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_rest_nt_run_status.md)
for progress beyond the September 28 counts above.
See the [current reconciliation checkpoint](../../Meta_Bible_Data/Bible_Noun_Extraction/ar/reports/ar_gospel_reconciliation_2026-09-28.md)
for evidence and vector/preflight status.

`Reference_Bible/Arabic_Bible_VanDyck1865/` contains the public-domain Arabic
Van Dyck comparison reference, preserved source archive, reproducible
GOI-coordinate normalization, and the two documented versification merges.

Verse drafts use UTF-8 `NNN_BOOK_CCC_VVV_GOI_Ar.txt` flatfiles translated
from the Greek TR1550 source. Hebrew WLC source preparation is complete;
Arabic OT translation has not started. The Van Dyck text is a comparison
reference and must not be copied into GOI output.
