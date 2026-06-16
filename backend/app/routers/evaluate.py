
import logging
import os
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.pipeline.pdf_extraction import extract_proposal, proposal_to_dict
from app.pipeline.graph import run_pipeline
from app.models.schemas import EvaluationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluate", tags=["evaluate"])

ALLOWED_EXTENSION = ".pdf"
MAX_FILE_SIZE_MB = 20


@router.post("/upload", response_model=EvaluationResponse)
async def evaluate_proposal(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(ALLOWED_EXTENSION):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        logger.info("Extracting proposal from %s (%.2f MB)", file.filename, size_mb)
        extracted = extract_proposal(tmp_path)
        proposal_sections = proposal_to_dict(extracted)

        logger.info("Running evaluation pipeline...")
        final_state = run_pipeline(proposal_sections)

        return EvaluationResponse(
            proposal_sections=proposal_sections,
            novelty_result=final_state.get("novelty_result"),
            financial_result=final_state.get("financial_result"),
            feasibility_result=final_state.get("feasibility_result"),
            ml_result=final_state.get("ml_result"),
            final_report=final_state.get("final_report"),
        )
    except ValueError as exc:
        
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Evaluation pipeline failed")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)