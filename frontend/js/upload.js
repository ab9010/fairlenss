/*
 * upload.js
 * ---------
 * Handles loading the built-in demo dataset and uploading a user's own CSV.
 * Both paths converge on `onDatasetLoaded(data)`, which renders the
 * dataset overview + preview table and hands control to testing.js to
 * populate the column-selection dropdowns.
 */

let currentDataset = null; // { rows, column_names, column_types, ... }

function showError(message) {
  const banner = document.getElementById("error-banner");
  const text = document.getElementById("error-message");
  if (!banner || !text) return;
  text.textContent = message;
  banner.classList.remove("hidden");
  banner.scrollIntoView({ behavior: "smooth", block: "center" });
}

function clearError() {
  const banner = document.getElementById("error-banner");
  if (banner) banner.classList.add("hidden");
}

async function loadDemoDataset() {
  clearError();
  const note = document.getElementById("loading-note");
  const demoBtn = document.getElementById("btn-use-demo");
  if (note) note.style.display = "block";
  demoBtn.classList.add("selected");

  try {
    const response = await apiRequest("/demo-dataset");
    const data = await response.json();
    currentDataset = data;
    onDatasetLoaded(data);
  } catch (err) {
    showError(err.message);
  } finally {
    if (note) note.style.display = "none";
  }
}

async function uploadCsvFile(file) {
  clearError();
  const note = document.getElementById("loading-note");
  if (note) { note.style.display = "block"; note.textContent = `Uploading ${file.name}…`; }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await apiRequest("/upload", { method: "POST", body: formData });
    const data = await response.json();
    currentDataset = data;
    document.getElementById("btn-use-demo").classList.remove("selected");
    document.querySelector(".dataset-option-upload").classList.add("selected");
    onDatasetLoaded(data);
  } catch (err) {
    showError(err.message);
  } finally {
    if (note) { note.style.display = "none"; note.textContent = "Loading dataset…"; }
  }
}

function renderDatasetOverview(data) {
  document.getElementById("dataset-overview-card").classList.remove("hidden");
  document.getElementById("dataset-name-badge").textContent = data.is_synthetic
    ? "Synthetic demonstration dataset"
    : data.dataset_name;

  document.getElementById("stat-rows").textContent = data.rows;
  document.getElementById("stat-columns").textContent = data.columns;
  document.getElementById("stat-missing").textContent = data.missing_values;

  const suggestedAttr = data.suggested_protected_attributes && data.suggested_protected_attributes.length
    ? data.suggested_protected_attributes[0]
    : "—";
  document.getElementById("stat-protected").textContent = suggestedAttr;

  // Preview table
  const headRow = document.getElementById("preview-head");
  const body = document.getElementById("preview-body");
  headRow.innerHTML = "";
  body.innerHTML = "";

  data.column_names.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    headRow.appendChild(th);
  });

  data.preview_rows.forEach((row) => {
    const tr = document.createElement("tr");
    data.column_names.forEach((col) => {
      const td = document.createElement("td");
      td.textContent = row[col] ?? "";
      tr.appendChild(td);
    });
    body.appendChild(tr);
  });
}

function onDatasetLoaded(data) {
  renderDatasetOverview(data);
  if (typeof populateConfigStep === "function") {
    populateConfigStep(data);
  }
  document.getElementById("step-config").classList.remove("hidden");
  document.getElementById("step-config").scrollIntoView({ behavior: "smooth", block: "start" });
}

document.addEventListener("DOMContentLoaded", () => {
  const demoBtn = document.getElementById("btn-use-demo");
  const fileInput = document.getElementById("csv-upload");

  if (demoBtn) demoBtn.addEventListener("click", loadDemoDataset);

  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) uploadCsvFile(file);
    });
  }
});
