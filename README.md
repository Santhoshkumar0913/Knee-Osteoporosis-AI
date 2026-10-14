# Knee Osteoporosis AI

An AI-assisted osteoporosis screening and clinical decision-support application. It analyzes knee X-rays, combines the predicted image class with patient clinical information for T-score and Z-score estimates, and can retrieve guidance from osteoporosis reference documents to generate Clinical Support through OpenRouter.

This is a completed local research and development prototype. It is not clinically validated or intended for production use.

## What the application does

- Manages patient records and analysis history.
- Classifies an uploaded knee X-ray as **Normal**, **Osteopenia**, or **Osteoporosis** using a fine-tuned DINOv2 ViT-S/14 model.
- Displays the predicted class and class probabilities.
- Estimates T-score with a Random Forest Regressor and Z-score with a Gradient Boosting Regressor.
- Retrieves relevant passages from osteoporosis references with BGE embeddings and PostgreSQL/pgvector when Clinical Support is requested.
- Sends permitted analysis context and retrieved evidence to an LLM through OpenRouter to produce structured Clinical Support.
- Provides an on-demand, experimental Grad-CAM visualization and an on-demand PDF report.

The image classifier and clinical regressors are separate models used in sequence. The predicted image class is one feature passed to the regressors; this is not a jointly trained image-and-clinical-data fusion classifier.

## Workflow

```text
Patient record + knee X-ray + clinical inputs
                  ↓
       DINOv2 image classification
                  ↓
   Predicted class + class probabilities
                  ↓
Predicted class + fixed clinical feature vector
          ↙                     ↘
 Random Forest                 Gradient Boosting
 T-score estimate              Z-score estimate
          ↘                     ↙
             Saved analysis
                  ↓ (when requested)
Analysis context → BGE query embedding → PostgreSQL/pgvector retrieval
                  ↓
 Retrieved passages + permitted context → OpenRouter LLM
                  ↓
      Structured Clinical Support with sources
```

## Machine learning models

### Knee X-ray classification

- **Architecture:** Fine-tuned DINOv2 ViT-S/14 (`vit_small_patch14_dinov2`).
- **Input processing:** RGB conversion, aspect-ratio-preserving resize and padding to 518 × 518, then ImageNet normalization.
- **Classes:** Normal, Osteopenia, Osteoporosis.
- **Output:** Predicted class, class probabilities, and confidence for the selected class.

### Clinical score estimates

The application constructs this fixed feature vector for both regressors:

```text
[Age, Gender, BMI, Weight, Height,
 Joint Pain, Number of Pregnancies, Predicted Class, Pregnancy_Missing]
```

- **Random Forest Regressor:** estimates T-score.
- **Gradient Boosting Regressor:** estimates Z-score.
- Menopausal status, smoking, alcohol use, previous fracture, and long-term steroid use are saved as additional context for Clinical Support; they are not inputs to these regressors.

The displayed score values and error-margin ranges are model estimates. They are not measured DXA/QUS results or clinical confidence intervals.

Model weights are not included in the repository. Place the required files in `backend/models/`:

```text
dinov2_experiment2_best.pth
t_score_random_forest.joblib
z_score_gradient_boosting.joblib
model_metadata.json
```

The application loads these trained models for inference; it does not train them at runtime.

## RAG and Clinical Support

When a user requests Clinical Support for a saved analysis, the backend builds a query from the analysis context, embeds it with the local `BAAI/bge-base-en-v1.5` model, and searches stored document embeddings in PostgreSQL with pgvector cosine similarity. The default retrieval limit is five passages. The retrieved passages and permitted clinical context are sent to the configured LLM through the OpenRouter chat completions API.

The LLM generates structured educational support, such as an explanation, items to discuss with a doctor, follow-up considerations, and treatment-related information. It does not classify the X-ray or calculate the score estimates. Retrieved source metadata is shown with the response. Clinical Support is generated on demand and is not stored as a permanent analysis record.

### Approved reference documents

The intended approved source set consists of these four PDFs:

- `WHO_Fragility_Fractures.pdf` — WHO fragility-fracture information.
- `ISBMR_Osteoporosis_Adults.pdf` — ISBMR position statement on adult osteoporosis diagnosis and treatment.
- `IMS_Postmenopausal_Osteoporosis.pdf` — Indian Menopause Society guidance on postmenopausal osteoporosis.
- `BHOF_Clinicians_Guide.pdf` — BHOF clinician guidance on osteoporosis prevention and treatment.

Keep the reference PDFs locally in `rag_documents/`; they are not application code. **The current ingestion script processes every `*.pdf` in that directory.** To keep the indexed corpus limited to the approved set, make sure only these four PDFs are present there before running ingestion. The script has source metadata for these four documents; other PDFs may be ingested without that approved metadata.

Ingestion extracts PDF text with pypdf, chunks it using the configured character size and overlap, generates BGE embeddings, and stores the document and chunk metadata in PostgreSQL/pgvector. Unchanged documents are skipped using checksums.

Default settings:

```text
RAG_TOP_K=5
CHUNK_SIZE=512 characters
CHUNK_OVERLAP=50 characters
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
```

