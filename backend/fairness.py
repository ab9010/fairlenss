"""
fairness.py
------------
The core fairness analysis engine for FairLens.

Every function here performs a real calculation on the data passed to it.
Nothing is hard-coded — the numbers you see on the results dashboard are
produced by this file.

The metrics implemented are simplified, educational versions of concepts
used in real fairness research (e.g. Fairlearn, Aequitas). They are meant
to teach the underlying ideas, not to serve as a certified fairness audit.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder


# --------------------------------------------------------------------------
# 1. Selection rates
# --------------------------------------------------------------------------

def calculate_selection_rates(
    df: pd.DataFrame,
    protected_attribute: str,
    outcome_column: str,
    positive_outcome: str,
) -> dict[str, float]:
    """
    For each group inside the protected attribute (e.g. Male / Female),
    calculate what fraction of that group received the positive outcome
    (e.g. was Approved).

    This is the "selection rate" — the foundation every other fairness
    metric here is built on.
    """
    rates: dict[str, float] = {}
    groups = df[protected_attribute].dropna().unique()

    for group in groups:
        subset = df[df[protected_attribute] == group]
        if len(subset) == 0:
            continue
        positive_count = (subset[outcome_column].astype(str) == str(positive_outcome)).sum()
        rate = positive_count / len(subset)
        rates[str(group)] = round(float(rate), 4)

    return rates


def calculate_group_counts(df: pd.DataFrame, protected_attribute: str) -> dict[str, int]:
    """How many records fall into each demographic group."""
    counts = df[protected_attribute].value_counts().to_dict()
    return {str(k): int(v) for k, v in counts.items()}


def calculate_outcome_distribution(
    df: pd.DataFrame,
    protected_attribute: str,
    outcome_column: str,
) -> dict[str, dict[str, int]]:
    """Breakdown of every outcome value (Yes/No, Approved/Rejected...) per group."""
    result: dict[str, dict[str, int]] = {}
    for group in df[protected_attribute].dropna().unique():
        subset = df[df[protected_attribute] == group]
        counts = subset[outcome_column].astype(str).value_counts().to_dict()
        result[str(group)] = {str(k): int(v) for k, v in counts.items()}
    return result


# --------------------------------------------------------------------------
# 2. Demographic parity
# --------------------------------------------------------------------------

def calculate_demographic_parity(rates: dict[str, float]) -> dict[str, Any]:
    """
    Demographic parity asks: "do all groups get the positive outcome at
    roughly the same rate?"

    We report the parity ratio (lowest rate / highest rate — 1.0 is perfect
    parity) and the raw percentage-point difference between the best and
    worst served groups.
    """
    if len(rates) < 2:
        return {"ratio": 1.0, "difference": 0.0, "best_group": None, "worst_group": None}

    best_group = max(rates, key=rates.get)
    worst_group = min(rates, key=rates.get)
    best_rate = rates[best_group]
    worst_rate = rates[worst_group]

    ratio = worst_rate / best_rate if best_rate > 0 else 0.0
    difference = best_rate - worst_rate

    return {
        "ratio": round(float(ratio), 4),
        "difference": round(float(difference), 4),
        "best_group": best_group,
        "worst_group": worst_group,
        "best_rate": best_rate,
        "worst_rate": worst_rate,
    }


# --------------------------------------------------------------------------
# 3. Disparate impact
# --------------------------------------------------------------------------

def calculate_disparate_impact(rates: dict[str, float]) -> float:
    """
    The classic "80% rule" metric used in employment discrimination law
    (US EEOC guidelines): the ratio of the least-favoured group's selection
    rate to the most-favoured group's. A value below 0.8 is traditionally
    treated as a red flag.
    """
    if len(rates) < 2:
        return 1.0
    best_rate = max(rates.values())
    worst_rate = min(rates.values())
    if best_rate == 0:
        return 0.0
    return round(float(worst_rate / best_rate), 4)


# --------------------------------------------------------------------------
# 4. Equal opportunity (via a simple trained classifier)
# --------------------------------------------------------------------------

def calculate_equal_opportunity(
    df: pd.DataFrame,
    protected_attribute: str,
    outcome_column: str,
    positive_outcome: str,
) -> dict[str, Any]:
    """
    Equal opportunity compares the TRUE POSITIVE RATE between groups: among
    people who *actually* deserved the positive outcome, does the model
    correctly identify them at the same rate for every group?

    Since this prototype does not receive a pre-trained production model,
    we train a small, transparent logistic regression on the non-protected
    features to stand in for "the model", then measure its true positive
    rate per group. This keeps the metric real and data-driven rather than
    hard-coded.
    """
    work = df.copy()

    y = (work[outcome_column].astype(str) == str(positive_outcome)).astype(int)

    feature_cols = [
        c for c in work.columns
        if c not in (outcome_column, protected_attribute)
    ]

    if not feature_cols or y.nunique() < 2:
        return {"values": {}, "difference": 0.0, "note": "Not enough data to train a comparison model."}

    X = work[feature_cols].copy()

    # Encode any categorical/text columns numerically so LogisticRegression can use them
    for col in X.columns:
        if pd.api.types.is_numeric_dtype(X[col]):
            numeric_col = pd.to_numeric(X[col], errors="coerce")
            fill_value = float(numeric_col.median()) if numeric_col.notna().any() else 0.0
            X[col] = numeric_col.fillna(fill_value)
        else:
            X[col] = X[col].astype(str).fillna("missing")
            X[col] = LabelEncoder().fit_transform(X[col])

    try:
        model = LogisticRegression(max_iter=1000)
        model.fit(X, y)
        predictions = model.predict(X)
    except Exception:
        return {"values": {}, "difference": 0.0, "note": "Model could not be trained on this dataset."}

    work["_actual"] = y.values
    work["_predicted"] = predictions

    tpr_by_group: dict[str, float] = {}
    for group in work[protected_attribute].dropna().unique():
        subset = work[work[protected_attribute] == group]
        actually_positive = subset[subset["_actual"] == 1]
        if len(actually_positive) == 0:
            continue
        true_positives = (actually_positive["_predicted"] == 1).sum()
        tpr = true_positives / len(actually_positive)
        tpr_by_group[str(group)] = round(float(tpr), 4)

    if len(tpr_by_group) < 2:
        return {"values": tpr_by_group, "difference": 0.0, "note": None}

    difference = max(tpr_by_group.values()) - min(tpr_by_group.values())

    return {"values": tpr_by_group, "difference": round(float(difference), 4), "note": None}


# --------------------------------------------------------------------------
# 5. Fairness score
# --------------------------------------------------------------------------

def calculate_fairness_score(
    demographic_parity_difference: float,
    disparate_impact: float,
    equal_opportunity_difference: float,
) -> int:
    """
    Combines the three metrics above into a single 0-100 "Fairness Score".

    This is a transparent, adjustable educational formula — NOT a
    scientific or regulatory standard. Each percentage-point of measured
    disparity subtracts points from a perfect 100, weighted so that
    demographic parity and disparate impact (which speak directly to
    selection-rate fairness) matter most, and the equal opportunity gap
    contributes a smaller share. The weights below can be changed at any
    time:

        - 0.8x weight on the demographic parity difference
        - 0.6x weight on how far disparate impact falls below 1.0
        - 0.3x weight on the equal opportunity difference
    """
    score = 100.0

    score -= min(demographic_parity_difference, 1.0) * 100 * 0.8
    score -= max(0.0, (1.0 - disparate_impact)) * 100 * 0.6
    score -= min(equal_opportunity_difference, 1.0) * 100 * 0.3

    score = max(0, min(100, round(score)))
    return int(score)


def determine_bias_level(score: int) -> dict[str, str]:
    """Translate the numeric score into a plain-language severity label."""
    if score >= 80:
        return {"level": "Relatively Fair", "tone": "good"}
    if score >= 60:
        return {"level": "Moderate Disparity", "tone": "moderate"}
    if score >= 40:
        return {"level": "High Disparity", "tone": "high"}
    return {"level": "Severe Disparity", "tone": "severe"}


# --------------------------------------------------------------------------
# 6. Recommendations
# --------------------------------------------------------------------------

def generate_recommendations(
    score: int,
    demographic_parity: dict[str, Any],
    disparate_impact: float,
    equal_opportunity: dict[str, Any],
) -> list[dict[str, str]]:
    """Builds a list of recommendation cards tailored to what was actually found."""
    recs: list[dict[str, str]] = []

    if score < 80:
        recs.append({
            "title": "Review group representation",
            "text": "Check whether every demographic group is represented in "
                     "the training data in proportions that reflect the real "
                     "population you intend to serve. Under-representation "
                     "often shows up later as uneven outcomes.",
        })

    if demographic_parity.get("difference", 0) >= 0.10:
        worst = demographic_parity.get("worst_group")
        recs.append({
            "title": f"Investigate outcomes for {worst}",
            "text": f"The '{worst}' group has a noticeably lower positive-outcome "
                     "rate than others. Look for historical patterns in the data "
                     "that may be driving this gap rather than assuming the "
                     "underlying model is simply 'correct'.",
        })

    if disparate_impact < 0.8:
        recs.append({
            "title": "Disparate impact falls below the 80% guideline",
            "text": "This ratio is commonly used as an early warning threshold "
                     "in employment and lending contexts. A ratio under 0.8 "
                     "typically warrants a closer legal and ethical review.",
        })

    eo_diff = equal_opportunity.get("difference", 0)
    if eo_diff and eo_diff >= 0.10:
        recs.append({
            "title": "Evaluate the model separately per group",
            "text": "The comparison model correctly identifies deserving "
                     "candidates at different rates across groups. Consider "
                     "evaluating accuracy, precision and recall separately "
                     "for each group rather than relying on one overall score.",
        })

    recs.append({
        "title": "Consider fairness-aware techniques",
        "text": "Pre-processing (re-balancing training data), in-processing "
                 "(fairness constraints during training) and post-processing "
                 "(adjusting decision thresholds per group) are three broad "
                 "families of mitigation techniques worth exploring.",
    })

    recs.append({
        "title": "Re-test after making changes",
        "text": "Fairness is not a one-time checkbox. Re-run this analysis "
                 "whenever the dataset, features, or model change, and track "
                 "the fairness score over time alongside accuracy.",
    })

    return recs[:6]


# --------------------------------------------------------------------------
# 7. Before / after mitigation simulation
# --------------------------------------------------------------------------

def simulate_mitigation(rates: dict[str, float]) -> dict[str, Any]:
    """
    A simplified, transparent EDUCATIONAL simulation of what a fairness-aware
    post-processing step (adjusting decision thresholds per group) could look
    like. This does NOT retrain a real model — it mathematically nudges each
    group's selection rate toward the mean, weighted so the most disadvantaged
    group is lifted the most. This is a common simplified illustration of
    threshold-adjustment mitigation strategies.
    """
    if len(rates) < 2:
        return {"before": rates, "after": rates, "before_difference": 0.0, "after_difference": 0.0}

    mean_rate = sum(rates.values()) / len(rates)
    after: dict[str, float] = {}

    for group, rate in rates.items():
        # Move 80% of the way toward the mean rate — simulates a fairness constraint
        adjusted = rate + 0.80 * (mean_rate - rate)
        after[group] = round(float(max(0.0, min(1.0, adjusted))), 4)

    before_diff = max(rates.values()) - min(rates.values())
    after_diff = max(after.values()) - min(after.values())

    return {
        "before": rates,
        "after": after,
        "before_difference": round(float(before_diff), 4),
        "after_difference": round(float(after_diff), 4),
    }


# --------------------------------------------------------------------------
# 8. Bias simulator (standalone, slider-driven)
# --------------------------------------------------------------------------

def simulate_bias_scenario(group_a_rate: float, group_b_rate: float) -> dict[str, Any]:
    """Powers the interactive Bias Simulator sliders on the frontend."""
    group_a_rate = max(0.0, min(1.0, group_a_rate))
    group_b_rate = max(0.0, min(1.0, group_b_rate))

    difference = abs(group_a_rate - group_b_rate)
    higher = max(group_a_rate, group_b_rate)
    lower = min(group_a_rate, group_b_rate)
    disparate_impact = round(lower / higher, 4) if higher > 0 else 1.0

    # Reuse the same scoring approach as the main engine, treating this as
    # a two-metric scenario (no equal-opportunity data available here).
    score = 100.0
    score -= difference * 100 * 0.6
    score -= max(0.0, (1.0 - disparate_impact)) * 100 * 0.4
    score = int(max(0, min(100, round(score))))

    status = determine_bias_level(score)

    return {
        "difference": round(float(difference), 4),
        "disparate_impact": disparate_impact,
        "score": score,
        "status": status["level"],
        "tone": status["tone"],
    }
