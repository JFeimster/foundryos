#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "normalized" / "assets.json"
OUTPUTS = ROOT / "outputs"
SPECS = ROOT / "specs"

sys.path.insert(0, str(ROOT))

from builders import calculator as calculator_builder
from builders import dashboard as dashboard_builder
from builders import landing_page as landing_page_builder
from builders import portal as portal_builder
from builders import scorecard as scorecard_builder
from builders import simulator as simulator_builder


def slugify(value):
    value = str(value or "").lower()
    value = re.sub(r'["“”()]+', "", value)
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "untitled"


def clean(value):
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    value = re.sub(r"\s*\d+(?:,\s*\d+)*\s*$", "", value).strip()
    return value or "A business decision needs to be made faster and with less guesswork."


def normalize_asset_type(value):
    raw = re.sub(r"[\s_]+", "-", str(value or "").strip().lower())
    raw = re.sub(r"-+", "-", raw)
    aliases = {
        "static-calculator": "calculator",
        "calculator": "calculator",
        "scorecard": "scorecard",
        "qualifier": "scorecard",
        "assessment": "scorecard",
        "simulator": "simulator",
        "generator": "simulator",
        "dashboard": "dashboard",
        "portal": "portal",
        "data-room": "portal",
        "landing-page": "landing_page",
        "landing_page": "landing_page",
        "landing": "landing_page",
    }
    return aliases.get(raw, raw)


def load_assets():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def save_assets(assets):
    REGISTRY.write_text(json.dumps(assets, indent=2), encoding="utf-8")


def normalize(asset):
    asset = dict(asset)
    asset.setdefault("id", slugify(asset.get("name", "asset")))
    asset.setdefault("audience", "Business owners")
    asset.setdefault("problem", "Turn a painful business decision into a useful interactive asset.")
    asset.setdefault("coreLogic", "Collect relevant inputs, calculate a useful result, and route the user to the next action.")
    asset.setdefault("tier", 1)
    asset.setdefault("assetType", "calculator")
    asset["assetType"] = normalize_asset_type(asset.get("assetType"))
    asset.setdefault("primaryAction", "Get My Result")
    return asset


def find_asset(query):
    query = query.lower().strip()
    assets = [normalize(item) for item in load_assets()]
    for asset in assets:
        if asset["id"] == query or slugify(asset["name"]) == query:
            return asset
    matches = [asset for asset in assets if query in asset["id"].lower() or query in asset["name"].lower()]
    if len(matches) == 1:
        return matches[0]
    if matches:
        print("Multiple matches:")
        [print(f"- {item['id']} :: {item['name']}") for item in matches[:30]]
        raise SystemExit(2)
    raise SystemExit(f"No asset found for: {query}")


def field(key, label, kind="currency", default=10000):
    return {"key": key, "label": label, "type": kind, "default": default}


