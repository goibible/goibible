# fr OT noun-coverage triage (existing text vs generated OT noun table; WLC base)

Produced by `fr/verify_fr_ot.py` and a per-anchor count (run 2026-10-14). Measured, not estimated.

- OT verses with at least one noun anchor: **23145** (all verse files present); anchors checked: **146502**; anchors missing without review: **0** (0.00%); verses with a miss: **0** (0.00%)
- exact 141663 (96.70%), mined synonym 4839 (3.30%; accepted by hand-reviewed receipt in fr/ot_review_accept.tsv, post-verification fix log, or cross-language fix log; 3793 verses), missing 0
- RED 0 / ORANGE 18 / YELLOW 572 (the reviewed receipts; the 986 accepted anchors are mostly genealogy "engendra" for ben, cattle "bétail" for bœuf, and ruach rendered as souffle/esprit in context)
- undocumented misses: 0; YHWH verses without «Éternel»: 0
- Reference Bible for corroboration: Louis Segond 1910 (read only)

- 2026-10-14: after the full-corpus sense audit (5,361 flagged verses hand-reviewed against WLC/TR), most of the growth in accepted anchors is deliberate sense correction where the table default is the wrong sense in context (e.g. «traîneau aigu»→«or fin» for charuts, «perche»→«bannière» for nes, «citerne»→«fosse» for bor); each is logged in fr/ot_post_verify_fixes.tsv.
