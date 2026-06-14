# Registry Imports

This folder is used for importing assets into the FoundryOS registry via CSV.

The `registry_importer.py` engine provides the following functions:
- `load_csv_rows`
- `normalize_row`
- `write_normalized_assets`

Use these functions to bulk load ideas, calculators, and assessments from CSV into `registry/normalized/assets.json`.
