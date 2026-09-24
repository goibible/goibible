# French NT pilot: Jude (2026-09-24)

Draft only (`translate_verses.py --allow-unreviewed-cube-draft`), written to staging, not `GOI_Bible/GOI_Bible_fr`.
Model DeepSeek-V4-Flash-0731 (DeepInfra), one stream, `--require-noun-anchors`, cube `fr_lsg`.

| Run | References in prompt | Verses | Noun coverage | Anchor stops | Mean 4-gram overlap with LSG | Verses > 0.6 overlap |
|---|---|---:|---:|---:|---:|---:|
| A `jude_pilot/` | GOI English, GOI Spanish, **LSG 1910** | 25 | 100% | 2 (both root-fixed) | 0.36 | 4 |
| B `jude_pilot_noLSG/` | GOI English, GOI Spanish | 25 | 100% | 0 | 0.25 | 1 |

## What worked

- **Translates the Greek, not the reference.** Where the Textus Receptus and LSG's critical text differ, both runs follow
  the TR: 1:1 «sanctifiés» (ἡγιασμένοις; LSG «aimés»), 1:4 includes θεόν, 1:22 «ayez pitié … en discernant», 1:25
  «Dieu seul sage» without LSG's «par Jésus-Christ … dès avant tous les temps».
- Divine names per policy (NT κύριος → «Seigneur»); consistent vouvoiement; the Jude sense («Jude», not «Judas») resolved.
- Script gate clean (Latin only); every anchor present.

## Anchor stops (fixed at the root, not per verse)

1. 1:13 «étoiles **errantes**» failed anchor «errant»: `FrenchMatcher` lacked feminine agreement. Added regular feminine
   formation (+e, -er/-ère, -ier/-ière, -en/-enne, -on/-onne, -el/-elle, -eux/-euse, -f/-ve, -eur/-euse/-rice) + plurals,
   with negative controls (roi ≠ reine).
2. 1:23 model wrote «avec **crainte**» against default «peur» (φόβος, G5401). The cube had flagged it (LSG agreement 1/47)
   but the LSG judge accepted «peur» as "natural modern French". Default moved to «crainte»; «peur» accepted as a form.
   **Lesson: the judge's `ok` verdicts on low-agreement defaults were too lenient on register.**

## Findings to act on before the full NT

| # | Finding | Evidence | Proposed fix |
|---|---|---|---|
| 1 | LSG in the prompt leaks wording | run A 1:12 reproduces LSG's «faisant impudemment bonne chère … deux fois morts, déracinés»; overlap 0.36 vs 0.25, near-copies 4 vs 1 | **drop LSG from translator references**; keep it for QA/cube only |
| 2 | Wrong-sense anchors forced | 1:12 «dans vos amours» (ἀγάπαις = love-feasts), 1:6 «leur commencement» (ἀρχή = rank), 1:16 «admirant les visages» (πρόσωπα = persons) | context senses: agapes / dignité / personnes |
| 3 | Same-verse default collision | 1:13 «les ténèbres des ténèbres» (ζόφος and σκότος both «ténèbres») | ζόφος (G2217) → «obscurité» |
| 4 | Register-lenient defaults | «peur» for φόβος; the 336 low-agreement defaults judged `ok` | re-judge them with a "standard French Bible register" criterion |
| 5 | Structural defect not gated | run B 1:24 starts with a stray colon («:Or à celui…») | structural lint (leading punctuation, doubled spaces, unbalanced quotes) before write |
| 6 | Occasional garbling | run B 1:4 «… Seigneur Jésus-Christ, Dieu» (run A correct) | the per-verse wrong-sense/clause sweep already built for Russian |

## Gate for the canonical NT run

`translate_verses.py` refuses canonical output until every French lexeme is `reviewed` (a good gate). The French
defaults are AI-drafted, LSG-measured and partly LSG-judged, not human-reviewed. Owner decision: what counts as
"reviewed" for French (e.g. LSG-agreement ≥ threshold or LSG-judge `ok`/fixed), or a human pass.
