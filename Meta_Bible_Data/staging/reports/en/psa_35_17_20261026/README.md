# GOI English Psalm 35:17 — owner-confirmed correction, 2026-10-26

> Lord, how long will you look on? Rescue my soul from their destructions, my precious life from the young lions.

The owner confirmed this exact proposed wording. WLC Hebrew remains the definitive source: the final יחידתי (my only one / precious life) parallels נפשי (my soul). The former “from (young) lions my self” was ungrammatical. Sentence-initial Rescue is capitalized; Lord receives vocative punctuation. No source or reference edition was edited.

All four populated Hebrew noun anchors and single-line format passed before the canonical write. The complete source and before/after hashes are in `text_validation.json`.

A read-only inventory inspected 133 local SQLite databases, including ignored app/build files. Fifteen current app/distribution verse rows in fifteen databases now equal the canonical text; the English cube is the sixteenth updated database. Its verse chunk and four noun windows, corresponding hashes/features, and five sparse-index rows were regenerated with the production adapter/vectorizer. H5315 is explicitly aligned to the soul noun; the later life phrase renders יחידתי and is not a second source-noun occurrence. The whole-corpus cube input fingerprints were retained: this targeted repair does not certify unrelated corpus/build freshness.

The score-82 GOI_En randomizer records retain their existing score, not a newly calculated rating. Other editions, including WEBUS, were not changed. Seven historical backup/deployment/archive snapshots retain their original text and are explicitly listed in `sqlite_updates.json`.

`verify_sqlite.py` checks current copies, edition/coordinate identity, retained scores, SQLite quick checks, exact chunk hashes, sparse vector equality, and source immutability. `verification.json` records PASS. `sqlite_inventory.json` preserves the pre-update inventory. `sync_sqlite.py` records the narrowly scoped synchronization logic.

The commit contains the canonical verse, the two tracked distribution databases, this evidence, and the randomizer submodule commit containing its two tracked databases. Ignored runtime/build/cube artifacts were updated locally. Preexisting unrelated edits in distribution databases are preserved in the working tree and excluded from this commit by applying only this verse change to HEAD copies in an isolated Git index. No remote push or deployment is performed.
