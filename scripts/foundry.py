
#!/usr/bin/env python3
import argparse, json, re, shutil
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"registry"/"normalized"/"assets.json"
OUTPUTS=ROOT/"outputs"
SPECS=ROOT/"specs"

def slugify(v):
    v=str(v or "").lower()
    v=re.sub(r'["“”()]+','',v)
    return re.sub(r"[^a-z0-9]+","-",v).strip("-") or "untitled"

def clean(v):
    v=re.sub(r"\s+"," ",str(v or "")).strip()
    v=re.sub(r"\s*\d+(?:,\s*\d+)*\s*$","",v).strip()
    return v or "A business decision needs to be made faster and with less guesswork."

def load_assets(): return json.loads(REGISTRY.read_text(encoding="utf-8"))
def save_assets(a): REGISTRY.write_text(json.dumps(a,indent=2),encoding="utf-8")

def normalize(a):
    a=dict(a)
    a.setdefault("id",slugify(a.get("name","asset")))
    a.setdefault("audience","Business owners")
    a.setdefault("problem","Turn a painful business decision into a useful interactive asset.")
    a.setdefault("coreLogic","Collect relevant inputs, calculate a useful result, and route the user to the next action.")
    a.setdefault("tier",1); a.setdefault("assetType","calculator")
    a.setdefault("primaryAction","Get My Result")
    return a

def find_asset(q):
    q=q.lower().strip()
    assets=[normalize(x) for x in load_assets()]
    for a in assets:
        if a["id"]==q or slugify(a["name"])==q: return a
    m=[a for a in assets if q in a["id"].lower() or q in a["name"].lower()]
    if len(m)==1: return m[0]
    if m:
        print("Multiple matches:")
        [print(f"- {x['id']} :: {x['name']}") for x in m[:30]]
        raise SystemExit(2)
    raise SystemExit(f"No asset found for: {q}")

def field(key,label,kind="currency",default=10000):
    return {"key":key,"label":label,"type":kind,"default":default}

FIELDS={
"insurance":[field("annualPremium","Annual Premium","currency",50000),field("requiredDepositPct","Required Down Payment %","percent",25),field("cashAvailable","Cash Available","currency",7500)],
"amazon":[field("heldPayout","Payout Held","currency",25000),field("daysHeld","Days Held","number",14),field("monthlyRoiPct","Expected Monthly ROI %","percent",8)],
"tax":[field("taxBalance","Tax Balance Due","currency",22000),field("cashAvailable","Cash Available","currency",4000),field("daysUntilDeadline","Days Until Deadline","number",10)],
"payroll":[field("weeklyPayroll","Weekly Payroll","currency",35000),field("cashAvailable","Cash Available","currency",12000),field("receivablesDue","Receivables Due Within 30 Days","currency",50000)],
"trucking":[field("repairCost","Repair Cost","currency",8500),field("dailyRevenue","Daily Revenue When Running","currency",1200),field("downtimeDays","Estimated Downtime Days","number",7)],
"commission":[field("targetIncome","Target Income","currency",10000),field("avgCommission","Average Commission","currency",750),field("closeRatePct","Close Rate %","percent",20)],
"construction":[field("projectValue","Project Value","currency",120000),field("materialCostPct","Material Cost %","percent",35),field("cashAvailable","Cash Available","currency",18000)],
"underwriting":[field("monthlyRevenue","Monthly Revenue","currency",50000),field("creditScore","Credit Score","number",620),field("cashAvailable","Cash Available","currency",10000)],
"capital":[field("raiseAmount","Target Raise","currency",1000000),field("monthlyBurn","Monthly Burn","currency",65000),field("currentRunway","Current Runway Months","number",6)],
"default":[field("monthlyRevenue","Monthly Revenue","currency",50000),field("cashAvailable","Available Cash","currency",10000),field("amountNeeded","Amount Needed","currency",15000)]
}

def domain(a):
    t=f"{a.get('name','')} {a.get('problem','')} {a.get('audience','')}".lower()
    if any(x in t for x in ["premium","insurance","policy"]): return "insurance"
    if any(x in t for x in ["amazon","seller","ecommerce","payout"]): return "amazon"
    if "tax" in t or "irs" in t: return "tax"
    if "payroll" in t or "staffing" in t: return "payroll"
    if any(x in t for x in ["truck","freight","repair"]): return "trucking"
    if any(x in t for x in ["commission","referral","partner","agent"]): return "commission"
    if any(x in t for x in ["material","construction","contractor","neca","trade"]): return "construction"
    if any(x in t for x in ["bank","credit","score","qualifier","risk"]): return "underwriting"
    if any(x in t for x in ["deck","investor","data room","capital raise","runway"]): return "capital"
    return "default"

