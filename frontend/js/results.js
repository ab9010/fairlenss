/*
 * results.js
 * ----------
 * Reads the analysis produced by the Fairness Lab (stored in
 * sessionStorage) and renders the full results dashboard: score, severity
 * gauge, metric cards, four charts, the plain-language explanation,
 * recommendations, the before/after mitigation simulation, and the
 * "Download Fairness Report" button.
 */

function toneForRatio(ratio) {
  if (ratio >= 0.8) return "good";
  if (ratio >= 0.6) return "moderate";
  if (ratio >= 0.4) return "high";
  return "severe";
}

function toneForDifference(diff) {
  if (diff <= 0.05) return "good";
  if (diff <= 0.15) return "moderate";
  if (diff <= 0.25) return "high";
  return "severe";
}

function toneLabel(tone) {
  return { good: "Relatively Fair", moderate: "Moderate", high: "High Disparity", severe: "Severe" }[tone];
}

function renderMetricCards(analysis) {
  const container = document.getElementById("metric-cards");
  const dp = analysis.demographic_parity;
  const di = analysis.disparate_impact;
  const eo = analysis.equal_opportunity;

  const dpTone = toneForRatio(dp.ratio);
  const diTone = toneForRatio(di);
  const eoTone = toneForDifference(eo.difference || 0);
  const diffTone = toneForDifference(dp.difference);

  const cards = [
    {
      title: "Demographic Parity",
      value: dp.ratio.toFixed(2),
      explain: "Ratio of the lowest to highest group selection rate. 1.00 means perfect parity.",
      tone: dpTone,
    },
    {
      title: "Disparate Impact",
      value: di.toFixed(2),
      explain: "The classic '80% rule' — a value under 0.80 is a traditional red flag.",
      tone: diTone,
    },
    {
      title: "Equal Opportunity",
      value: eo.difference != null ? (1 - eo.difference).toFixed(2) : "—",
      explain: "How equally a comparison model identifies deserving candidates across groups.",
      tone: eoTone,
    },
    {
      title: "Selection Rate Difference",
      value: `${(dp.difference * 100).toFixed(0)}%`,
      explain: `Gap between ${dp.best_group} and ${dp.worst_group}'s positive outcome rate.`,
      tone: diffTone,
    },
  ];

  container.innerHTML = cards.map((c) => `
    <div class="metric-card">
      <div class="metric-card-head">
        <h4>${c.title}</h4>
        <span class="metric-info" title="${c.explain}">i</span>
      </div>
      <div class="metric-value">${c.value}</div>
      <p class="metric-explain">${c.explain}</p>
      <span class="metric-status tone-${c.tone}">${toneLabel(c.tone)}</span>
    </div>
  `).join("");
}

function renderExplanation(analysis) {
  const dp = analysis.demographic_parity;
  const el = document.getElementById("explanation-card");

  if (!dp.best_group || dp.difference === 0) {
    el.innerHTML = `<p>The selected groups received the positive outcome at very similar rates in this dataset. No meaningful disparity was detected for <strong>${analysis.protected_attribute}</strong> on <strong>${analysis.outcome_column}</strong>.</p>`;
    return;
  }

  el.innerHTML = `
    <p>The positive outcome rate differs between the selected demographic groups.</p>
    <p class="figure-line"><strong>${dp.best_group}</strong> applicants: ${(dp.best_rate * 100).toFixed(0)}% received <em>${analysis.positive_outcome}</em></p>
    <p class="figure-line"><strong>${dp.worst_group}</strong> applicants: ${(dp.worst_rate * 100).toFixed(0)}% received <em>${analysis.positive_outcome}</em></p>
    <p class="figure-line">Difference: <strong>${(dp.difference * 100).toFixed(0)} percentage points</strong></p>
    <p>This indicates that the data/model produces different outcome rates for these two groups. This does not automatically prove the model is "biased" in a legal sense — but it does mean the disparity is real and worth investigating further, especially if the groups are otherwise similarly qualified.</p>
  `;
}

function renderRecommendations(recommendations) {
  const grid = document.getElementById("recommendation-grid");
  grid.innerHTML = recommendations.map((r) => `
    <div class="recommendation-card">
      <h4>${r.title}</h4>
      <p>${r.text}</p>
    </div>
  `).join("");
}

