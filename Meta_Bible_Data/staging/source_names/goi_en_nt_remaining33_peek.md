# GOI English NT Remaining 33 - Peek

After the first NT source-name cleanup, 33 NT rows still failed the strict expected-form audit.

## Clear Form Approvals

These are spelling/English-form differences, not obvious corpus errors:

- `MRK 3:8` `Idoumaia`: `Idumaea`
- `LUK 3:1` `Itouraia`: `Ituraea`
- `ROM 9:25` `Osee`: `Hosea`
- `2CO 6:15` `Belial`: `Beliar`
- `2PE 1:1` `Simon`: `Simeon`
- `2PE 2:15` `Bosor`: `Beor`
- `JUD 1:11` `Core`: `Korah`
- `REV 2:20` `Jezabel`: `Jezebel`

Status: all 8 have been added as approved English forms and now pass.

## Context/Form Issues

These are Greek `theos`/`kyrios` rows where the English rendering is grammatically valid but not the dictionary's exact singular form:

- `JHN 10:34`, `ACT 7:40`, `ACT 14:11`, `ACT 19:26`, `1CO 8:5`: plural/common `gods`.
- `MAT 20:8`, `MAT 21:40`, `LUK 20:13`, `LUK 20:15`: `owner of the vineyard`.
- `LUK 19:33`, `ACT 16:16`, `ACT 16:19`, `ACT 16:30`, `EPH 6:5`: `owners`, `masters`, `Sirs`.
- `2CO 11:2`: `godly zeal`.

## Needs Human Judgment / Likely Corpus Review

These may be acceptable pronoun compression, but the explicit source name is absent:

- `LUK 2:43` has Greek `Joseph`; GOI English says `his parents`.
- `JHN 13:1` has Greek `Jesus`; GOI English starts `knowing that his hour...`.
- `ACT 4:6` has Greek `Jerusalem`; GOI English says `high-priestly family`.
- `ACT 9:29` has `Lord Jesus`; GOI English says `He spoke boldly...`.
- `ACT 13:33` has `God` and `Jesus`; GOI English says `it has also been written...`.

## Special Case

- `MAT 16:17` `Iona/Jonah`: GOI English has `Bar-jona`. This is probably acceptable, but the matcher needs a compound-name form.

## Current Remaining NT Queue

After approving the 8 clear forms, NT `missing` rows are down to 25. The remaining rows are the context/form issues, likely corpus-review rows, and the `Bar-jona` compound-name matcher case.
