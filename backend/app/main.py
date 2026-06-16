
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import evaluate
from app.models.schemas import HealthResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

settings = get_settings()

app = FastAPI(
    title="NaCCER R&D Proposal Auto-Evaluation System",
    description="AI/ML-based automatic evaluation of coal-sector R&D proposals.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evaluate.router)


@app.get("/", response_model=HealthResponse)
def root():
    return HealthResponse(status="ok", message="NaCCER Proposal Evaluation API is running.")


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", message="Healthy")