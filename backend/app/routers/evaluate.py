
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
MIN_TEXT_LENGTH = 200  


@router.post("/upload", response_model=EvaluationResponse)
async def evaluate_proposal(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was uploaded. Please select a PDF file.")

    if not file.filename.lower().endswith(ALLOWED_EXTENSION):
        raise HTTPException(
            status_code=400,
            detail=f"'{file.filename}' is not a PDF. Please upload a proposal in PDF format."
        )

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({size_mb:.1f} MB) exceeds the {MAX_FILE_SIZE_MB} MB limit. "
                    "Please upload a smaller file."
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        logger.info("Extracting proposal from %s (%.2f MB)", file.filename, size_mb)

        try:
            extracted = extract_proposal(tmp_path)
        except ValueError as exc:
            
            raise HTTPException(
                status_code=422,
                detail="No readable text could be extracted from this PDF. It may be a "
                        "scanned document or image-based file. Please upload a text-based "
                        "PDF, or run OCR on the document before uploading."
            ) from exc

        proposal_sections = proposal_to_dict(extracted)

       
        total_extracted_length = sum(
            len(proposal_sections.get(key, "")) for key in
            ["abstract", "objectives", "methodology", "budget"]
        )
        if total_extracted_length < MIN_TEXT_LENGTH:
            raise HTTPException(
                status_code=422,
                detail="This PDF does not appear to contain a recognizable proposal structure "
                        "(abstract, objectives, methodology, or budget sections could not be found "
                        "or were too short). Please check the document and try again."
            )

        logger.info("Running evaluation pipeline...")
        try:
            final_state = run_pipeline(proposal_sections)
        except Exception as exc:
            logger.exception("Pipeline execution failed")
            raise HTTPException(
                status_code=502,
                detail="The evaluation pipeline encountered an error, possibly due to an AI "
                        "service issue (rate limit or timeout). Please try again in a moment."
            ) from exc

        return EvaluationResponse(
            proposal_sections=proposal_sections,
            novelty_result=final_state.get("novelty_result"),
            financial_result=final_state.get("financial_result"),
            feasibility_result=final_state.get("feasibility_result"),
            ml_result=final_state.get("ml_result"),
            final_report=final_state.get("final_report"),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during evaluation")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the proposal. Please try again "
                    "or contact support if the issue persists."
        ) from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)