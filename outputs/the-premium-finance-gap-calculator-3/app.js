const spec = window.FOUNDRY_SPEC;
const form = document.getElementById("toolForm");
const fmtCurrency = n => new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0}).format(isFinite(n)?n:0);
const fmtNumber = n => new Intl.NumberFormat("en-US",{maximumFractionDigits:1}).format(isFinite(n)?n:0);
function addFields(){
  form.innerHTML = "";
  spec.fields.forEach(f=>{
    const label=document.createElement("label");
    label.textContent=f.label;
    const input=document.createElement("input");
    input.type="number"; input.id=f.key; input.value=f.default ?? 0;
    input.dataset.type=f.type || "number";
    form.appendChild(label); form.appendChild(input);
  });
}
function values(){
  const v={};
  spec.fields.forEach(f=>v[f.key]=Number(document.getElementById(f.key).value||0));
  return v;
}
function calc(){
  const v=values(); let r=0; const type=spec.formula.type;
  if(type==="gap"){
    if(v.annualPremium!==undefined) r=v.annualPremium*(v.requiredDepositPct||0)/100-(v.cashAvailable||0);
    else if(v.projectValue!==undefined) r=v.projectValue*(v.materialCostPct||0)/100-(v.cashAvailable||0);
    else if(v.taxBalance!==undefined) r=v.taxBalance-(v.cashAvailable||0);
    else if(v.weeklyPayroll!==undefined) r=v.weeklyPayroll-(v.cashAvailable||0);
    else r=(v.amountNeeded||0)-(v.cashAvailable||0);
  } else if(type==="opportunity_cost") r=(v.heldPayout||0)*(v.monthlyRoiPct||0)/100*(v.daysHeld||0)/30;
  else if(type==="cost_of_delay") r=(v.repairCost||0)+(v.dailyRevenue||0)*(v.downtimeDays||0);
  else if(type==="commission_plan") r=(v.targetIncome||0)/Math.max(1,(v.avgCommission||1))/Math.max(.01,(v.closeRatePct||1)/100);
  else if(type==="runway") r=(v.raiseAmount||0)/Math.max(1,(v.monthlyBurn||1))+(v.currentRunway||0);
  else if(type==="score"){
    const rev=v.monthlyRevenue||0, credit=v.creditScore||600, cash=v.cashAvailable||0;
    r=Math.max(0,Math.min(100,Math.round((rev/1000)*.45 + ((credit-500)/3) + (cash/1000)*.8)));
  }
  r=Math.max(0,r);
  const isMoney = spec.formula.resultFormat==="currency";
  document.getElementById("result").textContent = spec.formula.resultFormat==="score" ? `${Math.round(r)}/100` : isMoney ? fmtCurrency(r) : fmtNumber(r);
  const signal = r>50000 || (spec.formula.resultFormat==="score" && r>70) ? "High" : r>10000 || (spec.formula.resultFormat==="score" && r>45) ? "Medium" : "Low";
  document.getElementById("signal").textContent=signal;
  document.getElementById("resultCopy").textContent = `${spec.formula.resultLabel}: ${document.getElementById("result").textContent}. ${spec.outputs[2] || "Route this lead to the next action."}`;
}
addFields(); calc();
document.getElementById("calculate").addEventListener("click", calc);
document.querySelectorAll("input").forEach(i=>i.addEventListener("input", calc));