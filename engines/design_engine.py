import json
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DESIGN_SYSTEMS_DIR = ROOT / "design-systems"

DEFAULT_DESIGN_SYSTEM = {
  "brand": "FoundryOS Default",
  "theme": "light",
  "font": "Inter",
  "radius": "8px",
  "tone": "professional",
  "layout": "standard"
}

def get_design_system(asset=None):
    try:
        path = DESIGN_SYSTEMS_DIR / "moonshine-capital.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
    except Exception:
        pass
    return DEFAULT_DESIGN_SYSTEM