FIELDS = {
    "insurance": [
        field("annualPremium", "Annual Premium", "currency", 50000),
        field("requiredDepositPct", "Required Down Payment %", "percent", 25),
        field("cashAvailable", "Cash Available", "currency", 7500),
    ],
    "amazon": [
        field("heldPayout", "Payout Held", "currency", 25000),
        field("daysHeld", "Days Held", "number", 14),
        field("monthlyRoiPct", "Expected Monthly ROI %", "percent", 8),
    ],
    "tax": [
        field("taxBalance", "Tax Balance Due", "currency", 22000),
        field("cashAvailable", "Cash Available", "currency", 4000),
        field("daysUntilDeadline", "Days Until Deadline", "number", 10),
    ],
    "payroll": [
        field("weeklyPayroll", "Weekly Payroll", "currency", 35000),
        field("cashAvailable", "Cash Available", "currency", 12000),
        field("receivablesDue", "Receivables Due Within 30 Days", "currency", 50000),
    ],
    "trucking": [
        field("repairCost", "Repair Cost", "currency", 8500),
        field("dailyRevenue", "Daily Revenue When Running", "currency", 1200),
        field("downtimeDays", "Estimated Downtime Days", "number", 7),
    ],
    "commission": [
        field("targetIncome", "Target Income", "currency", 10000),
        field("avgCommission", "Average Commission", "currency", 750),
        field("closeRatePct", "Close Rate %", "percent", 20),
    ],
    "construction": [
        field("projectValue", "Project Value", "currency", 120000),
        field("materialCostPct", "Material Cost %", "percent", 35),
        field("cashAvailable", "Cash Available", "currency", 18000),
    ],
    "underwriting": [
        field("monthlyRevenue", "Monthly Revenue", "currency", 50000),
        field("creditScore", "Credit Score", "number", 620),
        field("cashAvailable", "Cash Available", "currency", 10000),
    ],
    "capital": [
        field("raiseAmount", "Target Raise", "currency", 1000000),
        field("monthlyBurn", "Monthly Burn", "currency", 65000),
        field("currentRunway", "Current Runway Months", "number", 6),
    ],
    "default": [
        field("monthlyRevenue", "Monthly Revenue", "currency", 50000),
        field("cashAvailable", "Available Cash", "currency", 10000),
        field("amountNeeded", "Amount Needed", "currency", 15000),
    ],
}


def domain(asset):
    text = f"{asset.get('name', '')} {asset.get('problem', '')} {asset.get('audience', '')}".lower()
    if any(item in text for item in ["premium", "insurance", "policy"]):
        return "insurance"
    if any(item in text for item in ["amazon", "seller", "ecommerce", "payout"]):
        return "amazon"
    if "tax" in text or "irs" in text:
        return "tax"
    if "payroll" in text or "staffing" in text:
        return "payroll"
    if any(item in text for item in ["truck", "freight", "repair"]):
        return "trucking"
    if any(item in text for item in ["commission", "referral", "partner", "agent"]):
        return "commission"
    if any(item in text for item in ["material", "construction", "contractor", "neca", "trade"]):
        return "construction"
    if any(item in text for item in ["bank", "credit", "score", "qualifier", "risk"]):
        return "underwriting"
    if any(item in text for item in ["deck", "investor", "data room", "capital raise", "runway"]):
        return "capital"
    return "default"


def formula(asset, domain_name):
    text = f"{asset.get('name', '')} {asset.get('problem', '')} {asset.get('assetType', '')}".lower()
    if "score" in text or "risk" in text or "qualifier" in text:
        return {"type": "score", "label": "Readiness Score", "expression": "weighted score from inputs", "resultLabel": "Score", "resultFormat": "score"}

    formulas = {
        "insurance": {"type": "gap", "label": "Premium Finance Gap", "expression": "annualPremium * requiredDepositPct / 100 - cashAvailable", "resultLabel": "Estimated Gap", "resultFormat": "currency"},
        "amazon": {"type": "opportunity_cost", "label": "Opportunity Cost", "expression": "heldPayout * monthlyRoiPct / 100 * daysHeld / 30", "resultLabel": "Missed Profit", "resultFormat": "currency"},
        "tax": {"type": "gap", "label": "Tax Cash Gap", "expression": "taxBalance - cashAvailable", "resultLabel": "Advance Need", "resultFormat": "currency"},
        "payroll": {"type": "gap", "label": "Payroll Bridge Need", "expression": "weeklyPayroll - cashAvailable", "resultLabel": "Bridge Amount", "resultFormat": "currency"},
        "trucking": {"type": "cost_of_delay", "label": "Repair-to-Revenue Impact", "expression": "repairCost + dailyRevenue * downtimeDays", "resultLabel": "Revenue at Risk", "resultFormat": "currency"},
        "commission": {"type": "commission_plan", "label": "Required Lead Volume", "expression": "targetIncome / avgCommission / (closeRatePct / 100)", "resultLabel": "Required Leads", "resultFormat": "number"},
        "construction": {"type": "gap", "label": "Material Financing Need", "expression": "projectValue * materialCostPct / 100 - cashAvailable", "resultLabel": "Material Gap", "resultFormat": "currency"},
        "underwriting": {"type": "score", "label": "Funding Readiness Score", "expression": "weighted score from monthlyRevenue, creditScore, cashAvailable", "resultLabel": "Readiness Score", "resultFormat": "score"},
        "capital": {"type": "runway", "label": "Runway Coverage", "expression": "raiseAmount / monthlyBurn + currentRunway", "resultLabel": "Projected Runway Months", "resultFormat": "number"},
        "default": {"type": "gap", "label": "Funding Gap", "expression": "amountNeeded - cashAvailable", "resultLabel": "Estimated Gap", "resultFormat": "currency"},
    }
    return formulas.get(domain_name, formulas["default"])


