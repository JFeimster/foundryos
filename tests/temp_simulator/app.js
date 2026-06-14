const spec = window.FOUNDRY_SPEC;
const form = document.getElementById("toolForm");
const meter = document.getElementById("meter");
const result = document.getElementById("result");
const signal = document.getElementById("signal");
const resultCopy = document.getElementById("resultCopy");

function addFields() {
  form.innerHTML = "";
  spec.fields.forEach(field => {
    const label = document.createElement("label");
    label.textContent = field.label;
    const input = document.createElement("input");
    input.type = "number";
    input.id = field.key;
    input.value = field.default ?? 0;
    form.appendChild(label);
    form.appendChild(input);
  });
}

function values() {
  const data = {};
  spec.fields.forEach(field => {
    data[field.key] = Number(document.getElementById(field.key).value || 0);
  });
  return data;
}

function evaluate(data) {
  const formula = spec.formula || {};
  if (formula.type === "score") {
    const revenue = data.monthlyRevenue || 0;
    const credit = data.creditScore || 600;
    const cash = data.cashAvailable || 0;
    return Math.max(0, Math.min(100, Math.round((revenue / 1000) * 0.45 + ((credit - 500) / 3) + (cash / 1000) * 0.8)));
  }
  if (formula.type === "gap") {
    if (data.annualPremium !== undefined) return Math.max(0, data.annualPremium * (data.requiredDepositPct || 0) / 100 - (data.cashAvailable || 0));
    if (data.projectValue !== undefined) return Math.max(0, data.projectValue * (data.materialCostPct || 0) / 100 - (data.cashAvailable || 0));
    if (data.taxBalance !== undefined) return Math.max(0, data.taxBalance - (data.cashAvailable || 0));
    if (data.weeklyPayroll !== undefined) return Math.max(0, data.weeklyPayroll - (data.cashAvailable || 0));
    return Math.max(0, (data.amountNeeded || 0) - (data.cashAvailable || 0));
  }
  if (formula.type === "opportunity_cost") return Math.max(0, (data.heldPayout || 0) * (data.monthlyRoiPct || 0) / 100 * (data.daysHeld || 0) / 30);
  if (formula.type === "cost_of_delay") return Math.max(0, (data.repairCost || 0) + (data.dailyRevenue || 0) * (data.downtimeDays || 0));
  if (formula.type === "commission_plan") return Math.max(0, (data.targetIncome || 0) / Math.max(1, data.avgCommission || 1) / Math.max(0.01, (data.closeRatePct || 1) / 100));
  if (formula.type === "runway") return Math.max(0, (data.raiseAmount || 0) / Math.max(1, data.monthlyBurn || 1) + (data.currentRunway || 0));
  return 0;
}

function formatValue(value) {
  const formula = spec.formula || {};
  if (formula.resultFormat === "score") return `${Math.round(value)}/100`;
  if (formula.resultFormat === "currency") return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value);
}

function band(value) {
  const formula = spec.formula || {};
  if (formula.resultFormat === "score") {
    if (value >= 75) return "High";
    if (value >= 50) return "Medium";
    return "Low";
  }
  if (value > 50000) return "High";
  if (value > 10000) return "Medium";
  return "Low";
}

function calc() {
  const data = values();
  const value = evaluate(data);
  const display = formatValue(value);
  result.textContent = display;
  signal.textContent = band(value);
  meter.style.width = `${Math.min(100, Math.max(4, value))}%`;
  resultCopy.textContent = `${(spec.formula || {}).resultLabel || "Simulation output"}: ${display}. ${(spec.outputs || [])[2] || "Use this scenario to guide the next move."}`;
}

addFields();
calc();
document.getElementById("calculate").addEventListener("click", calc);
document.querySelectorAll("input").forEach(input => input.addEventListener("input", calc));
