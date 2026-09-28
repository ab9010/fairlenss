# FairLens

**AI Ethics & Bias Detection — Detect Bias. Measure Fairness. Build Responsible AI.**

FairLens is an educational, interactive fairness-testing platform built as a
college social internship prototype. It lets you load a dataset, pick a
protected attribute and an outcome column, and see real, calculated fairness
metrics — a fairness score, disparity charts, a plain-language explanation of
what was found, and tailored recommendations.

---

## Project overview

The project topic is **AI Ethics – Bias Detection: Tools for Fairness Testing
in AI Models**. FairLens combines:

1. Real fairness calculations (Python / pandas / scikit-learn)
2. AI ethics education (a dedicated Learn page)
3. Social awareness (real-world impact of biased AI)
4. A distinct, editorial-style UI (not a generic blue SaaS template)
5. An interactive bias/fairness testing experience, including a live slider-based simulator

## Problem statement

AI systems increasingly make or influence decisions that affect people's
lives — loan approvals, hiring, healthcare risk scores, and more. These
systems can be highly accurate overall while still treating demographic
groups very differently. Most people interacting with (or building) these
systems have no easy way to check for this. FairLens gives students and
practitioners a hands-on way to measure it.

## Objectives

- Create awareness about AI bias
- Demonstrate fairness testing on a real (synthetic) dataset
- Explain fairness metrics in plain language, technical detail underneath
- Help students understand responsible AI concretely
- Encourage ethical AI development habits early

## Features

- **Fairness Lab**: load the bundled demo dataset or upload your own CSV, auto-detect column types and likely protected attributes, then run a full fairness analysis
- **Real metrics**: demographic parity, disparate impact ("80% rule"), and equal opportunity (via a small trained logistic regression comparison model) — every number is calculated from your data, nothing is hard-coded
- **Fairness Score**: a transparent 0–100 composite score with a plain-language severity level
- **Results dashboard**: metric cards, four Chart.js visualizations, a "why was this detected" explanation, dynamically generated recommendations, and a before/after mitigation simulation
- **Bias Simulator**: two sliders that recalculate disparity metrics in real time, both instantly on the client and confirmed against the backend
- **Downloadable fairness report** (self-contained HTML, printable to PDF from the browser)
- **Learn page**: what AI ethics/bias is, five common bias types, real-world impact areas, and an interactive "Responsible AI" framework
- Friendly error handling for invalid/empty CSVs, missing columns, and insufficient groups
- Fully responsive, from 1920px desktops down to 390px phones

## Technology stack