def formula(a,d):
    t=f"{a.get('name','')} {a.get('problem','')} {a.get('assetType','')}".lower()
    if "score" in t or "risk" in t or "qualifier" in t:
        return {"type":"score","label":"Readiness Score","expression":"weighted score from inputs","resultLabel":"Score","resultFormat":"score"}
    return {
      "insurance":{"type":"gap","label":"Premium Finance Gap","expression":"annualPremium * requiredDepositPct / 100 - cashAvailable","resultLabel":"Estimated Gap","resultFormat":"currency"},
      "amazon":{"type":"opportunity_cost","label":"Opportunity Cost","expression":"heldPayout * monthlyRoiPct / 100 * daysHeld / 30","resultLabel":"Missed Profit","resultFormat":"currency"},
      "tax":{"type":"gap","label":"Tax Cash Gap","expression":"taxBalance - cashAvailable","resultLabel":"Advance Need","resultFormat":"currency"},
      "payroll":{"type":"gap","label":"Payroll Bridge Need","expression":"weeklyPayroll - cashAvailable","resultLabel":"Bridge Amount","resultFormat":"currency"},
      "trucking":{"type":"cost_of_delay","label":"Repair-to-Revenue Impact","expression":"repairCost + dailyRevenue * downtimeDays","resultLabel":"Revenue at Risk","resultFormat":"currency"},
      "commission":{"type":"commission_plan","label":"Required Lead Volume","expression":"targetIncome / avgCommission / (closeRatePct / 100)","resultLabel":"Required Leads","resultFormat":"number"},
      "construction":{"type":"gap","label":"Material Financing Need","expression":"projectValue * materialCostPct / 100 - cashAvailable","resultLabel":"Material Gap","resultFormat":"currency"},
      "capital":{"type":"runway","label":"Runway Coverage","expression":"raiseAmount / monthlyBurn + currentRunway","resultLabel":"Projected Runway Months","resultFormat":"number"},
      "default":{"type":"gap","label":"Funding Gap","expression":"amountNeeded - cashAvailable","resultLabel":"Estimated Gap","resultFormat":"currency"}
    }[d]

def outputs(f):
    return {
      "score":["Qualification score","Risk band","Recommended next step"],
      "commission_plan":["Required leads","Deals needed","Daily activity target"],
      "runway":["Projected runway","Funding coverage","Scenario recommendation"],
      "cost_of_delay":["Revenue at risk","Repair funding need","Payback urgency"],
      "opportunity_cost":["Missed profit","Working capital drag","Action recommendation"]
    }.get(f["type"],[f["resultLabel"],"Qualification signal","Recommended next step"])

def benefits(d):
    return {
      "insurance":["Show the exact premium deposit gap.","Protect renewals before price shock kills the policy.","Route qualified clients into financing options."],
      "amazon":["Show the cost of trapped marketplace cash.","Translate payout delays into missed reinvestment.","Create urgency around working capital."],
      "commission":["Turn income goals into activity targets.","Expose the lead volume required to hit commission goals.","Motivate partners with projection math."],
      "construction":["Estimate material cash needs before the job starts.","Identify the gap between project cost and cash on hand.","Route contractors into funding conversations."]
    }.get(d,["Quantify the problem in plain language.","Give the visitor an immediate result.","Route high-intent leads into the next action."])

def spec_for(a,brand=None):
    a=normalize(a); d=domain(a); f=formula(a,d)
    raw=a.get("inputs") or []
    fields=FIELDS[d]
    if len(raw)>=2:
        fields=[]
        for r in raw[:5]:
            label=str(r).strip()
            kind="currency" if any(w in label.lower() for w in ["cash","amount","revenue","cost","premium","payroll","commission","funding"]) else "number"
            fields.append(field(slugify(label).replace("-","_"),label.title(),kind,10000))
    tier=int(a.get("tier",1)); at=a.get("assetType","calculator")
    modules=[]
    if tier==3 or at in ["portal","dashboard","data-room"]:
        modules=[{"name":"Intake","description":"Collect lead, partner, or client details."},{"name":"Status Board","description":"Track progress from submitted to closed."},{"name":"Resource Vault","description":"Centralize documents, links, scripts, and next steps."},{"name":"Reporting","description":"Show pipeline, activity, and conversion metrics."}]
    return {
      "schemaVersion":"0.3","id":a["id"],"title":a.get("name"),"brand":brand or a.get("brand") or "FoundryOS",
      "audience":a.get("audience"),"industry":a.get("industry",d),"tier":tier,"assetType":at,"domain":d,
      "problem":clean(a.get("problem")),"promise":f"Turn {clean(a.get('problem')).lower()} into a clear next step.",
      "primaryAction":a.get("primaryAction") or "Get My Result","fields":fields,"formula":f,"outputs":a.get("outputs") or outputs(f),
      "benefits":benefits(d),"leadCapture":{"enabled":True,"fields":["name","email","phone","company"],"routingNote":"Replace demo handler with CRM/form/webhook."},
      "modules":modules,"deployment":{"type":"static","entry":"index.html"},"sourceAsset":a
    }

