# Knee Osteoporosis AI

AI-assisted osteoporosis screening using knee X-ray images and structured patient clinical information, with optional evidence-grounded Clinical Support.

## Overview

Knee Osteoporosis AI is a local-first web application with two connected workflows:

### V1 Screening

```text
Patient
  ↓
Knee X-ray + clinical inputs
  ↓
DINOv2 classification
  ↓
Normal / Osteopenia / Osteoporosis
  ↓
T-score Random Forest
  ↓
Z-score Gradient Boosting
  ↓
Save analysis + image reference
  ↓
Analysis Result
```

### Phase 2 Clinical Support

```text
Saved analysis
  ↓
Automatic clinical evidence query
  ↓
BGE embedding
  ↓
PostgreSQL + pgvector
  ↓
3–5 relevant evidence chunks
  ↓
Grounded OpenRouter prompt
  ↓
Structured Clinical Support
  ↓
Clinical Support UI
```

Clinical Support is generated on demand and is not stored as a report.

> **Medical safety:** This is an AI-assisted screening/support application. It does not replace DXA/QUS measurement, professional diagnosis, clinical judgement, or treatment decisions.

---

## Technology Stack

### Frontend

- React
- TypeScript
- Vite
- React Router
- Axios
- CSS
- Oxlint

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- pydantic-settings
- SQLAlchemy
- PyTorch
- timm
- torchvision
- scikit-learn
- joblib
- Pillow
- Sentence Transformers
- pypdf
- pgvector
- httpx

### Database / Infrastructure

- PostgreSQL 15-compatible pgvector image
- pgAdmin
- Docker
- Docker Compose

### ML / RAG

- DINOv2 ViT-Small/14
- Random Forest for T-score estimation
- Gradient Boosting for Z-score estimation
- `BAAI/bge-base-en-v1.5` embeddings
- PostgreSQL/pgvector similarity search
- OpenRouter REST API with configurable `openrouter/free` initial model selector

> **As-built RAG note:** LlamaIndex dependencies are present from the Phase 2 specification, but the current verified runtime retrieval path uses direct SQLAlchemy + PostgreSQL/pgvector similarity search.

---

## Application Routes

```text
/                                      Home
/patients                              Patients
/patients/:patientId                   Patient Details
/patients/:patientId/analysis/new     New Analysis
/analyses/:analysisId                  Analysis Result
/analyses/:analysisId/clinical-support Clinical Support
```

---

## Requirements

Install:

- Docker Desktop
- Python 3.13+
- Node.js + npm
- Git

The trained ML model files are required locally.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Santhoshkumar0913/Knee-Osteoporosis-AI.git
cd Knee-Osteoporosis-AI
```

### 2. Create environment configuration

Copy `.env.example` to `.env` and set the local values.

```bash
cp .env.example .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Do not commit `.env`.

---

## PostgreSQL + pgAdmin

Start the Docker services:

```bash
docker compose up -d
```

Current host ports:

```text
PostgreSQL: localhost:5433
pgAdmin:    localhost:5050
```

The PostgreSQL container uses a named volume:

```text
postgres_data
```

Do not remove the volume during normal development.

### pgAdmin

Open:

```text
http://localhost:5050
```

Use the credentials configured in `.env`.

For a database connection from pgAdmin to the Docker PostgreSQL service, use the Docker service/container hostname rather than `localhost` from inside the pgAdmin container.

---

## ML Models

The trained model files are intentionally excluded from Git and must be placed manually in:

```text
backend/models/
```

Required files:

```text
backend/models/
├── dinov2_experiment2_best.pth
├── t_score_random_forest.joblib
├── z_score_gradient_boosting.joblib
└── model_metadata.json
```

The project does not retrain these models during application runtime.

---

## RAG Documents

The four approved RAG PDFs are local-only and are intentionally excluded from Git.

Create:

```text
rag_documents/
├── WHO_Fragility_Fractures.pdf
├── ISBMR_Osteoporosis_Adults.pdf
├── IMS_Postmenopausal_Osteoporosis.pdf
└── BHOF_Clinicians_Guide.pdf
```

Do not commit or push these PDFs.

---

## Backend Setup

Install backend dependencies:

```bash
cd backend
python -m pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/api/health
```

---

## RAG Ingestion

Run the manual ingestion command from the `backend` directory:

```bash
python -m app.rag.ingest
```

The pipeline is:

```text
PDF
→ pypdf extraction
→ chunking
→ metadata/checksum
→ BAAI/bge-base-en-v1.5
→ PostgreSQL/pgvector
```

Current configuration defaults include:

```text
RAG_TOP_K=5
CHUNK_SIZE=512
CHUNK_OVERLAP=50
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
```

The ingestion process is designed to skip unchanged documents using checksums and existing chunks.

---

## Frontend Setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

### Frontend checks

Build:

```bash
npm run build
```

Lint:

```bash
npm run lint
```

The repository currently has existing React hook lint warnings; these are non-blocking warnings from existing components.

---

