# GOI English NT Name Audit - First 50

Scope: first 50 NT `missing` rows from the source-name audit after WLC/GOI alignment cleanup.

## Result

The first batch was mostly approved English spelling/plural differences from Strong's/KJV dictionary forms, not corpus errors.

Examples cleared by approved English forms:

- `Iakob`: `Jacob`
- `Ioudas`: `Judah`, `Judas`, `Jude`
- `Esaias`: `Isaiah`
- `Elias`: `Elijah`
- `Pharisee`: `Pharisees`
- `Zabulon`: `Zebulun`
- `Nephthalim`: `Naphtali`
- `Phares`: `Perez`
- `Rachab`: `Rahab`
- `Urias`: `Uriah`
- `Zorobabel`: `Zerubbabel`
- `Gomorrha`: `Gomorrah`
- `Sion`: `Zion`

Audit improvement:

- Before this batch: NT `missing` rows = 328.
- After first override pass: NT `missing` rows = 72.
- After spelling/plural/demonym cleanup: NT `missing` rows = 33.

## Remaining Shape

The remaining 33 are mostly not simple spelling misses. They include:

- Greek common/title Strong's used in non-divine or plural contexts (`theos`, `kyrios`).
- Implied/natural English renderings (`owners`, `parents`, `sons of Hamor`).
- A few remaining spelling choices (`Beliar`, `Hosea`, `Simeon`, `Beor`, `Korah`, `Jezebel`).
- Possible source/corpus review rows where the entity is genuinely absent from English wording.

Next pass should handle the remaining 33 individually, with context classification rather than blanket form additions.
