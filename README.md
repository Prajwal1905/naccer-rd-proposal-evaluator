# NaCCER R&D Proposal Auto-Evaluation System

An AI/ML-powered system that automatically evaluates coal-sector R&D research proposals submitted to NaCCER (CMPDI / Coal India Limited's R&D arm) across novelty, financial compliance, and feasibility/relevance — producing a reviewer-style evaluation report with explainable scores and actionable improvement suggestions.

## Problem

NaCCER manually reviews R&D proposals for novelty, financial compliance, and technical feasibility. This process is slow, subjective, and prone to inconsistency, with infrequent committee meetings causing long delays for applicants.

## Solution

This system ingests a proposal PDF and automatically runs four parallel/sequential evaluation checks, then aggregates them into a single, explainable, reviewer-ready report.

## Demo

[Watch Demo Video](https://drive.google.com/file/d/1FCGHgXGzDJAuesI-KZ2j8WAcL9hcU4uH/view?usp=sharing)

## Features

- **PDF Ingestion & Extraction** — parses proposal PDFs into structured sections (title, abstract, objectives, methodology, budget, timeline, deliverables) using heuristic heading detection with an LLM fallback for unstructured documents.
- **Section-Level Novelty Check (RAG)** — embeds the new proposal's sections and compares them against a reference database of past proposals using ChromaDB, flagging specific overlaps with similarity percentages and an LLM-generated explanation of whether the overlap is duplicative or a genuine extension.
- **Financial Compliance Check (LLM + Rules)** — extracts budget line items, pre-computes percentage-of-total figures in code (not LLM arithmetic) and compares them against official S&T funding guidelines retrieved via RAG, flagging violations by severity (HIGH/MEDIUM/LOW).
- **Feasibility/Relevance Scoring (LLM + RAG)** — scores the proposal's alignment with CIL/MoC priority research areas across four weighted dimensions: priority area match, operational specificity, technology-domain alignment, and differentiation from prior work.
- **ML Approval Prediction** — a Random Forest classifier trained on a synthetic, calibrated dataset of 800 historical proposals, predicting approval likelihood with SHAP-based per-instance explanations of the top contributing factors.
- **Aggregated Evaluation Report** — an LLM combines all four check results into a single reviewer-style narrative with an overall recommendation (Recommend / Recommend with Revisions / Not Recommended), key strengths, key concerns, and component scores.
- **Improvement Suggestions** — for proposals scoring below threshold on any dimension, the system generates specific, actionable suggestions for resubmission.
- **Trend/Gap Analysis Dashboard** — visualizes which research areas are historically over- or under-funded based on approval rates and total funding requested across the proposal dataset.
- **PDF Export** — evaluation reports can be downloaded as a formatted PDF.

## Architecture

```
User uploads Proposal PDF
        |
[PDF Extraction] -> structured sections (title, abstract, objectives, methodology, budget, timeline)
        |
[LangGraph Pipeline] (parallel execution)
  +--> Novelty Check (RAG against past proposals)        --+
  +--> Financial Check (LLM + S&T guideline RAG)          +--> ML Approval Prediction --> Aggregator
  +--> Feasibility/Relevance Check (priority-area RAG)   --+
        |
[React Dashboard] -> displays full evaluation report, trend analysis, PDF export
```

Novelty, financial, and feasibility checks run as independent parallel branches in the LangGraph state machine since none of them depend on each other's output. ML prediction depends on the financial and feasibility outputs (budget figures and matched priority area feed into its feature set), and the aggregator depends on all four prior results.

## Tech Stack

**Backend:** FastAPI, LangChain, LangGraph, ChromaDB, sentence-transformers, Groq API (Llama 3.3), scikit-learn, XGBoost, SHAP, pandas, pdfplumber

**Frontend:** React (Vite), Tailwind CSS, Axios, html2pdf.js

**Infrastructure:** Docker, docker-compose, nginx

## Project Structure

```
ProjectNew/
├── backend/
│   ├── app/
│   │   ├── pipeline/          # PDF extraction, novelty/financial/feasibility checks, ML prediction, aggregator, LangGraph wiring
│   │   ├── services/          # LLM client, vector store (ChromaDB), LLM-based extraction fallback
│   │   ├── routers/           # FastAPI routes (evaluate, trends)
│   │   ├── models/            # Pydantic API response schemas
│   │   └── main.py            # FastAPI app entrypoint
│   ├── data/
│   │   ├── reference_proposals/   # Synthetic past proposals dataset (novelty check reference)
│   │   ├── guidelines/            # S&T funding guidelines document (financial check reference)
│   │   ├── priority_areas/        # CIL/MoC priority research areas document (feasibility check reference)
│   │   └── ml_dataset/            # Synthetic historical proposals dataset + trained model
│   ├── notebooks/              # ML training notebook (EDA, model comparison, SHAP)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/              # UploadPage, ReportPage, TrendsPage
│   │   └── components/         # ScoreCard, NoveltySection, FinancialSection, FeasibilitySection, MLSection, SuggestionsSection
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A free Groq API key from [console.groq.com/keys](https://console.groq.com/keys)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Create .env from .env.example and add your GROQ_API_KEY
cp .env.example .env

# Build the ChromaDB vector store from reference data
python -m app.services.vector_store

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The backend must be running on port 8000.

### Docker (alternative)

```bash
docker-compose up --build
```

Open `http://localhost:5173`.

## Training the ML Model

The approval prediction model is trained in `backend/notebooks/train_approval_model.ipynb`. To regenerate the synthetic dataset and retrain:

```bash
cd backend/data/ml_dataset
python generate_dataset.py
```

Then run the notebook cells to retrain and save `approval_model.joblib`.

## API Endpoints

- `POST /evaluate/upload` — upload a proposal PDF, returns the full evaluation report
- `GET /trends/research-areas` — returns aggregated funding/approval trend data by research area
- `GET /health` — health check

Full interactive API documentation is available at `http://localhost:8000/docs` when the backend is running.

## Known Limitations

- Reference data (past proposals, guidelines, priority areas) is synthetic, generated for development and demonstration purposes. Real deployment would require replacing these with actual NaCCER reference documents.
- LLM-based extraction and scoring can have minor run-to-run variance in qualitative reasoning text, though numeric calculations (budget percentages, reconciliation checks) are computed deterministically in code rather than relying on LLM arithmetic.
- The ML approval prediction model is trained on a synthetic dataset calibrated to plausible patterns (priority area, budget ceiling, duration); it does not reflect real historical NaCCER approval data.

## License

This is a project for academic and demonstration purposes.
