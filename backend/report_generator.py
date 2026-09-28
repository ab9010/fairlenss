"""
report_generator.py
--------------------
Builds a self-contained, downloadable HTML fairness report from a completed
analysis result. The report opens correctly in any browser and can be
printed to PDF by the user (File > Print > Save as PDF) without needing any
extra PDF libraries — keeping the prototype dependency-light and reliable.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _rows_table(rates: dict[str, float]) -> str:
    rows = ""
    for group, rate in rates.items():
        rows += f"<tr><td>{group}</td><td>{rate * 100:.1f}%</td></tr>"
    return rows


def _recommendations_html(recommendations: list[dict[str, str]]) -> str:
    items = ""
    for rec in recommendations:
        items += f"<li><strong>{rec['title']}</strong><p>{rec['text']}</p></li>"
    return items


def generate_html_report(analysis: dict[str, Any], meta: dict[str, Any]) -> str:
    """
    analysis: the full JSON result produced by /api/analyze
    meta: {dataset_name, protected_attribute, outcome_column, positive_outcome}
    """
    now = datetime.now().strftime("%d %B %Y, %H:%M")

    score = analysis.get("fairness_score", 0)
    bias_level = analysis.get("bias_level", {}).get("level", "Unknown")
    selection_rates = analysis.get("selection_rates", {})
    demographic_parity = analysis.get("demographic_parity", {})
    disparate_impact = analysis.get("disparate_impact", 0)
    equal_opportunity = analysis.get("equal_opportunity", {})
    recommendations = analysis.get("recommendations", [])
    mitigation = analysis.get("mitigation", {})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FairLens Fairness Report</title>
<style>
    body {{
        font-family: 'Georgia', 'Times New Roman', serif;
        max-width: 800px;
        margin: 40px auto;
        padding: 0 24px;
        color: #201E1A;
        line-height: 1.6;
    }}
    h1, h2 {{ font-family: Arial, Helvetica, sans-serif; }}
    .masthead {{
        border-bottom: 3px solid #201E1A;
        padding-bottom: 16px;
        margin-bottom: 24px;
    }}
    .masthead .brand {{
        font-size: 13px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #B5541E;
        font-family: Arial, Helvetica, sans-serif;
    }}
    .masthead h1 {{ margin: 4px 0; font-size: 30px; }}
    .meta-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px 24px;
        background: #F4F1E9;
        padding: 16px 20px;
        border: 1px solid #DAD3C4;
        margin-bottom: 28px;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 14px;
    }}
    .score-block {{
        text-align: center;
        padding: 28px;
        background: #201E1A;
        color: #F4F1E9;
        margin-bottom: 28px;
    }}
    .score-block .score {{ font-size: 56px; font-weight: bold; font-family: Arial, sans-serif; }}
    .score-block .level {{ font-size: 16px; letter-spacing: 1px; text-transform: uppercase; color: #E8B02E; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0 24px; font-family: Arial, sans-serif; font-size: 14px; }}
    th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #DAD3C4; }}
    th {{ background: #F4F1E9; }}
    ul.recs {{ list-style: none; padding: 0; }}
    ul.recs li {{ border-left: 3px solid #B5541E; padding: 6px 0 6px 14px; margin-bottom: 14px; }}
    ul.recs p {{ margin: 4px 0 0; font-size: 14px; }}
    .disclaimer {{
        margin-top: 40px;
        font-size: 12px;
        color: #6B6656;
        border-top: 1px solid #DAD3C4;
        padding-top: 16px;
        font-family: Arial, sans-serif;
    }}
    @media print {{ body {{ margin: 0; }} }}
</style>
</head>
<body>

<div class="masthead">
    <div class="brand">FairLens &middot; AI Ethics &amp; Bias Detection</div>
    <h1>AI Fairness Analysis Report</h1>
</div>

<div class="meta-grid">
    <div><strong>Dataset:</strong> {meta.get('dataset_name', 'Uploaded dataset')}</div>
    <div><strong>Generated:</strong> {now}</div>
    <div><strong>Protected attribute:</strong> {meta.get('protected_attribute', '-')}</div>
    <div><strong>Outcome column:</strong> {meta.get('outcome_column', '-')}</div>
    <div><strong>Positive outcome:</strong> {meta.get('positive_outcome', '-')}</div>
    <div><strong>Rows analyzed:</strong> {analysis.get('row_count', '-')}</div>
</div>

<div class="score-block">
    <div class="score">{score}<span style="font-size: 22px;">/100</span></div>
    <div class="level">{bias_level}</div>
</div>

<h2>Fairness Metrics</h2>
<table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Demographic Parity Ratio</td><td>{demographic_parity.get('ratio', '-')}</td></tr>
    <tr><td>Selection Rate Difference</td><td>{demographic_parity.get('difference', 0) * 100:.1f} percentage points</td></tr>
    <tr><td>Disparate Impact</td><td>{disparate_impact}</td></tr>
    <tr><td>Equal Opportunity Difference</td><td>{equal_opportunity.get('difference', 0) * 100:.1f} percentage points</td></tr>
</table>

<h2>Selection Rate by Group</h2>
<table>
    <tr><th>Group</th><th>Positive Outcome Rate</th></tr>
    {_rows_table(selection_rates)}
</table>

<h2>Educational Mitigation Simulation</h2>
<p>This is a simplified, educational simulation of a fairness-aware threshold
adjustment &mdash; it does not represent a scientifically retrained model.</p>
<table>
    <tr><th>Group</th><th>Before</th><th>After (simulated)</th></tr>
    {''.join(f"<tr><td>{g}</td><td>{mitigation.get('before', {}).get(g, 0)*100:.1f}%</td><td>{mitigation.get('after', {}).get(g, 0)*100:.1f}%</td></tr>" for g in mitigation.get('before', {}))}
</table>

<h2>Recommendations</h2>
<ul class="recs">
    {_recommendations_html(recommendations)}
</ul>

<div class="disclaimer">
    <p><strong>Disclaimer:</strong> FairLens is an educational prototype designed to
    demonstrate concepts in AI fairness and bias detection. Its metrics and
    scoring should not be interpreted as legal, regulatory, medical, financial,
    or production-model certification. The Fairness Score is an educational
    composite indicator used by this prototype and is not a universal
    regulatory or scientific threshold.</p>
    <p>If this report was generated using the bundled demonstration dataset,
    that dataset is entirely synthetic and was created solely for educational
    purposes. It does not represent real people or real financial decisions.</p>
</div>

</body>
</html>"""

    return html
