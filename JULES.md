# JULES.md — FoundryOS Engine Layer Task

## Repository

`foundryos`

## Prime Directive

Work only inside the existing `foundryos` repository.

Do **not** create:
- a new repo
- a duplicate project folder
- a versioned folder
- a ZIP file
- a replacement scaffold

FoundryOS is a single evolving repo. All work should be committed as changes inside the existing project.

---

## Current State

The repo currently has:

- `scripts/foundry.py`
- `builders/` modules
- builder routing by asset type
- registry files
- templates
- ignored generated outputs
- ignored generated specs

Existing CLI commands must continue working.

---

## Goal

Build the next FoundryOS engine layer so assets are generated through this pipeline:

```text
registry item
→ logic profile
→ copy profile
→ design system
→ lead flow
→ builder
→ output folder
```

The goal is to move FoundryOS from basic static generation into reusable internal asset production.

---

## Create These Files

### Engine Layer

```text
engines/
├─ __init__.py
├─ design_engine.py
├─ copy_engine.py
├─ lead_flow_engine.py
├─ registry_importer.py
└─ logic_engine.py
```

### Logic Library

```text
logic-library/
├─ logic.schema.json
├─ funding/
│  ├─ cash-flow-gap.json
│  ├─ payroll-bridge.json
│  ├─ tax-advance.json
│  ├─ mca-repayment.json
│  ├─ equipment-finance.json
│  └─ invoice-factoring.json
├─ insurance/
│  ├─ premium-finance-gap.json
│  ├─ renewal-risk-score.json
│  └─ coverage-gap.json
├─ ecommerce/
│  ├─ amazon-payout-delay.json
│  ├─ inventory-cash-gap.json
│  └─ ad-cost-inflation.json
└─ real-estate/
   ├─ proof-of-funds.json
   ├─ bridge-loan.json
   └─ investor-roi.json
```

### Design Systems

```text
design-systems/
└─ moonshine-capital.json
```

### Registry Imports

```text
registry/imports/
└─ README.md
```

### Tests

```text
tests/
└─ smoke_test.py
```

---

## Requirements

1. Preserve all existing CLI commands in `scripts/foundry.py`.

2. Add optional CLI flags:

```bash
--design moonshine-capital
--logic auto
```

3. `logic_engine.py` should:
   - load JSON profiles from `logic-library/`
   - match profiles by title, domain, audience, problem, asset type, and keywords
   - return a safe default logic profile when no match is found

4. `design_engine.py` should:
   - load design systems from `design-systems/*.json`
   - return a default design system if the requested one is missing
   - expose a function builders can consume cleanly

5. `copy_engine.py` should generate structured copy:

```json
{
  "heroEyebrow": "",
  "heroTitle": "",
  "heroSubtitle": "",
  "formTitle": "",
  "resultTitle": "",
  "benefitBullets": [],
  "faq": [],
  "primaryCta": ""
}
```

6. `lead_flow_engine.py` should generate `lead-flow.json`:

```json
{
  "primaryAction": "",
  "leadFields": [],
  "routingTags": [],
  "qualificationRules": [],
  "followUpSequence": []
}
```

7. `registry_importer.py` should:
   - read CSV files from `registry/imports/`
   - normalize them into the same schema used by `registry/normalized/assets.json`
   - support common column variations such as:
     - `name`, `title`, `tool`, `idea`
     - `audience`, `market`, `persona`
     - `problem`, `pain`, `use_case`
     - `assetType`, `type`, `format`
     - `tier`, `complexity`
     - `cta`, `primaryAction`
   - preserve existing assets unless explicitly overwritten

8. Every generated output folder must include:

```text
index.html
styles.css
app.js
asset.json
asset-spec.json
lead-flow.json
README.md
```

9. Update all builders to consume:
   - design data
   - copy data
   - logic data
   - lead flow data

10. Keep the project pure Python with no external dependencies.

11. Add `tests/smoke_test.py` to verify:
   - registry loads
   - logic profiles load
   - design system loads
   - calculator builds
   - scorecard builds
   - simulator builds
   - output includes `lead-flow.json`

12. Run validation commands:

```bash
python -m py_compile scripts/foundry.py builders/*.py engines/*.py
python tests/smoke_test.py
```

---

## Design System Expectations

`design-systems/moonshine-capital.json` should define:

```json
{
  "id": "moonshine-capital",
  "brandName": "Moonshine Capital",
  "theme": "finance-dark",
  "tone": "premium, direct, capital-market fluent",
  "font": {
    "sans": "Inter, system-ui, sans-serif",
    "display": "Inter, system-ui, sans-serif"
  },
  "colors": {
    "background": "#080A0F",
    "surface": "#111827",
    "surfaceAlt": "#172033",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "accent": "#D4AF37",
    "accentAlt": "#38BDF8",
    "border": "rgba(255,255,255,0.12)"
  },
  "radius": {
    "sm": "12px",
    "md": "18px",
    "lg": "28px"
  },
  "layout": {
    "maxWidth": "1120px",
    "hero": "split",
    "tool": "card",
    "proof": "bullet-grid"
  }
}
```

---

## Logic Profile Expectations

Each logic profile should follow `logic-library/logic.schema.json`.

Minimum useful structure:

```json
{
  "id": "premium-finance-gap",
  "domain": "insurance",
  "assetTypes": ["calculator", "scorecard", "simulator"],
  "keywords": ["premium", "finance", "deposit", "insurance", "gap"],
  "title": "Premium Finance Gap",
  "description": "Calculates the cash gap between required insurance premium deposits and available cash.",
  "inputs": [
    {
      "key": "annualPremium",
      "label": "Annual Premium",
      "type": "currency",
      "default": 50000
    }
  ],
  "outputs": [
    {
      "key": "estimatedGap",
      "label": "Estimated Gap",
      "format": "currency"
    }
  ],
  "formula": {
    "type": "expression",
    "expression": "annualPremium * requiredDepositPct / 100 - cashAvailable"
  },
  "qualificationRules": [],
  "recommendedCta": "Request Financing Options"
}
```

---

## CLI Behavior

Existing examples should still work:

```bash
python scripts/foundry.py list
python scripts/foundry.py build the-premium-finance-gap-calculator --brand "Moonshine Capital"
python scripts/foundry.py build-all --brand "Moonshine Capital" --limit 10
```

New examples should work:

```bash
python scripts/foundry.py build the-premium-finance-gap-calculator --brand "Moonshine Capital" --design moonshine-capital --logic auto
python scripts/foundry.py build-all --brand "Moonshine Capital" --design moonshine-capital --logic auto --limit 10
python scripts/foundry.py import-registry
```

If `import-registry` is added, document it in `README.md`.

---

## Output Quality Bar

Generated assets should feel meaningfully different by type:

- calculator: focused input/result tool
- scorecard: weighted readiness or risk assessment
- simulator: scenario-driven tool
- dashboard: metric/card/reporting layout
- portal: multi-section resource/workflow hub
- landing page: conversion page with CTA flow

Generated pages should use the selected design system rather than hardcoded generic styles.

---

## Do Not

- Do not remove existing registry data.
- Do not break existing CLI commands.
- Do not commit generated `outputs/` folders.
- Do not commit local `.env` files.
- Do not add external dependencies.
- Do not rename the repo.
- Do not create versioned folders.