The runtime retrieval implementation uses SQLAlchemy and direct PostgreSQL/pgvector similarity search. LlamaIndex packages may be present in the dependency list, but are not used by the current retrieval path.

## Explainability and PDF reports

- **Grad-CAM:** Generated on demand for a saved X-ray. It is experimental, intended for research/explainability, and is not confirmed anatomical disease localization or evidence for Clinical Support. It is excluded from the PDF report.
- **PDF report:** Generated in memory and streamed for download. It contains saved analysis information, the original X-ray, and the Clinical Support response currently displayed in the interface. The application does not archive the generated PDF.

## Technology

| Area | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite, React Router, Axios, CSS, Oxlint |
| Backend API | Python, FastAPI, Uvicorn, Pydantic, SQLAlchemy |
| Machine learning | PyTorch, timm, torchvision, scikit-learn, joblib |
| RAG and documents | Sentence Transformers, BGE, pypdf, PostgreSQL, pgvector |
| LLM connection | OpenRouter REST API using httpx |
| Local infrastructure | Docker Compose, PostgreSQL/pgvector, pgAdmin |

Docker Compose runs PostgreSQL and pgAdmin. The frontend and backend are started separately for local development.

## Requirements

- Docker Desktop with Docker Compose
- Python 3.13 or newer
- Node.js and npm
- The trained model files listed above
- An OpenRouter API key for live LLM-generated Clinical Support
- The four approved RAG PDFs for document ingestion

## Local setup

### 1. Configure environment variables

From the project root, copy `.env.example` to `.env` and set appropriate local credentials and the OpenRouter API key.

PowerShell:

```powershell
Copy-Item .env.example .env
```

Do not commit `.env` or share its secrets.

### 2. Start PostgreSQL and pgAdmin

```bash
docker compose up -d
```

Default host addresses from `.env.example`:

- PostgreSQL: `localhost:5433`
- pgAdmin: `http://localhost:5050`

The database uses a named Docker volume (`postgres_data`) so data persists across container restarts. When connecting from pgAdmin inside Docker, use the PostgreSQL service name `postgres` and container port `5432`.

### 3. Install and start the backend

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`; its health endpoint is `http://localhost:8000/api/health`.

### 4. Ingest RAG documents

Ensure the approved PDFs are present in `rag_documents/`, then run this from the `backend/` directory:

```bash
python -m app.rag.ingest
```

### 5. Install and start the frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Using the application

1. Open **Patients** and create a patient record or select an existing one.
2. Start a new analysis, upload a supported knee X-ray, and enter the required clinical information.
3. Submit the analysis and review the predicted class, class probabilities, and model-estimated scores.
4. Optionally request the Grad-CAM visualization or open Clinical Support.
5. Download a PDF report from the Clinical Support page when a response is displayed.

## Application routes

| Route | Page |
|---|---|
| `/` | Home |
| `/patients` | Patient list |
| `/patients/:patientId` | Patient details and analysis history |
| `/patients/:patientId/analysis/new` | New analysis |
| `/analyses/:analysisId` | Analysis result |
| `/analyses/:analysisId/clinical-support` | Clinical Support |

## API endpoints

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
GET    /api/analyses/{analysis_id}/image
GET    /api/analyses/{analysis_id}/xai
POST   /api/analyses/{analysis_id}/clinical-support/pdf
```

## Privacy and safety

- The OpenRouter request contains permitted clinical context and retrieved document passages. Patient name, patient ID, image bytes, image path, internal database IDs, filesystem paths, API keys, and database credentials are not included in the LLM context.
- The knee X-ray is processed and stored by the local application; it is not sent to OpenRouter.
- The PDF report contains patient-identifying details and should be handled accordingly.
- The application has no authentication or production deployment controls and is intended for local research/development use.
- This application is not clinically validated. Its outputs do not replace DXA/QUS testing, professional diagnosis, or clinical judgment, and must not be used as the sole basis for treatment decisions.

## Development checks

From `frontend/`:

```bash
npm run build
npm run lint
```

Backend tests are located in `backend/tests/` and can be run from `backend/` with the project's Python test environment.

## Project structure

```text
Knee-Osteoporosis-AI/
├── backend/
│   ├── app/                 # API, database, ML, RAG, and report services
│   ├── models/              # Locally supplied trained model files
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/                 # React application
│   └── package.json
├── rag_documents/           # Local RAG reference PDFs
├── storage/uploads/         # Uploaded X-ray images
├── docker-compose.yml
├── .env.example
└── README.md
```

## Completion and limitations

The defined application scope is implemented: patient and analysis management, knee X-ray classification, clinical score estimates, RAG-based OpenRouter Clinical Support, original X-ray display, experimental Grad-CAM, and on-demand PDF reporting. Completion refers to these software workflows; it does not imply clinical validation, production readiness, or medical-device approval.

Known limitations include the experimental nature of Grad-CAM, the estimate-only nature of T-score and Z-score, the variable upstream model routing behind `openrouter/free`, and the need to keep the RAG PDF directory limited to the intended approved corpus before ingestion.


