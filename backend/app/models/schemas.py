
from typing import Optional
from pydantic import BaseModel


class ProposalSections(BaseModel):
    title: str = ""
    abstract: str = ""
    objectives: str = ""
    methodology: str = ""
    budget: str = ""
    timeline: str = ""
    deliverables: str = ""


class EvaluationResponse(BaseModel):
    proposal_sections: ProposalSections
    novelty_result: Optional[dict] = None
    financial_result: Optional[dict] = None
    feasibility_result: Optional[dict] = None
    ml_result: Optional[dict] = None
    final_report: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    message: str