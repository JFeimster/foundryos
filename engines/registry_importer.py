import csv
import json
import re
from pathlib import Path

def slugify(value):
    value = str(value or "").lower()
    value = re.sub(r'["“”()]+', "", value)
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "untitled"

def load_csv_rows(filepath):
    path = Path(filepath)
    if not path.exists():
        return []

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def normalize_row(row):
    title = row.get("title") or row.get("name") or "Untitled"
    return {
        "id": row.get("id") or slugify(title),
        "title": title,
        "slug": row.get("slug") or slugify(title),
        "domain": row.get("domain", "general"),
        "category": row.get("category", "general"),
        "assetType": row.get("assetType", "calculator"),
        "audience": row.get("audience", "Business owners"),
        "description": row.get("description", ""),
        "keywords": [k.strip() for k in row.get("keywords", "").split(",") if k.strip()],
        "source": row.get("source", "csv-import"),
        "status": row.get("status", "draft")
    }

def write_normalized_assets(assets, output_path=None):
    if output_path is None:
        root = Path(__file__).resolve().parents[1]
        output_path = root / "registry" / "normalized" / "assets.json"

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing to append/update
    existing = []
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass

    # Update logic (replace if id exists)
    lookup = {item["id"]: item for item in existing}
    for asset in assets:
        lookup[asset["id"]] = asset

    final_list = list(lookup.values())

    with open(path, "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)
