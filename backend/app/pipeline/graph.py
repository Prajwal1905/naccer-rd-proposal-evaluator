
import logging
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END, START

from app.pipeline.novelty_check import run_novelty_check, NoveltyResult
from app.pipeline.financial_check import run_financial_check, FinancialCheckResult
from app.pipeline.feasibility_check import run_feasibility_check, FeasibilityResult
from app.pipeline.ml_prediction import run_ml_prediction, MLPredictionResult
from app.pipeline.feature_mapping import build_approval_features
from app.pipeline.aggregator import run_aggregator, AggregatedReport

logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    proposal_sections: dict
    novelty_result: Optional[NoveltyResult]
    financial_result: Optional[FinancialCheckResult]
    feasibility_result: Optional[FeasibilityResult]
    ml_result: Optional[MLPredictionResult]
    final_report: Optional[AggregatedReport]


def novelty_node(state: PipelineState) -> dict:
    logger.info("Running novelty check...")
    result = run_novelty_check(state["proposal_sections"])
    return {"novelty_result": result}


def financial_node(state: PipelineState) -> dict:
    logger.info("Running financial compliance check...")
    result = run_financial_check(state["proposal_sections"])
    return {"financial_result": result}


def feasibility_node(state: PipelineState) -> dict:
    logger.info("Running feasibility/relevance check...")
    result = run_feasibility_check(state["proposal_sections"])
    return {"feasibility_result": result}


def ml_prediction_node(state: PipelineState) -> dict:
    logger.info("Running ML approval prediction...")
    extracted_budget = (state.get("financial_result") or {}).get("extracted_budget", {})
    feasibility_result = state.get("feasibility_result") or {}

    features = build_approval_features(
        proposal_sections=state["proposal_sections"],
        feasibility_result=feasibility_result,
        extracted_budget=extracted_budget,
    )

    try:
        result = run_ml_prediction(features)
    except FileNotFoundError as exc:
        logger.error("ML model not found: %s", exc)
        result = {
            "approval_probability": 0.0,
            "predicted_label": "Unavailable",
            "top_factors": [],
            "input_features": features,
            "warnings": [str(exc)],
        }

    return {"ml_result": result}


def aggregator_node(state: PipelineState) -> dict:
    logger.info("Running aggregator...")
    report = run_aggregator(
        proposal_sections=state["proposal_sections"],
        novelty_result=state.get("novelty_result"),
        financial_result=state.get("financial_result"),
        feasibility_result=state.get("feasibility_result"),
        ml_result=state.get("ml_result"),
    )
    return {"final_report": report}


def build_pipeline_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("novelty_check", novelty_node)
    graph.add_node("financial_check", financial_node)
    graph.add_node("feasibility_check", feasibility_node)
    graph.add_node("ml_prediction", ml_prediction_node)
    graph.add_node("aggregator", aggregator_node)

    graph.add_edge(START, "novelty_check")
    graph.add_edge(START, "financial_check")
    graph.add_edge(START, "feasibility_check")

    graph.add_edge("financial_check", "ml_prediction")
    graph.add_edge("feasibility_check", "ml_prediction")

    
    graph.add_edge("novelty_check", "aggregator")
    graph.add_edge("ml_prediction", "aggregator")

    graph.add_edge("aggregator", END)

    return graph.compile()


def run_pipeline(proposal_sections: dict) -> PipelineState:
    
    app = build_pipeline_graph()
    initial_state: PipelineState = {
        "proposal_sections": proposal_sections,
        "novelty_result": None,
        "financial_result": None,
        "feasibility_result": None,
        "ml_result": None,
        "final_report": None,
    }
    final_state = app.invoke(initial_state)
    return final_state