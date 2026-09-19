# Arabic Gospel recovery plan — 2026-09-18

## Status and scope

The existing `GOI_Bible/GOI_Bible_ar/` Gospel corpus is a **rejected machine
draft**. It has all 3,779 expected files and passes coordinate, empty-file,
duplicate-coordinate, and Arabic-script checks. It fails noun/Strong's
coverage: 4,131 of 12,021 checked NT noun positions (34.4%). It is untracked
and must not be committed, packaged, or deployed.

No further Arabic model request is allowed until the preflight gates below
pass. This avoids spending tokens repeatedly re-rendering a verse because a
matcher mistakes a valid Arabic inflection for a missing noun.

## What the Russian comparison does and does not show

`ru/translate_gospels.log` proves that the Russian run used one continuous,
logged, sequential MAT→MRK→LUK→JHN batch and produced 3,779 files. It does
not preserve its shell launcher, supervisor configuration, or a noun-coverage
report. It is evidence for the operational properties to retain (one process,
append-only log, clear book boundaries and completion receipts), not evidence
that Arabic can skip Arabic-specific morphology and semantic QA.

## Recovery gates

### Gate A — freeze and inventory (no model calls)

1. Keep the rejected Arabic files uncommitted and label every report `draft`.
2. Save the failing coverage list by book and Strong's number.
3. Preserve the source noun ledger, proposed-default ledger, model/profile
settings, and runner logs as audit inputs. Never overwrite them to make the
failure disappear.

### Gate B — Arabic matcher and vocabulary pilot (no Gospel-scale run)

1. Build an Arabic matcher from reviewed observed forms, not from unconstrained
root-prefix guesses. It must normalize vowel marks/tatweel and recognize
documented clitic, plural, dual, case, and possessive forms.
2. Keep an explicit irregular-form table with evidence. Example: G80 default
`أخ` may match `أخوه`, `أخا`, `أخي`, `إخوة`, and `إخوته`; it must not accept
unrelated words beginning with `اخ`.
3. Add unit tests for every accepted form and a negative false-positive test.
4. Run the matcher against a hand-reviewed pilot of Matthew 1. Every remaining
miss is classified as one of: valid inflection, wrong default, needed
contextual sense, source-anchor defect, or actual translation defect.
5. Add only reviewed forms to the matcher or a narrow contextual override. Do
not bulk-add model guesses or weaken the matcher to increase a percentage.

**Gate B exit:** all Matthew 1 noun positions have a documented disposition;
the matcher has positive and negative tests; a reviewer signs the pilot report.

### Gate C — controlled generation pilot

1. Re-render a small fixed scope (Matthew 1 only) with a saved batch receipt:
absolute Conda Python path, `use_model deepseek`, exact model, `flex`, one
worker, lock path, prompt version, source commit, log path, and output count.
2. Validate a candidate verse before it replaces a draft file. The validator
uses the reviewed Arabic matcher, then requires the coordinate, Arabic-script,
single-line, non-empty, and noun-anchor gates.
3. A rejected candidate is retained in a quarantine report with its failing
anchors; it is never written as canonical output. Stop at a repeated same
coordinate rather than retrying indefinitely.

**Gate C exit:** Matthew 1 is 100% noun-covered under reviewed matcher rules;
all structural gates pass; the report and defects are committed before scope
expansion.

### Gate D — book-at-a-time recovery

Run Matthew, then Mark, Luke, and John. After each book:

1. Require 100% coverage after documented textual-policy exclusions.
2. Run Arabic script gate, coordinate comparison, duplicate check, and
matcher-dictionary duplicate check.
3. Record every defect in the cross-language regression ledger and inspect
the same issue class in every active language.
4. Commit the passing book plus its reports; do not defer validation until all
four books are generated.

### Gate E — Gospel release candidate

Only after four book receipts pass: run full-Gospel coverage, script, GOI
coordinate, duplicate, semantic-review, and release-integrity gates. A native
Arabic reviewer must record scope, findings, and resolutions. Only then may
the corpus be committed and later promoted through the new-language recipe.

## Batch-runner requirements

The next runner must be a tracked project script, not an ad-hoc terminal or
transient systemd command. It must provide: an exclusive lock; absolute
interpreter; DeepSeek-only/Flex assertion; append-only JSONL/event log;
per-verse quarantine; bounded retries; a restartable checkpoint; a 20-minute
heartbeat reporting current coordinate and pass/fail counts; and a final
nonzero exit unless every expected coordinate and quality gate passes.

The heartbeat is observability only. The runner itself owns resumption and
must not claim completion based solely on process exit or file count.