function renderMitigationTable(mitigation) {
  const tbody = document.querySelector("#mitigation-table tbody");
  tbody.innerHTML = Object.keys(mitigation.before).map((group) => `
    <tr>
      <td>${group}</td>
      <td>${(mitigation.before[group] * 100).toFixed(0)}%</td>
      <td>${(mitigation.after[group] * 100).toFixed(0)}%</td>
    </tr>
  `).join("");
}

function renderCharts(analysis) {
  const groups = Object.keys(analysis.selection_rates);

  makeBarChart(
    "chart-approval",
    groups,
    groups.map((g) => Math.round(analysis.selection_rates[g] * 100)),
    { label: "Approval rate" }
  );

  makeDoughnutChart(
    "chart-distribution",
    groups,
    groups.map((g) => analysis.group_counts[g] || 0)
  );

  const outcomeLabels = new Set();
  groups.forEach((g) => Object.keys(analysis.outcome_distribution[g] || {}).forEach((k) => outcomeLabels.add(k)));
  const labelsArr = Array.from(outcomeLabels);
  const positiveLabel = analysis.positive_outcome;
  const otherLabel = labelsArr.find((l) => l !== positiveLabel) || "Other";

  makeStackedOutcomeChart(
    "chart-outcome",
    groups,
    groups.map((g) => (analysis.outcome_distribution[g] || {})[positiveLabel] || 0),
    groups.map((g) => (analysis.outcome_distribution[g] || {})[otherLabel] || 0),
    positiveLabel,
    otherLabel
  );

  makeMetricRadar(
    "chart-metrics",
    ["Demographic Parity", "Disparate Impact", "Equal Opportunity"],
    [
      Math.round(analysis.demographic_parity.ratio * 100),
      Math.round(analysis.disparate_impact * 100),
      Math.round((1 - (analysis.equal_opportunity.difference || 0)) * 100),
    ]
  );

  const mitGroups = Object.keys(analysis.mitigation.before);
  makeBeforeAfterChart(
    "chart-mitigation",
    mitGroups,
    mitGroups.map((g) => Math.round(analysis.mitigation.before[g] * 100)),
    mitGroups.map((g) => Math.round(analysis.mitigation.after[g] * 100))
  );
}

function renderScore(analysis) {
  const scoreEl = document.getElementById("score-value");
  animateCount(scoreEl, analysis.fairness_score, 900);
  document.getElementById("score-level").textContent = analysis.bias_level.level;
  document.getElementById("severity-marker").style.left = `${analysis.fairness_score}%`;
}

async function downloadReport(analysis, meta) {
  const btn = document.getElementById("btn-download-report");
  btn.disabled = true;
  btn.textContent = "Preparing report…";

  try {
    const response = await apiRequest("/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        analysis,
        dataset_name: meta.dataset_name,
        protected_attribute: meta.protected_attribute,
        outcome_column: meta.outcome_column,
        positive_outcome: meta.positive_outcome,
      }),
    });
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "fairlens-fairness-report.html";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert(`We couldn't generate the report: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = "Download Fairness Report";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const rawAnalysis = sessionStorage.getItem("fairlens_analysis");
  const rawMeta = sessionStorage.getItem("fairlens_meta");

  if (!rawAnalysis || !rawMeta) {
    document.getElementById("empty-state").classList.remove("hidden");
    return;
  }

  const analysis = JSON.parse(rawAnalysis);
  const meta = JSON.parse(rawMeta);

  document.getElementById("results-content").classList.remove("hidden");
  document.getElementById("report-dataset-name").textContent = meta.dataset_name;
  document.getElementById("report-meta-line").textContent =
    `Protected attribute: ${meta.protected_attribute} · Outcome: ${meta.outcome_column} · Positive outcome: ${meta.positive_outcome} · ${analysis.row_count} rows analyzed`;

  renderScore(analysis);
  renderMetricCards(analysis);
  renderCharts(analysis);
  renderExplanation(analysis);
  renderRecommendations(analysis.recommendations);
  renderMitigationTable(analysis.mitigation);

  document.getElementById("btn-download-report").addEventListener("click", () => downloadReport(analysis, meta));
});
