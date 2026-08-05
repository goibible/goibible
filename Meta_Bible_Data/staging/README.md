# GOI Staging

This directory is for review artifacts that support a release but are not the
app-facing downloads themselves.

- `reports/`: coverage reports, validation logs, and other human-review output.
- `tmp/`: scratch files; ignored by git.

The public app download payload remains `goi_db_download/`. Build it with:

```bash
python3 scripts/goi_language_pipeline.py stage GOI_vi
```

