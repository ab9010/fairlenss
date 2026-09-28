"""
data_processor.py
------------------
Handles turning a raw CSV (uploaded file or the bundled demo dataset) into
a clean pandas DataFrame, plus utility functions that describe the dataset
back to the frontend: column types, missing values, and a guess at which
columns look like protected attributes.
"""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

# Column names commonly used for protected/demographic attributes.
# Used only to suggest a sensible default in the UI — the user can always
# pick a different column.
LIKELY_PROTECTED_NAMES = [
    "gender", "sex", "age", "age_group", "race", "ethnicity",
    "location", "region", "disability", "disability_status",
    "marital_status", "nationality",
]

LIKELY_OUTCOME_NAMES = [
    "approved", "outcome", "result", "decision", "target",
    "label", "hired", "accepted", "status",
]


class DatasetValidationError(Exception):
    """Raised when an uploaded CSV cannot be safely analyzed."""


def read_csv_bytes(raw_bytes: bytes) -> pd.DataFrame:
    """Parse raw CSV bytes into a DataFrame, with friendly error handling."""
    if not raw_bytes or len(raw_bytes.strip()) == 0:
        raise DatasetValidationError("The uploaded file is empty.")

    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        raise DatasetValidationError(
            "We couldn't read this file as a CSV. Please check the formatting "
            "and make sure it uses comma-separated values."
        ) from exc

    return validate_dataframe(df)


def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise DatasetValidationError("The dataset has no rows to analyze.")

    if len(df.columns) < 2:
        raise DatasetValidationError(
            "The dataset needs at least two columns: a protected attribute "
            "and an outcome column."
        )

    if len(df) < 10:
        raise DatasetValidationError(
            "The dataset is too small to produce a meaningful fairness "
            "analysis. Please provide at least 10 rows."
        )

    # Drop fully empty rows/columns which frequently sneak into CSV exports
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")

    return df.reset_index(drop=True)


def detect_column_types(df: pd.DataFrame) -> dict[str, str]:
    """Classify every column as 'numeric' or 'categorical'."""
    types: dict[str, str] = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            types[col] = "numeric"
        else:
            types[col] = "categorical"
    return types


def suggest_protected_attributes(df: pd.DataFrame, column_types: dict[str, str]) -> list[str]:
    """
    Suggest which columns are good protected-attribute candidates: either
    the name matches a common demographic term, or it's a low-cardinality
    categorical column (a handful of repeating groups).
    """
    suggestions: list[str] = []

    for col in df.columns:
        lower = col.lower().replace(" ", "_")
        if any(name in lower for name in LIKELY_PROTECTED_NAMES):
            suggestions.append(col)

    # Also add any low-cardinality categorical column not already included
    for col in df.columns:
        if col in suggestions:
            continue
        if column_types.get(col) == "categorical":
            n_unique = df[col].nunique(dropna=True)
            if 2 <= n_unique <= 8:
                suggestions.append(col)

    return suggestions


def suggest_outcome_columns(df: pd.DataFrame, column_types: dict[str, str]) -> list[str]:
    """Suggest likely outcome/target columns: name match or binary categorical."""
    suggestions: list[str] = []

    for col in df.columns:
        lower = col.lower().replace(" ", "_")
        if any(name in lower for name in LIKELY_OUTCOME_NAMES):
            suggestions.append(col)

    for col in df.columns:
        if col in suggestions:
            continue
        n_unique = df[col].nunique(dropna=True)
        if n_unique == 2:
            suggestions.append(col)

    return suggestions


def build_dataset_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Builds the 'Dataset Overview' block shown on the Fairness Lab page."""
    column_types = detect_column_types(df)
    missing_values = int(df.isna().sum().sum())

    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_values": missing_values,
        "column_names": list(df.columns),
        "column_types": column_types,
        "suggested_protected_attributes": suggest_protected_attributes(df, column_types),
        "suggested_outcome_columns": suggest_outcome_columns(df, column_types),
        "preview_rows": df.head(15).fillna("").astype(str).to_dict(orient="records"),
    }


def dataframe_from_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Rebuild a DataFrame from the JSON records the frontend sends back."""
    if not records:
        raise DatasetValidationError("No dataset rows were provided to analyze.")
    df = pd.DataFrame.from_records(records)
    return validate_dataframe(df)


def validate_analysis_inputs(
    df: pd.DataFrame,
    protected_attribute: str,
    outcome_column: str,
    positive_outcome: str,
) -> None:
    """Friendly, specific validation before running any fairness math."""
    if not protected_attribute:
        raise DatasetValidationError("Please select a protected attribute before running the test.")
    if not outcome_column:
        raise DatasetValidationError("Please select an outcome column before running the test.")
    if protected_attribute == outcome_column:
        raise DatasetValidationError("The protected attribute and outcome column must be different.")
    if protected_attribute not in df.columns:
        raise DatasetValidationError(f"Column '{protected_attribute}' was not found in the dataset.")
    if outcome_column not in df.columns:
        raise DatasetValidationError(f"Column '{outcome_column}' was not found in the dataset.")

    n_groups = df[protected_attribute].dropna().nunique()
    if n_groups < 2:
        raise DatasetValidationError(
            "We couldn't analyze this dataset. Please make sure your CSV "
            "contains at least two demographic groups in the selected "
            "protected attribute column."
        )

    outcome_values = set(df[outcome_column].astype(str).unique())
    if not positive_outcome:
        raise DatasetValidationError("Please select which outcome value counts as 'positive'.")
    if str(positive_outcome) not in outcome_values:
        raise DatasetValidationError(
            f"'{positive_outcome}' was not found in the outcome column. "
            f"Available values: {', '.join(sorted(outcome_values))}."
        )