def write_spec(a,brand=None,force=False):
    s=spec_for(a,brand); SPECS.mkdir(exist_ok=True)
    p=SPECS/f"{s['id']}.json"
    if p.exists() and not force: return json.loads(p.read_text(encoding="utf-8"))
    p.write_text(json.dumps(s,indent=2),encoding="utf-8"); return s

def template_for(s):
    at=s["assetType"]; tier=int(s["tier"])
    if tier==3 or at in ["portal","dashboard","data-room"]: return "portal"
    if tier==2 or at in ["simulator","generator"]: return "simulator"
    if at in ["landing","landing-page"]: return "landing-page"
    if at=="widget": return "widget"
    return "static-calculator"

def render(txt,a,brand=None,s=None):
    s=s or spec_for(a,brand)
    vals={"ASSET_NAME":s["title"],"BRAND_NAME":s["brand"],"AUDIENCE":s["audience"],"PROBLEM":s["problem"],"PROMISE":s["promise"],"CTA":s["primaryAction"],"ASSET_ID":s["id"],"ASSET_TYPE":s["assetType"],"TIER":str(s["tier"]),"SPEC_JSON":json.dumps(s),"FIELDS_JSON":json.dumps(s["fields"]),"FORMULA_JSON":json.dumps(s["formula"]),"OUTPUTS":", ".join(s["outputs"]),"BENEFITS_HTML":"".join(f"<li>{b}</li>" for b in s["benefits"]),"MODULES_HTML":"".join(f"<div class='module'><b>{m['name']}</b><span>{m['description']}</span></div>" for m in s["modules"]),"YEAR":datetime.now().strftime("%Y")}
    for k,v in vals.items(): txt=txt.replace("{{"+k+"}}",str(v))
    return txt

def safe_target(base,aid,force=False,flat=False):
    base=Path(base); target=base if flat else base/aid
    if target.exists():
        if force: shutil.rmtree(target)
        else:
            i=2
            while Path(str(target)+f"-{i}").exists(): i+=1
            target=Path(str(target)+f"-{i}")
    target.mkdir(parents=True,exist_ok=True); return target

def build(a,brand=None,outdir=None,force=False,flat=False,spec_force=False):
    a=normalize(a); s=write_spec(a,brand,spec_force)
    tdir=ROOT/"templates"/template_for(s)
    target=safe_target(Path(outdir) if outdir else OUTPUTS,a["id"],force,flat)
    for src in tdir.rglob("*"):
        rel=src.relative_to(tdir); dest=target/rel
        if src.is_dir(): dest.mkdir(parents=True,exist_ok=True); continue
        dest.write_text(render(src.read_text(encoding="utf-8"),a,brand,s),encoding="utf-8")
    (target/"asset.json").write_text(json.dumps(a,indent=2),encoding="utf-8")
    (target/"asset-spec.json").write_text(json.dumps(s,indent=2),encoding="utf-8")
    (target/"README.md").write_text(f"# {s['title']}\n\nGenerated by FoundryOS V3.\n\nOpen `index.html`.\n\nDriven by `asset-spec.json`.\n",encoding="utf-8")
    print(f"Built: {target}")

def list_assets(limit=25,tier=None,atype=None):
    assets=[normalize(x) for x in load_assets()]
    if tier: assets=[a for a in assets if int(a.get("tier",0))==int(tier)]
    if atype: assets=[a for a in assets if a.get("assetType")==atype]
    for a in assets[:limit]: print(f"{a['id']} | T{a['tier']} | {a['assetType']} | {a['name']}")
    print(f"\nShowing {min(limit,len(assets))} of {len(assets)}")

