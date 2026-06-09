# FoundryOS V3

FoundryOS now runs as:

Registry → Asset Spec → Builder → Deployable Files

## Commands

List registry:

```powershell
python .\scripts\foundry.py list
```

Generate one asset spec:

```powershell
python .\scripts\foundry.py spec the-premium-finance-gap-calculator --brand "Moonshine Capital" --print
```

Build one asset:

```powershell
python .\scripts\foundry.py build the-premium-finance-gap-calculator --brand "Moonshine Capital" --spec-force
```

Build all Tier 1:

```powershell
python .\scripts\foundry.py build-all --brand "Moonshine Capital" --tier 1 --spec-force
```

Build Tier 2:

```powershell
python .\scripts\foundry.py build-all --brand "Moonshine Capital" --tier 2 --spec-force
```

Build Tier 3:

```powershell
python .\scripts\foundry.py build-all --brand "Moonshine Capital" --tier 3 --spec-force
```

Create a new idea:

```powershell
python .\scripts\foundry.py create "material financing calculator for roofing contractors" --brand "Moonshine Capital" --audience "Roofing contractors" --tier 1 --build --save
```

## What changed in V3

- Adds `/specs`
- Generates `asset-spec.json`
- Uses asset-specific fields instead of the same generic inputs
- Routes Tier 1 to calculators/widgets/landing pages
- Routes Tier 2 to simulators/generators
- Routes Tier 3 to portals/dashboards/data rooms
- Every generated folder includes:
  - `index.html`
  - `styles.css`
  - `app.js` where applicable
  - `asset.json`
  - `asset-spec.json`
  - `README.md`

## Notes

This is still a static-file generator. It does not deploy by itself yet.
Deployment engine is the next layer: GitHub/Vercel/Cloudflare push.