## End-to-End Usage

### V1 analysis

1. Open `http://localhost:5173`.
2. Open Patients.
3. Create a patient or select an existing patient.
4. Open New Analysis.
5. Upload a knee X-ray.
6. Enter the required clinical fields.
7. Enter the Phase 2 context fields when available.
8. Check the automatically calculated BMI.
9. Click **Run Analysis**.
10. Review the Analysis Result page.

### Clinical Support

From a saved Analysis Result:

```text
View Clinical Support
```

The backend then:

```text
loads saved analysis
→ builds query
→ retrieves 3–5 evidence chunks
→ calls OpenRouter
→ parses response
→ returns structured support
```

The Clinical Support page displays the prediction, clinical context, evidence-grounded explanation, action sections, sources, grounding note, and medical disclaimer.

---

## API Endpoints

```text
GET    /api/health

POST   /api/patients
GET    /api/patients
GET    /api/patients/{patient_id}
DELETE /api/patients/{patient_id}

POST   /api/analyses
GET    /api/analyses/patient/{patient_id}
GET    /api/analyses/{analysis_id}
DELETE /api/analyses/{analysis_id}

POST   /api/analyses/{analysis_id}/clinical-support
```

---

## ML Details

### DINOv2

Current image model:

```text
DINOv2 ViT-Small/14
Input: 518 × 518
Feature dimension: 384
Classes: 3
```

Class mapping:

```text
1 → Normal
2 → Osteopenia
3 → Osteoporosis
```

### Clinical feature vector

The V1 clinical models use the fixed order:

```text
[Age, Gender, BMI, Weight, Height,
 Joint Pain, Number of Pregnancies, Class, Pregnancy_Missing]
```

Phase 2 fields are context/RAG fields only and do not alter this vector.

### T/Z ranges

Current empirical prediction-error margins:

```text
T-score: ±0.3715
Z-score: ±1.2232
```

These are not clinical confidence intervals and are not measured DXA/QUS results.

---

## RAG Source Set

The current approved corpus is:

```text
WHO — 2024
ISBMR — 2021
Indian Menopause Society — 2020
BHOF — 2022
```

The UI displays sources as:

```text
Organization — Year
```

Source metadata is stored internally with the document records, while the PDFs themselves remain local-only.

---

## Privacy and Security

Do not commit:

```text
.env
rag_documents/
patient images
.pth model weights
.joblib model weights
```

Never send the following to OpenRouter:

```text
Patient name
Patient ID
X-ray image
X-ray path
Filesystem paths
Internal database IDs
Database credentials
API keys
```

The OpenRouter key is backend-only.

The X-ray image is never sent to the external LLM provider.

---

## Project Structure

```text
Knee-Osteoporosis-AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── rag/
│   │   ├── schemas/
│   │   └── services/
│   ├── models/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
│
├── storage/
│   └── uploads/
│
├── docs/
│   ├── DEVIN-PHASE-2-PROMPT.md
│   └── PHASE-2-PRD.md
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── PRD.md
└── README.md
```

---

## Testing

### V1 regression

```text
patient
→ analysis
→ DINOv2
→ T-score/Z-score
→ save
→ history
```

### RAG

Verify:

- four PDFs are available locally;
- ingestion completes;
- metadata is present;
- vectors are stored;
- retrieval returns 3–5 chunks;
- repeated ingestion of unchanged documents does not duplicate them.

### Clinical Support

Verify:

- Analysis Result navigation works;
- saved context is loaded server-side;
- 3–5 chunks are retrieved;
- OpenRouter returns content;
- structured sections render;
- sources are derived from retrieved metadata;
- disclaimer is present;
- retry/regenerate works.

### Frontend

```bash
npm run build
npm run lint
```

---

## Current Verification Status

The latest project verification reported:

```text
V1 regression                  PASS
Clinical Support real flow    PASS
RAG verification               PASS
Security/privacy               PASS
Parser tests                   5/5 PASS
Frontend build                 PASS
Frontend lint                  PASS with existing warnings
Git diff check                  PASS
```

The verified environment also reported:

```text
5 retrieved chunks in the verified Clinical Support flow
488 indexed RAG chunks
No RAG PDFs tracked by Git
No sensitive patient/file values sent to OpenRouter
```

These are software verification results, not evidence of clinical validation.

---

## Known Limitations

- The current retrieval runtime uses direct SQLAlchemy + pgvector rather than LlamaIndex execution.
- XAI/Grad-CAM is not implemented.
- No validated probability-level multimodal fusion classifier is implemented.
- T-score/Z-score outputs are model estimates.
- `openrouter/free` may route to different upstream models and response formats.
- Existing frontend lint warnings remain.
- The application is intended for local research/development use rather than production clinical deployment.

---

## Documentation

The root `PRD.md` is the authoritative project specification and describes the current as-built architecture and workflow.

The documents under `docs/` are retained as historical development specifications for the V1/Phase 2 implementation process.

---

## License

This project is part of the Knee Osteoporosis AI research initiative.
