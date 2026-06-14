import json
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
LOGIC_LIBRARY_DIR = ROOT / "logic-library"

DEFAULT_LOGIC_PROFILE = {
    "id": "default",
    "name": "Default Profile",
    "domain": "general",
    "assetTypes": ["calculator"],
    "keywords": [],
    "audiences": ["general"],
    "problemStatements": ["A business decision needs to be made faster."],
    "inputs": [],
    "outputs": ["Calculated result"],
    "calculations": [],
    "recommendations": ["Review the result and take action."],
    "routingTags": ["general"]
}

def load_all_profiles():
    profiles = []
    if not LOGIC_LIBRARY_DIR.exists():
        return profiles

    for root, _, files in os.walk(LOGIC_LIBRARY_DIR):
        for file in files:
            if file.endswith(".json") and file != "logic.schema.json":
                path = Path(root) / file
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            profiles.append(data)
                except Exception:
                    pass
    return profiles

def score_profile(profile, asset):
    score = 0

    asset_text = ""
    for field in ["title", "name", "domain", "assetType", "type", "audience", "description", "problem", "category"]:
        val = asset.get(field, "")
        if isinstance(val, str):
            asset_text += " " + val.lower()

    # Check simple fields
    if profile.get("domain", "").lower() in asset_text:
        score += 2

    for atype in profile.get("assetTypes", []):
        if atype.lower() in asset_text:
            score += 1

    for kw in profile.get("keywords", []):
        if kw.lower() in asset_text:
            score += 2

    for aud in profile.get("audiences", []):
        if aud.lower() in asset_text:
            score += 1

    return score

def get_logic_profile(asset):
    if not asset:
        return DEFAULT_LOGIC_PROFILE

    profiles = load_all_profiles()
    if not profiles:
        return DEFAULT_LOGIC_PROFILE

    best_profile = None
    best_score = -1

    for profile in profiles:
        score = score_profile(profile, asset)
        if score > best_score:
            best_score = score
            best_profile = profile

    # Require at least some minimal match, or just return best if any keywords match
    if best_score > 0 and best_profile:
        return best_profile

    return DEFAULT_LOGIC_PROFILE
