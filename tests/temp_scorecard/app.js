const spec = window.FOUNDRY_SPEC;
const form = document.getElementById("toolForm");
const score = document.getElementById("score");
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

function scoreValue(data) {
  const formula = spec.formula || {};
  if (formula.type === "score") {
    const revenue = data.monthlyRevenue || 0;
    const credit = data.creditScore || 600;
    const cash = data.cashAvailable || 0;
    return Math.max(0, Math.min(100, Math.round((revenue / 1000) * 0.45 + ((credit - 500) / 3) + (cash / 1000) * 0.8)));
  }

  const values = Object.values(data);
  const total = values.reduce((acc, value) => acc + Math.abs(Number(value) || 0), 0);
  const scaled = Math.max(0, Math.min(100, Math.round(total / Math.max(1, values.length * 1000))));
  return scaled;
}

function band(value) {
  if (value >= 75) return "High fit";
  if (value >= 50) return "Qualified with gaps";
  return "Needs nurture";
}

function calc() {
  const data = values();
  const value = scoreValue(data);
  score.textContent = value;
  signal.textContent = band(value);
  resultCopy.textContent = `${(spec.formula || {}).resultLabel || "Readiness score"} is ${value}/100. ${(spec.outputs || [])[0] || "Use the score to route the lead."}`;
  const ring = document.querySelector(".ring");
  ring.style.background = `conic-gradient(#7fd0ff 0 ${value}%, #20334d ${value}% 100%)`;
}

addFields();
calc();
document.getElementById("calculate").addEventListener("click", calc);
document.querySelectorAll("input").forEach(input => input.addEventListener("input", calc));
