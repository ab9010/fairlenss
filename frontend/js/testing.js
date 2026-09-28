/*
 * testing.js
 * ----------
 * Drives Step 2-4 of the Fairness Lab (selecting columns), the "Run
 * Fairness Test" flow with its analysis animation, and the standalone
 * Bias Simulator sliders.
 */

function fillSelect(selectEl, options, preferredValue) {
  selectEl.innerHTML = "";
  options.forEach((opt) => {
    const el = document.createElement("option");
    el.value = opt;
    el.textContent = opt;
    selectEl.appendChild(el);
  });
  if (preferredValue && options.includes(preferredValue)) {
    selectEl.value = preferredValue;
  }
}

function populateOutcomeValueOptions(data, outcomeColumn) {
  const positiveSelect = document.getElementById("select-positive");
  const values = Array.from(
    new Set(data.records.map((row) => String(row[outcomeColumn])))
  ).sort();

  // Prefer common "positive" labels if present
  const preferredPositives = ["yes", "approved", "1", "true", "hired", "accepted"];
  const preferred = values.find((v) => preferredPositives.includes(v.toLowerCase()));

  fillSelect(positiveSelect, values, preferred || values[0]);
}

function populateConfigStep(data) {
  const protectedSelect = document.getElementById("select-protected");
  const outcomeSelect = document.getElementById("select-outcome");

  const protectedDefault = data.suggested_protected_attributes[0] || data.column_names[0];
  const outcomeDefault = data.suggested_outcome_columns.find((c) => c !== protectedDefault)
    || data.column_names.find((c) => c !== protectedDefault);

  fillSelect(protectedSelect, data.column_names, protectedDefault);
  fillSelect(outcomeSelect, data.column_names, outcomeDefault);

  populateOutcomeValueOptions(data, outcomeSelect.value);

  outcomeSelect.onchange = () => populateOutcomeValueOptions(data, outcomeSelect.value);
}

function runAnalysisAnimation() {
  return new Promise((resolve) => {
    const card = document.getElementById("analysis-card");
    card.classList.remove("hidden");
    card.scrollIntoView({ behavior: "smooth", block: "start" });

    const steps = card.querySelectorAll("li");
    let i = 0;

    function advance() {
      if (i > 0) steps[i - 1].classList.remove("active");
      if (i >= steps.length) {
        resolve();
        return;
      }
      steps[i].classList.add("active");
      setTimeout(() => {
        steps[i].classList.remove("active");
        steps[i].classList.add("done");
        i += 1;
        advance();
      }, 480);
    }
    advance();
  });
}

async function runFairnessTest() {
  clearError();

  if (!currentDataset) {
    showError("Please load a dataset first (use the demo dataset or upload a CSV).");
    return;
  }

  const protectedAttribute = document.getElementById("select-protected").value;
  const outcomeColumn = document.getElementById("select-outcome").value;
  const positiveOutcome = document.getElementById("select-positive").value;

  const runButton = document.getElementById("btn-run-test");
  runButton.disabled = true;
  runButton.textContent = "Running…";

  // Reset animation state in case the user runs the test more than once
  document.querySelectorAll("#analysis-steps li").forEach((li) => li.classList.remove("done", "active"));

  const animationPromise = runAnalysisAnimation();

  try {
    const [response] = await Promise.all([
      apiRequest("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rows: currentDataset.records,
          protected_attribute: protectedAttribute,
          outcome_column: outcomeColumn,
          positive_outcome: positiveOutcome,
          dataset_name: currentDataset.dataset_name,
        }),
      }),
      animationPromise,
    ]);

    const analysis = await response.json();

    sessionStorage.setItem("fairlens_analysis", JSON.stringify(analysis));
    sessionStorage.setItem("fairlens_meta", JSON.stringify({
      dataset_name: currentDataset.dataset_name,
      protected_attribute: protectedAttribute,
      outcome_column: outcomeColumn,
      positive_outcome: positiveOutcome,
    }));

    window.location.href = "results.html";
  } catch (err) {
    document.getElementById("analysis-card").classList.add("hidden");
    showError(err.message);
    runButton.disabled = false;
    runButton.textContent = "Run Fairness Test";
  }
}

/* --------------------------------------------------------------------
   Bias Simulator
   -------------------------------------------------------------------- */

let simulatorChart = null;
let simulatorDebounce = null;

function renderSimulatorChart(rateA, rateB) {
  if (simulatorChart) simulatorChart.destroy();
  simulatorChart = makeGroupedBarChart(
    "simulator-chart",
    ["Group A", "Group B"],
    [{ label: "Selection rate", data: [rateA, rateB] }]
  );
}

function updateSimulatorReadout(result) {
  document.getElementById("sim-difference").textContent = `${(result.difference * 100).toFixed(1)} pts`;
  document.getElementById("sim-impact").textContent = result.disparate_impact.toFixed(2);
  const statusEl = document.getElementById("sim-status");
  statusEl.textContent = result.status;
  statusEl.className = "readout-value";
  statusEl.classList.add(`tone-${result.tone}`);
}

async function runSimulation() {
  const a = Number(document.getElementById("slider-a").value) / 100;
  const b = Number(document.getElementById("slider-b").value) / 100;

  document.getElementById("value-a").textContent = `${Math.round(a * 100)}%`;
  document.getElementById("value-b").textContent = `${Math.round(b * 100)}%`;
  renderSimulatorChart(Math.round(a * 100), Math.round(b * 100));

  // Instant local estimate first, for a snappy feel
  const localDiff = Math.abs(a - b);
  const localImpact = Math.max(a, b) > 0 ? Math.min(a, b) / Math.max(a, b) : 1;
  updateSimulatorReadout({
    difference: localDiff,
    disparate_impact: localImpact,
    status: localDiff < 0.1 ? "Relatively Fair" : localDiff < 0.25 ? "Moderate Disparity" : "High Disparity",
    tone: localDiff < 0.1 ? "good" : localDiff < 0.25 ? "moderate" : "high",
  });

  // Then confirm with the real backend calculation (debounced)
  clearTimeout(simulatorDebounce);
  simulatorDebounce = setTimeout(async () => {
    try {
      const response = await apiRequest("/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ group_a_rate: a, group_b_rate: b }),
      });
      const result = await response.json();
      updateSimulatorReadout(result);
    } catch (err) {
      // The simulator still works locally if the backend is briefly unreachable
      console.warn("Simulator backend call failed:", err.message);
    }
  }, 250);
}

document.addEventListener("DOMContentLoaded", () => {
  const runButton = document.getElementById("btn-run-test");
  if (runButton) runButton.addEventListener("click", runFairnessTest);

  const sliderA = document.getElementById("slider-a");
  const sliderB = document.getElementById("slider-b");
  if (sliderA && sliderB) {
    sliderA.addEventListener("input", runSimulation);
    sliderB.addEventListener("input", runSimulation);
    runSimulation();
  }
});