def infer_type(text,tier):
    t=text.lower()
    if any(w in t for w in ["portal","dashboard","data room","partner"]): return "portal"
    if any(w in t for w in ["simulate","simulator","scenario","forecast","predictor","generator"]): return "generator" if "generator" in t else "simulator"
    if any(w in t for w in ["score","risk","qualifier","assessment"]): return "scorecard"
    if any(w in t for w in ["landing","sales page","waitlist"]): return "landing-page"
    if "widget" in t or "embed" in t: return "widget"
    return "portal" if tier==3 else "simulator" if tier==2 else "calculator"

def create(args):
    a={"id":slugify(args.name or args.idea),"name":args.name or args.idea.title(),"brand":args.brand or "","industry":args.industry or "general","audience":args.audience or "Business owners","problem":args.problem or args.idea,"tier":args.tier,"assetType":args.asset_type or infer_type(args.idea,args.tier),"inputs":[x.strip() for x in args.inputs.split(",")] if args.inputs else [],"outputs":[x.strip() for x in args.outputs.split(",")] if args.outputs else [],"primaryAction":args.cta or "Get My Result","source":"created"}
    if args.save:
        assets=load_assets()
        if not any(x["id"]==a["id"] for x in assets): assets.append(a); save_assets(assets); print(f"Saved: {a['id']}")
    if args.spec: print(json.dumps(write_spec(a,args.brand,True),indent=2))
    if args.build: build(a,args.brand,args.outdir,args.force,args.flat,True)
    if not args.spec and not args.build: print(json.dumps(a,indent=2))

def main():
    ap=argparse.ArgumentParser(description="FoundryOS V3: registry -> asset spec -> deployable files.")
    sub=ap.add_subparsers(dest="command",required=True)
    p=sub.add_parser("list"); p.add_argument("--limit",type=int,default=25); p.add_argument("--tier",type=int); p.add_argument("--type")
    p=sub.add_parser("spec"); p.add_argument("query"); p.add_argument("--brand"); p.add_argument("--force",action="store_true"); p.add_argument("--print",action="store_true")
    p=sub.add_parser("spec-all"); p.add_argument("--brand"); p.add_argument("--tier",type=int); p.add_argument("--limit",type=int); p.add_argument("--force",action="store_true")
    p=sub.add_parser("build"); p.add_argument("query"); p.add_argument("--brand"); p.add_argument("--outdir"); p.add_argument("--force",action="store_true"); p.add_argument("--flat",action="store_true"); p.add_argument("--spec-force",action="store_true")
    p=sub.add_parser("build-all"); p.add_argument("--brand"); p.add_argument("--outdir"); p.add_argument("--tier",type=int); p.add_argument("--limit",type=int); p.add_argument("--force",action="store_true"); p.add_argument("--spec-force",action="store_true")
    p=sub.add_parser("create"); p.add_argument("idea"); p.add_argument("--name"); p.add_argument("--audience"); p.add_argument("--problem"); p.add_argument("--tier",type=int,choices=[1,2,3],default=1); p.add_argument("--asset-type"); p.add_argument("--inputs"); p.add_argument("--outputs"); p.add_argument("--cta"); p.add_argument("--brand"); p.add_argument("--industry"); p.add_argument("--save",action="store_true"); p.add_argument("--build",action="store_true"); p.add_argument("--spec",action="store_true"); p.add_argument("--outdir"); p.add_argument("--force",action="store_true"); p.add_argument("--flat",action="store_true")
    args=ap.parse_args()
    if args.command=="list": list_assets(args.limit,args.tier,args.type)
    elif args.command=="spec":
        s=write_spec(find_asset(args.query),args.brand,args.force)
        print(json.dumps(s,indent=2) if args.print else f"Spec: {SPECS/(s['id']+'.json')}")
    elif args.command=="spec-all":
        assets=[normalize(x) for x in load_assets()]
        if args.tier: assets=[a for a in assets if int(a.get("tier",0))==int(args.tier)]
        if args.limit: assets=assets[:args.limit]
        for a in assets: print(f"Spec: {SPECS/(write_spec(a,args.brand,args.force)['id']+'.json')}")
        print(f"\nGenerated {len(assets)} specs.")
    elif args.command=="build": build(find_asset(args.query),args.brand,args.outdir,args.force,args.flat,args.spec_force)
    elif args.command=="build-all":
        assets=[normalize(x) for x in load_assets()]
        if args.tier: assets=[a for a in assets if int(a.get("tier",0))==int(args.tier)]
        if args.limit: assets=assets[:args.limit]
        for a in assets: build(a,args.brand,args.outdir or OUTPUTS,args.force,False,args.spec_force)
        print(f"\nBuilt {len(assets)} assets.")
    elif args.command=="create": create(args)

if __name__=="__main__": main()
