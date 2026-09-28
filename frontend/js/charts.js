/*
 * charts.js
 * ---------
 * Small wrapper functions around Chart.js so results.js and testing.js stay
 * readable. Every function returns the created Chart instance so the caller
 * can destroy/replace it later (e.g. when the simulator sliders move).
 */

const CHART_PALETTE = ["#b5541e", "#6b7f3a", "#c99a2e", "#4a5a80", "#9c3b2e", "#7a6a4f"];

Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.color = "#55503f";
Chart.defaults.borderColor = "#d4cab3";

function pctTick(value) {
  return `${value}%`;
}

function makeBarChart(canvasId, labels, data, { label = "", horizontal = false } = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label,
          data,
          backgroundColor: labels.map((_, i) => CHART_PALETTE[i % CHART_PALETTE.length]),
          borderRadius: 4,
          maxBarThickness: 64,
        },
      ],
    },
    options: {
      indexAxis: horizontal ? "y" : "x",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: horizontal ? { max: 100, ticks: { callback: pctTick } } : { grid: { display: false } },
        y: horizontal ? { grid: { display: false } } : { max: 100, ticks: { callback: pctTick } },
      },
    },
  });
}

function makeGroupedBarChart(canvasId, labels, datasets) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: datasets.map((ds, i) => ({
        ...ds,
        backgroundColor: CHART_PALETTE[i % CHART_PALETTE.length],
        borderRadius: 4,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
      scales: { y: { beginAtZero: true } },
    },
  });
}

function makeStackedOutcomeChart(canvasId, labels, positiveData, negativeData, positiveLabel, negativeLabel) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: positiveLabel, data: positiveData, backgroundColor: "#6b7f3a", borderRadius: 3 },
        { label: negativeLabel, data: negativeData, backgroundColor: "#d4cab3", borderRadius: 3 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
      scales: {
        x: { stacked: true, grid: { display: false } },
        y: { stacked: true, beginAtZero: true },
      },
    },
  });
}

function makeDoughnutChart(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data, backgroundColor: CHART_PALETTE, borderWidth: 0 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "62%",
      plugins: { legend: { position: "bottom" } },
    },
  });
}

function makeBeforeAfterChart(canvasId, labels, beforeData, afterData) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "Before", data: beforeData, backgroundColor: "#9c3b2e", borderRadius: 4 },
        { label: "After (simulated)", data: afterData, backgroundColor: "#6b7f3a", borderRadius: 4 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
      scales: { y: { max: 100, ticks: { callback: pctTick } } },
    },
  });
}

function makeMetricRadar(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: "radar",
    data: {
      labels,
      datasets: [
        {
          label: "Fairness metrics (100 = best)",
          data,
          backgroundColor: "rgba(181, 84, 30, 0.18)",
          borderColor: "#b5541e",
          pointBackgroundColor: "#b5541e",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { r: { min: 0, max: 100, ticks: { stepSize: 20 } } },
      plugins: { legend: { display: false } },
    },
  });
}