def outputs(formula_spec):
    return {
        "score": ["Qualification score", "Risk band", "Recommended next step"],
        "commission_plan": ["Required leads", "Deals needed", "Daily activity target"],
        "runway": ["Projected runway", "Funding coverage", "Scenario recommendation"],
        "cost_of_delay": ["Revenue at risk", "Repair funding need", "Payback urgency"],
        "opportunity_cost": ["Missed profit", "Working capital drag", "Action recommendation"],
    }.get(formula_spec["type"], [formula_spec["resultLabel"], "Qualification signal", "Recommended next step"])


def benefits(domain_name):
    return {
        "insurance": [
            "Show the exact premium deposit gap.",
            "Protect renewals before price shock kills the policy.",
            "Route qualified clients into financing options.",
        ],
        "amazon": [
            "Show the cost of trapped marketplace cash.",
            "Translate payout delays into missed reinvestment.",
            "Create urgency around working capital.",
        ],
        "commission": [
            "Turn income goals into activity targets.",
            "Expose the lead volume required to hit commission goals.",
            "Motivate partners with projection math.",
        ],
        "construction": [
            "Estimate material cash needs before the job starts.",
            "Identify the gap between project cost and cash on hand.",
            "Route contractors into funding conversations.",
        ],
    }.get(domain_name, [
        "Quantify the problem in plain language.",
        "Give the visitor an immediate result.",
        "Route high-intent leads into the next action.",
    ])


def spec_for(asset, brand=None):
    asset = normalize(asset)
    domain_name = domain(asset)
    formula_spec = formula(asset, domain_name)
    raw_fields = asset.get("inputs") or []
    fields = FIELDS[domain_name]
    if len(raw_fields) >= 2:
        fields = []
        for raw in raw_fields[:5]:
            label = str(raw).strip()
            kind = "currency" if any(word in label.lower() for word in ["cash", "amount", "revenue", "cost", "premium", "payroll", "commission", "funding"]) else "number"
            fields.append(field(slugify(label).replace("-", "_"), label.title(), kind, 10000))

    tier = int(asset.get("tier", 1))
    asset_type = normalize_asset_type(asset.get("assetType", "calculator"))
    modules = []
    if tier == 3 or asset_type in ["portal", "dashboard", "data-room"]:
        modules = [
            {"name": "Intake", "description": "Collect lead, partner, or client details."},
            {"name": "Status Board", "description": "Track progress from submitted to closed."},
            {"name": "Resource Vault", "description": "Centralize documents, links, scripts, and next steps."},
            {"name": "Reporting", "description": "Show pipeline, activity, and conversion metrics."},
        ]

    return {
        "schemaVersion": "0.3",
        "id": asset["id"],
        "title": asset.get("name"),
        "brand": brand or asset.get("brand") or "FoundryOS",
        "audience": asset.get("audience"),
        "industry": asset.get("industry", domain_name),
        "tier": tier,
        "assetType": asset_type,
        "domain": domain_name,
        "problem": clean(asset.get("problem")),
        "promise": f"Turn {clean(asset.get('problem')).lower()} into a clear next step.",
        "primaryAction": asset.get("primaryAction") or "Get My Result",
        "fields": fields,
        "formula": formula_spec,
        "outputs": asset.get("outputs") or outputs(formula_spec),
        "benefits": benefits(domain_name),
        "leadCapture": {
            "enabled": True,
            "fields": ["name", "email", "phone", "company"],
            "routingNote": "Replace demo handler with CRM/form/webhook.",
        },
        "modules": modules,
        "deployment": {"type": "static", "entry": "index.html"},
        "sourceAsset": asset,
    }


