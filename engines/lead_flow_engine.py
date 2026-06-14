import json
import os
from pathlib import Path

def generate_lead_flow(asset, logic_profile=None, output_dir=None):
    logic = logic_profile or {}

    tags = logic.get("routingTags", ["general"])
    if isinstance(tags, str):
        tags = [tags]

    lead_fields = [
        {"name": "name", "type": "string", "required": True},
        {"name": "email", "type": "email", "required": True},
        {"name": "business_name", "type": "string", "required": False}
    ]

    # Add domain-specific fields roughly
    domain = logic.get("domain", "general")
    if domain == "funding":
        lead_fields.append({"name": "monthly_revenue", "type": "number", "required": True})
        lead_fields.append({"name": "funding_need", "type": "number", "required": True})
    elif domain == "insurance":
        lead_fields.append({"name": "annual_premium", "type": "number", "required": True})

    flow = {
        "primaryAction": asset.get("primaryAction", "Get My Result"),
        "leadFields": lead_fields,
        "routingTags": tags,
        "qualificationRules": [
            {
                "condition": "all fields provided",
                "action": "route to sales"
            }
        ],
        "followUpSequence": [
            {"day": 0, "type": "email", "subject": f"Your {asset.get('name', 'Result')} is inside"},
            {"day": 2, "type": "email", "subject": "Any questions?"}
        ]
    }

    if output_dir:
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        try:
            with open(target / "lead-flow.json", "w", encoding="utf-8") as f:
                json.dump(flow, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass # Do not crash

    return flow
