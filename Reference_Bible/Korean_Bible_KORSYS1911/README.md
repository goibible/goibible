# First Korean Bible (1911)

This directory preserves the public-domain Korean reference text used for the
GOI Korean translation pipeline.

- Edition: First Korean Bible (1911), catalog identifier `KORSYS`
- Language: Korean (`ko`)
- Rights: Public Domain / OPEN, according to Digital Bible Society's Find a
  Bible record
- Source record: https://dev.find.bible/bibles/KORSYS/
- Text archive: https://archive.org/details/KORSYS_DBS_HS
- Downloaded source: `source/Korean-Bible-Unicode-1911_djvu.txt`
- SHA-256: `9d106a786a2cfb08fecb778e06ba7794ed71d0ab6e40cf06fd6a654748e8530a`
- Structured atomization source: https://ebible.org/kor/kor_html.zip

The downloaded file is an archive text export and is retained as source
material, not as the normalized GOI corpus. Its OCR/text layout must be
validated and atomized into GOI-versification-aligned files before translation
work begins. It is reference and QA material only; the future `GOI_Ko`
translation will be generated from the Hebrew WLC and Greek TR1550 sources.

The structured export has been atomized as far as its supplied verse markers
allow. `alignment_report.json` records 30,991 available verses and 111 KJV
coordinates still requiring source-level resolution. Translation must wait on
that gap report.