def write_spec(asset, brand=None, force=False):
    spec = spec_for(asset, brand)
    SPECS.mkdir(exist_ok=True)
    path = SPECS / f"{spec['id']}.json"
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return spec


def safe_target(base, asset_id, force=False, flat=False):
    base = Path(base)
    target = base if flat else base / asset_id
    if target.exists():
        if force:
            shutil.rmtree(target)
        else:
            index = 2
            while Path(str(target) + f"-{index}").exists():
                index += 1
            target = Path(str(target) + f"-{index}")
    target.mkdir(parents=True, exist_ok=True)
    return target


def builder_for(asset_type):
    builders = {
        "calculator": calculator_builder,
        "scorecard": scorecard_builder,
        "simulator": simulator_builder,
        "dashboard": dashboard_builder,
        "portal": portal_builder,
        "landing_page": landing_page_builder,
    }
    normalized = normalize_asset_type(asset_type)
    builder = builders.get(normalized)
    if builder is None:
        print(f"Unknown assetType '{asset_type}', using calculator builder.")
        return calculator_builder
    return builder


def build(asset, brand=None, outdir=None, force=False, flat=False, spec_force=False):
    asset = normalize(asset)
    spec = write_spec(asset, brand, spec_force)
    target = safe_target(Path(outdir) if outdir else OUTPUTS, asset["id"], force, flat)
    builder = builder_for(spec.get("assetType"))
    builder.build(asset, spec, brand, target)
    print(f"Built: {target}")


def list_assets(limit=25, tier=None, atype=None):
    assets = [normalize(item) for item in load_assets()]
    if tier:
        assets = [asset for asset in assets if int(asset.get("tier", 0)) == int(tier)]
    if atype:
        atype = normalize_asset_type(atype)
        assets = [asset for asset in assets if normalize_asset_type(asset.get("assetType")) == atype]
    for asset in assets[:limit]:
        print(f"{asset['id']} | T{asset['tier']} | {asset['assetType']} | {asset['name']}")
    print(f"\nShowing {min(limit, len(assets))} of {len(assets)}")


def infer_type(text, tier):
    text = text.lower()
    if any(word in text for word in ["portal", "dashboard", "data room", "partner"]):
        return "portal"
    if any(word in text for word in ["simulate", "simulator", "scenario", "forecast", "predictor", "generator"]):
        return "simulator"
    if any(word in text for word in ["score", "risk", "qualifier", "assessment"]):
        return "scorecard"
    if any(word in text for word in ["landing", "sales page", "waitlist"]):
        return "landing_page"
    return "portal" if tier == 3 else "simulator" if tier == 2 else "calculator"


def create(args):
    asset = {
        "id": slugify(args.name or args.idea),
        "name": args.name or args.idea.title(),
        "brand": args.brand or "",
        "industry": args.industry or "general",
        "audience": args.audience or "Business owners",
        "problem": args.problem or args.idea,
        "tier": args.tier,
        "assetType": normalize_asset_type(args.asset_type or infer_type(args.idea, args.tier)),
        "inputs": [item.strip() for item in args.inputs.split(",")] if args.inputs else [],
        "outputs": [item.strip() for item in args.outputs.split(",")] if args.outputs else [],
        "primaryAction": args.cta or "Get My Result",
        "source": "created",
    }
    if args.save:
        assets = load_assets()
        if not any(item["id"] == asset["id"] for item in assets):
            assets.append(asset)
            save_assets(assets)
            print(f"Saved: {asset['id']}")
    if args.spec:
        print(json.dumps(write_spec(asset, args.brand, True), indent=2))
    if args.build:
        build(asset, args.brand, args.outdir, args.force, args.flat, True)
    if not args.spec and not args.build:
        print(json.dumps(asset, indent=2))


