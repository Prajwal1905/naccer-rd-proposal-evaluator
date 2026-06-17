
import json
import logging
import os

import pandas as pd
from fastapi import APIRouter, HTTPException

from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("/research-areas")
def get_research_area_trends():
    settings = get_settings()

  
    past_proposals_path = os.path.join(settings.reference_proposals_dir, "past_proposals.json")
    if not os.path.exists(past_proposals_path):
        raise HTTPException(status_code=404, detail="Past proposals reference data not found.")

    with open(past_proposals_path, "r", encoding="utf-8") as f:
        past_proposals = json.load(f)

    past_df = pd.DataFrame(past_proposals)

    
    historical_csv_path = os.path.join(settings.ml_dataset_dir, "historical_proposals.csv")
    if not os.path.exists(historical_csv_path):
        raise HTTPException(status_code=404, detail="Historical proposals dataset not found.")

    hist_df = pd.read_csv(historical_csv_path)

    past_summary = (
        past_df.groupby("research_area")
        .agg(
            proposal_count=("id", "count"),
            approved_count=("approved", "sum"),
        )
        .reset_index()
    )
    past_summary["approval_rate_percent"] = round(
        (past_summary["approved_count"] / past_summary["proposal_count"]) * 100, 1
    )

    
    hist_summary = (
        hist_df.groupby("research_area")
        .agg(
            total_proposals=("approved", "count"),
            approved_proposals=("approved", "sum"),
            avg_requested_amount_lakhs=("requested_amount_lakhs", "mean"),
            total_requested_amount_lakhs=("requested_amount_lakhs", "sum"),
            avg_duration_months=("duration_months", "mean"),
        )
        .reset_index()
    )
    hist_summary["approval_rate_percent"] = round(
        (hist_summary["approved_proposals"] / hist_summary["total_proposals"]) * 100, 1
    )
    hist_summary["avg_requested_amount_lakhs"] = round(hist_summary["avg_requested_amount_lakhs"], 1)
    hist_summary["total_requested_amount_lakhs"] = round(hist_summary["total_requested_amount_lakhs"], 1)
    hist_summary["avg_duration_months"] = round(hist_summary["avg_duration_months"], 1)

    # Identify over/under-funded areas relative to the mean approval rate
    mean_approval_rate = hist_summary["approval_rate_percent"].mean()
    hist_summary["funding_status"] = hist_summary["approval_rate_percent"].apply(
        lambda x: "over-funded" if x > mean_approval_rate + 5
        else "under-funded" if x < mean_approval_rate - 5
        else "average"
    )

    return {
        "reference_proposals_summary": past_summary.to_dict(orient="records"),
        "historical_dataset_summary": hist_summary.sort_values(
            "approval_rate_percent", ascending=False
        ).to_dict(orient="records"),
        "mean_approval_rate_percent": round(mean_approval_rate, 1),
        "total_historical_proposals": int(len(hist_df)),
    }