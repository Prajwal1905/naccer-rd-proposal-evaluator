
import logging
import os

import joblib
import numpy as np
import pandas as pd
import shap
from typing import TypedDict, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

CATEGORICAL_FEATURES = ["research_area", "institution_type"]
NUMERIC_FEATURES = ["requested_amount_lakhs", "duration_months", "num_objectives"]

VALID_RESEARCH_AREAS = [
    "Mine Safety",
    "Environmental Rehabilitation",
    "Automation in Mining",
    "Underground Coal Gasification",
    "Coal Bed Methane",
    "Coal Quality Assessment",
    "Mine Waste Utilization",
    "General IT Infrastructure",
]
VALID_INSTITUTION_TYPES = ["academic", "cil_psu", "industry"]

_model = None
_explainer = None


class ApprovalFeatures(TypedDict):
    research_area: str
    institution_type: str
    requested_amount_lakhs: Optional[float]
    duration_months: Optional[int]
    num_objectives: int


class TopFactor(TypedDict):
    feature: str
    shap_value: float
    direction: str  


class MLPredictionResult(TypedDict):
    approval_probability: float
    predicted_label: str  
    top_factors: list[TopFactor]
    input_features: dict
    warnings: list[str]


def _load_model():
    global _model, _explainer
    if _model is None:
        settings = get_settings()
        if not os.path.exists(settings.ml_model_path):
            raise FileNotFoundError(
                f"Model file not found at {settings.ml_model_path}. "
                "Run the training notebook (notebooks/train_approval_model.ipynb) first."
            )
        _model = joblib.load(settings.ml_model_path)
        _explainer = shap.TreeExplainer(_model.named_steps["classifier"])
    return _model, _explainer


def _humanize_feature_name(raw_name: str) -> str:
    
    name = raw_name
    for prefix in ("cat__", "remainder__"):
        if name.startswith(prefix):
            name = name[len(prefix):]
    name = name.replace("_", " ")
    return name.strip()


def run_ml_prediction(features: ApprovalFeatures) -> MLPredictionResult:
    warnings: list[str] = []

    # Validate / clean inputs with sensible fallbacks
    research_area = features.get("research_area") or "General IT Infrastructure"
    if research_area not in VALID_RESEARCH_AREAS:
        warnings.append(
            f"Research area '{research_area}' not recognized; defaulting to "
            f"'General IT Infrastructure' for prediction purposes."
        )
        research_area = "General IT Infrastructure"

    institution_type = features.get("institution_type") or "unknown"
    if institution_type not in VALID_INSTITUTION_TYPES:
        warnings.append(
            f"Institution type '{institution_type}' not recognized; defaulting to 'academic'."
        )
        institution_type = "academic"

    requested_amount_lakhs = features.get("requested_amount_lakhs")
    if requested_amount_lakhs is None:
        warnings.append("Requested amount (TPC) could not be determined; using dataset median (120 Lakhs).")
        requested_amount_lakhs = 120.0

    duration_months = features.get("duration_months")
    if duration_months is None:
        warnings.append("Project duration could not be determined; using default of 24 months.")
        duration_months = 24

    num_objectives = features.get("num_objectives")
    if not num_objectives or num_objectives <= 0:
        warnings.append("Number of objectives could not be determined; using default of 4.")
        num_objectives = 4

    input_df = pd.DataFrame([{
        "research_area": research_area,
        "institution_type": institution_type,
        "requested_amount_lakhs": float(requested_amount_lakhs),
        "duration_months": int(duration_months),
        "num_objectives": int(num_objectives),
    }])

    model, explainer = _load_model()

    proba = model.predict_proba(input_df)[0, 1]
    predicted_label = "Likely Approved" if proba >= 0.5 else "Likely Rejected"

    # SHAP explanation for this specific instance
    transformed = model.named_steps["preprocessor"].transform(input_df)
    feature_names = model.named_steps["preprocessor"].get_feature_names_out()

    shap_values = explainer.shap_values(transformed)
    # shape: (1, n_features, n_classes) -> class 1
    instance_shap = shap_values[0, :, 1]

    factor_pairs = list(zip(feature_names, instance_shap))
    factor_pairs.sort(key=lambda x: abs(x[1]), reverse=True)

    top_factors: list[TopFactor] = []
    for raw_name, value in factor_pairs[:5]:
        # Skip near-zero contributions (e.g. one-hot columns not relevant to this instance)
        if abs(value) < 1e-4:
            continue
        top_factors.append({
            "feature": _humanize_feature_name(raw_name),
            "shap_value": round(float(value), 4),
            "direction": "increases" if value > 0 else "decreases",
        })

    return {
        "approval_probability": round(float(proba), 4),
        "predicted_label": predicted_label,
        "top_factors": top_factors,
        "input_features": input_df.iloc[0].to_dict(),
        "warnings": warnings,
    }