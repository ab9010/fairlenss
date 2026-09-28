"""
routes.py
---------
All API endpoints for FairLens, in one router. See README.md for the full
list of endpoints and example request/response shapes.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import data_processor, fairness, report_generator

router = APIRouter(prefix="/api")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEMO_DATASET_PATH = os.path.join(DATA_DIR, "sample_dataset.csv")


# --------------------------------------------------------------------------
# Request models
# --------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    rows: list[dict[str, Any]] = Field(..., description="Dataset records as a list of row objects")
    protected_attribute: str
    outcome_column: str
    positive_outcome: str
    dataset_name: Optional[str] = "Uploaded dataset"


class SimulateRequest(BaseModel):
    group_a_rate: float
    group_b_rate: float


class ReportRequest(BaseModel):
    analysis: dict[str, Any]
    dataset_name: Optional[str] = "Uploaded dataset"
    protected_attribute: str
    outcome_column: str
    positive_outcome: str


# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "FairLens API"}


# --------------------------------------------------------------------------
# Demo dataset
# --------------------------------------------------------------------------

@router.get("/demo-dataset")
def get_demo_dataset():
    if not os.path.exists(DEMO_DATASET_PATH):
        raise HTTPException(status_code=500, detail="The demo dataset file is missing from the server.")

    df = pd.read_csv(DEMO_DATASET_PATH)
    summary = data_processor.build_dataset_summary(df)

    return {
        "dataset_name": "Loan Approval Demo Dataset (Synthetic)",
        "is_synthetic": True,
        "records": df.fillna("").astype(str).to_dict(orient="records"),
        **summary,
    }


# --------------------------------------------------------------------------
# Upload
# --------------------------------------------------------------------------

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")

    raw_bytes = await file.read()

    try:
        df = data_processor.read_csv_bytes(raw_bytes)
    except data_processor.DatasetValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    summary = data_processor.build_dataset_summary(df)

    return {
        "dataset_name": file.filename,
        "is_synthetic": False,
        "records": df.fillna("").astype(str).to_dict(orient="records"),
        **summary,
    }


# --------------------------------------------------------------------------
# Analyze
# --------------------------------------------------------------------------

@router.post("/analyze")
def analyze_dataset(payload: AnalyzeRequest):
    try:
        df = data_processor.dataframe_from_records(payload.rows)
        data_processor.validate_analysis_inputs(
            df, payload.protected_attribute, payload.outcome_column, payload.positive_outcome
        )
    except data_processor.DatasetValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    selection_rates = fairness.calculate_selection_rates(
        df, payload.protected_attribute, payload.outcome_column, payload.positive_outcome
    )
    group_counts = fairness.calculate_group_counts(df, payload.protected_attribute)
    outcome_distribution = fairness.calculate_outcome_distribution(
        df, payload.protected_attribute, payload.outcome_column
    )
    demographic_parity = fairness.calculate_demographic_parity(selection_rates)
    disparate_impact = fairness.calculate_disparate_impact(selection_rates)
    equal_opportunity = fairness.calculate_equal_opportunity(
        df, payload.protected_attribute, payload.outcome_column, payload.positive_outcome
    )

    fairness_score = fairness.calculate_fairness_score(
        demographic_parity_difference=demographic_parity.get("difference", 0.0),
        disparate_impact=disparate_impact,
        equal_opportunity_difference=equal_opportunity.get("difference", 0.0),
    )
    bias_level = fairness.determine_bias_level(fairness_score)
    recommendations = fairness.generate_recommendations(
        fairness_score, demographic_parity, disparate_impact, equal_opportunity
    )
    mitigation = fairness.simulate_mitigation(selection_rates)

    return {
        "dataset_name": payload.dataset_name,
        "row_count": int(len(df)),
        "protected_attribute": payload.protected_attribute,
        "outcome_column": payload.outcome_column,
        "positive_outcome": payload.positive_outcome,
        "selection_rates": selection_rates,
        "group_counts": group_counts,
        "outcome_distribution": outcome_distribution,
        "demographic_parity": demographic_parity,
        "disparate_impact": disparate_impact,
        "equal_opportunity": equal_opportunity,
        "fairness_score": fairness_score,
        "bias_level": bias_level,
        "recommendations": recommendations,
        "mitigation": mitigation,
    }


# --------------------------------------------------------------------------
# Simulate (Bias Simulator sliders)
# --------------------------------------------------------------------------

@router.post("/simulate")
def simulate(payload: SimulateRequest):
    result = fairness.simulate_bias_scenario(payload.group_a_rate, payload.group_b_rate)
    return result


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

@router.post("/report")
def download_report(payload: ReportRequest):
    meta = {
        "dataset_name": payload.dataset_name,
        "protected_attribute": payload.protected_attribute,
        "outcome_column": payload.outcome_column,
        "positive_outcome": payload.positive_outcome,
    }
    html = report_generator.generate_html_report(payload.analysis, meta)

    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=fairlens-fairness-report.html"},
    )