**Frontend:** HTML5, CSS3, vanilla JavaScript, [Chart.js](https://www.chartjs.org/) (via CDN)

**Backend:** Python, FastAPI, Uvicorn

**Data / ML:** pandas, NumPy, scikit-learn (a small LogisticRegression model powers the Equal Opportunity metric)

**Report generation:** a self-contained HTML report generated server-side (no extra PDF dependency — open it in a browser and use Print → Save as PDF if you need a PDF file)

## Folder structure

```text
FairLens/
│
├── frontend/
│   ├── index.html          Homepage
│   ├── bias-test.html      Fairness Testing Lab + Bias Simulator
│   ├── results.html        Results dashboard
│   ├── learn.html          AI ethics education
│   ├── about.html          About / disclaimer
│   │
│   ├── css/
│   │   ├── style.css       Shared design system (nav, footer, buttons, tokens)
│   │   ├── home.css        Homepage sections
│   │   ├── testing.css     Fairness Lab + Simulator
│   │   ├── results.css     Results dashboard
│   │   └── learn.css       Learn + About pages
│   │
│   ├── js/
│   │   ├── main.js         API base URL, nav toggle, shared helpers
│   │   ├── upload.js       Demo dataset loading + CSV upload
│   │   ├── testing.js      Column selection, run-test flow, Bias Simulator
│   │   ├── results.js      Results dashboard rendering + report download
│   │   └── charts.js       Chart.js helper functions
│   │
│   └── assets/
│       ├── images/
│       └── icons/
│
├── backend/
│   ├── main.py              FastAPI app + CORS
│   ├── routes.py            All API endpoints
│   ├── fairness.py          The fairness calculation engine
│   ├── data_processor.py    CSV parsing, validation, column detection
│   └── report_generator.py  HTML fairness report builder
│
├── data/
│   └── sample_dataset.csv   Synthetic demo dataset (360 rows)
│
├── reports/                 (generated reports land here if saved locally)
│
├── requirements.txt
├── README.md
└── .gitignore
```

## How the fairness analysis works

1. **Selection rates** — for each group in the protected attribute (e.g. Male/Female), what fraction received the positive outcome?
2. **Demographic parity** — the ratio and percentage-point gap between the best- and worst-served groups.
3. **Disparate impact** — the classic "80% rule": worst group's rate ÷ best group's rate.
4. **Equal opportunity** — a small logistic regression is trained on the dataset's non-protected features to predict the outcome, standing in for "a model." Its true positive rate is then compared across groups — this shows whether a model built *without* the protected attribute as a feature still ends up treating groups differently.
5. **Fairness Score** — a transparent, adjustable formula (see `backend/fairness.py::calculate_fairness_score`) combining the three metrics above into one 0–100 number, with plain-language bands: 80–100 Relatively Fair, 60–79 Moderate Disparity, 40–59 High Disparity, 0–39 Severe Disparity.
6. **Recommendations** — generated based on which thresholds were actually crossed, not a fixed script.
7. **Mitigation simulation** — an educational simulation of what a fairness-aware threshold adjustment could look like, nudging each group's rate toward the mean. This is clearly labeled as a simulation, not a retrained model.

## Dataset

`data/sample_dataset.csv` is a **synthetic demonstration dataset** created
for this project — it does not represent real people. It simulates loan
applications with columns:

`age, age_group, gender, income, education, employment_years, credit_score, loan_amount, approved`

It was generated with an intentional, moderate gender disparity (roughly a
19-percentage-point gap in approval rate) so the fairness tools have
something meaningful to detect. You can regenerate or tweak it by editing
the generation script described at the bottom of `backend/fairness.py`'s
docstring context, or simply replacing the CSV with your own.

## Installation

```bash
git clone <repository-url>
cd FairLens

python -m venv venv
```

Activate the virtual environment:

- **Windows:** `venv\Scripts\activate`
- **macOS / Linux:** `source venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the project

**1. Start the backend API** (from the `FairLens` project root):

```bash
uvicorn backend.main:app --reload
```

This starts the API at `http://127.0.0.1:8000`. Interactive docs are at
`http://127.0.0.1:8000/docs`.

**2. Serve the frontend.** Because the frontend makes `fetch()` calls to the
API, open it through a local web server rather than double-clicking the HTML
file. The simplest option, in a second terminal:

```bash
cd frontend
python -m http.server 5500
```

Then open `http://127.0.0.1:5500/index.html` in your browser.

(If you use VS Code's "Live Server" extension instead, right-click
`frontend/index.html` → "Open with Live Server" — that works too.)

## Deploying on Render

FairLens can run as a single Render web service: FastAPI serves both the API
and the static frontend. The included `render.yaml` is a Render Blueprint
configuration.

1. Push the project to a Git repository.
2. In Render, choose **New → Blueprint** and select the repository.
3. Render will use the commands in `render.yaml`; no frontend build step is required.
4. Open the generated service URL. The frontend is at `/`, the API docs are at `/docs`, and the health check is at `/api/health`.

The service binds to Render's `$PORT` and `0.0.0.0`, which is required for
Render's web service health checks. Uploaded CSV files are processed in
memory and are not persisted between requests or deploys.

## Demo flow

1. Open the homepage → click **Start Fairness Test**
2. On the Fairness Lab, click **Use Demo Dataset**
3. Gender and Approved are auto-selected as sensible defaults — adjust if you like
4. Click **Run Fairness Test** and watch the analysis animation
5. Review the Fairness Score, charts, explanation, and recommendations on the results page
6. Scroll to the Before/After mitigation simulation
7. Click **Download Fairness Report**
8. Go back to the Fairness Lab and try the **Bias Simulator** sliders

## API endpoints

| Method | Path                 | Description                                                        |
|--------|----------------------|----------------------------------------------------------------------|
| GET    | `/api/health`        | Health check                                                        |
| GET    | `/api/demo-dataset`  | Returns the bundled synthetic dataset + column analysis            |
| POST   | `/api/upload`        | Accepts a CSV file upload, returns parsed data + column analysis   |
| POST   | `/api/analyze`       | Runs the full fairness analysis on the provided rows               |
| POST   | `/api/simulate`      | Powers the Bias Simulator sliders                                  |
| POST   | `/api/report`        | Generates and returns a downloadable HTML fairness report          |

## Screenshots

_Add screenshots of the homepage, Fairness Lab, and Results dashboard here before your presentation._

## Future improvements

- Support additional fairness metrics (e.g. predictive parity, calibration)
- Persist analysis history so users can compare multiple runs
- Add authentication so uploaded datasets can be saved between sessions
- Offer a true PDF export using a headless-browser renderer
- Expand the mitigation simulation into a real reweighing/threshold-optimizer implementation

## Disclaimer

FairLens is an educational prototype designed to demonstrate concepts in AI
fairness and bias detection. Its metrics and scoring should not be
interpreted as legal, regulatory, medical, financial, or production-model
certification. The bundled demonstration dataset is entirely synthetic and
was created solely for educational purposes.