def main():
    parser = argparse.ArgumentParser(description="FoundryOS V3: registry -> asset spec -> deployable files.")
    sub = parser.add_subparsers(dest="command", required=True)

    parser_list = sub.add_parser("list")
    parser_list.add_argument("--limit", type=int, default=25)
    parser_list.add_argument("--tier", type=int)
    parser_list.add_argument("--type")

    parser_spec = sub.add_parser("spec")
    parser_spec.add_argument("query")
    parser_spec.add_argument("--brand")
    parser_spec.add_argument("--force", action="store_true")
    parser_spec.add_argument("--print", action="store_true")

    parser_spec_all = sub.add_parser("spec-all")
    parser_spec_all.add_argument("--brand")
    parser_spec_all.add_argument("--tier", type=int)
    parser_spec_all.add_argument("--limit", type=int)
    parser_spec_all.add_argument("--force", action="store_true")

    parser_build = sub.add_parser("build")
    parser_build.add_argument("query")
    parser_build.add_argument("--brand")
    parser_build.add_argument("--outdir")
    parser_build.add_argument("--force", action="store_true")
    parser_build.add_argument("--flat", action="store_true")
    parser_build.add_argument("--spec-force", action="store_true")

    parser_build_all = sub.add_parser("build-all")
    parser_build_all.add_argument("--brand")
    parser_build_all.add_argument("--outdir")
    parser_build_all.add_argument("--tier", type=int)
    parser_build_all.add_argument("--limit", type=int)
    parser_build_all.add_argument("--force", action="store_true")
    parser_build_all.add_argument("--spec-force", action="store_true")

    parser_create = sub.add_parser("create")
    parser_create.add_argument("idea")
    parser_create.add_argument("--name")
    parser_create.add_argument("--audience")
    parser_create.add_argument("--problem")
    parser_create.add_argument("--tier", type=int, choices=[1, 2, 3], default=1)
    parser_create.add_argument("--asset-type")
    parser_create.add_argument("--inputs")
    parser_create.add_argument("--outputs")
    parser_create.add_argument("--cta")
    parser_create.add_argument("--brand")
    parser_create.add_argument("--industry")
    parser_create.add_argument("--save", action="store_true")
    parser_create.add_argument("--build", action="store_true")
    parser_create.add_argument("--spec", action="store_true")
    parser_create.add_argument("--outdir")
    parser_create.add_argument("--force", action="store_true")
    parser_create.add_argument("--flat", action="store_true")

    args = parser.parse_args()

    if args.command == "list":
        list_assets(args.limit, args.tier, args.type)
    elif args.command == "spec":
        spec = write_spec(find_asset(args.query), args.brand, args.force)
        print(json.dumps(spec, indent=2) if args.print else f"Spec: {SPECS / (spec['id'] + '.json')}")
    elif args.command == "spec-all":
        assets = [normalize(item) for item in load_assets()]
        if args.tier:
            assets = [asset for asset in assets if int(asset.get("tier", 0)) == int(args.tier)]
        if args.limit:
            assets = assets[:args.limit]
        for asset in assets:
            print(f"Spec: {SPECS / (write_spec(asset, args.brand, args.force)['id'] + '.json')}")
        print(f"\nGenerated {len(assets)} specs.")
    elif args.command == "build":
        build(find_asset(args.query), args.brand, args.outdir, args.force, args.flat, args.spec_force)
    elif args.command == "build-all":
        assets = [normalize(item) for item in load_assets()]
        if args.tier:
            assets = [asset for asset in assets if int(asset.get("tier", 0)) == int(args.tier)]
        if args.limit:
            assets = assets[:args.limit]
        for asset in assets:
            build(asset, args.brand, args.outdir or OUTPUTS, args.force, False, args.spec_force)
        print(f"\nBuilt {len(assets)} assets.")
    elif args.command == "create":
        create(args)


if __name__ == "__main__":
    main()

