# PRD — Knee Osteoporosis AI

## Unified As-Built Product Requirements Document

**Full project title:** Adaptive Multimodal AI and LLM Framework for Early Osteoporosis Screening and Evidence-Based Clinical Decision Support using Knee X-ray Images  
**Product:** Knee Osteoporosis AI  
**Repository:** `Santhoshkumar0913/Knee-Osteoporosis-AI`  
**Current development branch:** `feature/rag-llm`  
**Document type:** Unified V1 + Phase 2 as-built Product Requirements Document  
**Status:** Current implementation specification

> This document is the single project PRD. It consolidates the original V1 PRD, the Phase 2 RAG/LLM specification, and the verified implementation in the current feature branch. Where the original specifications and the implementation differ, the implementation is explicitly identified as the as-built behavior.

---

## 1. Executive Summary

Knee Osteoporosis AI is a local-first web application for AI-assisted osteoporosis screening using knee X-ray images together with structured patient clinical information.

The system contains four major layers:

```text
1. Dedicated ML inference
2. Persistent patient and analysis data
3. Medical evidence retrieval
4. Grounded LLM Clinical Support
```

The V1 screening workflow uses a DINOv2-based image classifier to classify a knee X-ray into Normal, Osteopenia, or Osteoporosis. The predicted class is automatically inserted into the existing clinical feature vector used by a Random Forest T-score model and a Gradient Boosting Z-score model. The analysis, clinical context, and local X-ray reference are persisted in PostgreSQL/local storage.

Phase 2 adds an on-demand Clinical Support feature. The backend loads a saved analysis, builds a concise evidence query, generates a BGE embedding, retrieves 3–5 relevant passages from the approved local medical corpus using PostgreSQL/pgvector, sends permitted case context plus retrieved evidence to OpenRouter, parses the structured response, and returns it to the Clinical Support UI.

Clinical Support is an evidence-grounded educational/decision-support layer. It does not replace professional diagnosis, densitometry, clinical judgement, or treatment decisions.

---

## 2. Problem Statement

A knee X-ray screening model can produce a class prediction but does not by itself provide context-aware, evidence-grounded guidance. The project connects the screening result with structured clinical data, trusted medical evidence, and a controlled LLM synthesis layer so that the user can review the result in a more useful clinical-support context.

---

## 3. Product Goal

Provide a complete local-first workflow in which a user can:

1. Create or select a patient.
2. Upload a knee X-ray.
3. Enter clinical information.
4. Run the existing ML inference pipeline.
5. Review the predicted class, probabilities, confidence, and model-estimated T/Z scores.
6. Preserve the analysis in patient history.
7. Request Clinical Support on demand.
8. Review evidence-grounded support and source organizations/years.

The application must preserve strict boundaries between model inference, evidence retrieval, and LLM synthesis.

---

## 4. Scope

### 4.1 Implemented V1 scope

- React frontend
- TypeScript
- Vite
- FastAPI backend
- Python
- PostgreSQL
- Docker Compose
- pgAdmin
- Local X-ray storage
- Patient management
- Multiple analyses per patient
- X-ray upload and preview
- Clinical input form
- Automatic BMI calculation
- Backend BMI recalculation
- Gender-dependent pregnancy handling
- DINOv2 inference
- Three-class image classification
- Class probabilities and confidence
- T-score Random Forest estimation
- Z-score Gradient Boosting estimation
- Empirical model prediction-error ranges
- Analysis persistence
- Patient history
- Analysis deletion
- Patient deletion with image cleanup

### 4.2 Implemented Phase 2 scope

- Menopausal status
- Smoking
- Alcohol
- Previous fracture
- Long-term steroid use
- Local four-document RAG corpus
- PDF text extraction
- Chunking and metadata
- SHA-256 document checksums
- Local BGE embeddings
- PostgreSQL/pgvector vector storage
- Automatic evidence-query construction
- 3–5 chunk retrieval
- OpenRouter REST integration
- Structured Clinical Support parsing
- Evidence-derived source display
- Clinical Support API
- Clinical Support UI
- Loading/error/retry/regenerate states
- End-to-end verification
- Responsive frontend styling

### 4.3 Explicitly not implemented

- XAI / Grad-CAM / heatmaps
- Completed patient-only classification branch
- Validated probability-level multimodal fusion classifier
- LLM fine-tuning
- Autonomous diagnosis
- Prescription generation
- Medication dosage instructions
- Automated treatment decisions
- Arbitrary medical chat
- Automatic web scraping
- Authentication/login
- PDF export
- Cloud vector database
- Second vector database
- Cloud image storage
- Multilingual support
- Persisting generated Clinical Support reports

---

## 5. Product Boundaries

The system is an AI-assisted screening and evidence-support application.

It must not be represented as:

- a replacement for DXA/QUS measurement;
- a definitive diagnostic system;
- an autonomous clinical decision maker;
- a medication-prescribing system.

The LLM is a synthesis component. It does not replace the dedicated ML models.

The five Phase 2 clinical context fields are used for context/RAG and are not added to the frozen V1 ML feature vector.

---

## 6. Complete Product Workflow

### 6.1 Master workflow

```text
Home
  ↓
Patients
  ↓
Select Existing Patient OR Create Patient
  ↓
Patient Details
  ↓
New Analysis
  ↓
Upload Knee X-ray + Clinical Information
  ↓
Frontend validation + BMI display
  ↓
POST /api/analyses
  ↓
FastAPI validation
  ↓
DINOv2 preprocessing and inference
  ↓
Class + probabilities + confidence
  ↓
Build fixed V1 clinical feature vector
  ↓
T-score Random Forest
  ↓
Z-score Gradient Boosting
  ↓
Calculate empirical ranges
  ↓
Save Analysis + Local X-ray reference
  ↓
Analysis Result
  ↓
View Clinical Support
  ↓
POST /api/analyses/{analysis_id}/clinical-support
  ↓
Load saved analysis/context
  ↓
Build concise evidence query
  ↓
BGE query embedding
  ↓
PostgreSQL/pgvector cosine similarity search
  ↓
Retrieve 3–5 evidence chunks
  ↓
Build grounded prompt
  ↓
OpenRouter REST API
  ↓
Parse structured response
  ↓
Attach trusted source metadata + disclaimer
  ↓
Clinical Support UI
```

### 6.2 RAG vs LLM

**RAG retrieves evidence. The LLM synthesizes the supplied evidence and saved case context into structured Clinical Support.**

---

## 7. User and Usage Model

The primary usage pattern is:

```text
Create/select patient
→ Start analysis
→ Upload X-ray
→ Enter clinical data
→ Run analysis
→ Review ML results
→ View Clinical Support
→ Review evidence-grounded support
→ Return to history or start another analysis
```

One patient can have multiple independent analyses. Previous analyses are not overwritten.

---

## 8. Frontend Requirements

### 8.1 Routes

```text
/                                      Home
/patients                              Patients
/patients/:patientId                   Patient Details
/patients/:patientId/analysis/new     New Analysis
/analyses/:analysisId                  Analysis Result
/analyses/:analysisId/clinical-support Clinical Support
```

### 8.2 Home

Display the project purpose and a Start Analysis action.

### 8.3 Patients

Display:

- Patient ID
- Name
- Created date
- View action
- Delete action

Create patient with a generated patient code.

### 8.4 Patient Details

Display:

- Patient ID
- Name
- Created date
- Analysis history
- New Analysis action
- Delete Patient action

Analysis history includes date, diagnosis, confidence, T-score, Z-score, and analysis actions.

### 8.5 New Analysis

Collect:

```text
Age
Gender
Height (m)
Weight (kg)
BMI (auto-calculated/read-only)
Joint Pain
Number of Pregnancies
Menopausal Status
Smoking
Alcohol
Previous Fracture
Long-term Steroid Use
Knee X-ray
```

Supported image formats:

```text
PNG
JPG
JPEG
WEBP
```

Current frontend image-size limit: 10 MB.

### 8.6 Analysis Result

Display:

- predicted class;
- confidence;
- Normal probability;
- Osteopenia probability;
- Osteoporosis probability;
- model-estimated T-score and range;
- model-estimated Z-score and range;
- patient/clinical context;
- View Patient History;
- View Clinical Support;
- New Analysis.

### 8.7 Clinical Support

Display:

- Patient name and ID
- Predicted class
- Confidence and class probabilities
- Model-estimated T-score and empirical range
- Model-estimated Z-score and empirical range
- All clinical context fields
- Explanation
- What You Can Do Now
- Talk to Your Doctor About
- Testing and Follow-up
- Treatment Information
- Sources as `Organization — Year`
- Grounding Note
- Exact disclaimer
- Loading/error/retry/regenerate states

---

## 9. V1 Machine-Learning Workflow

### 9.1 Model artifacts

| Artifact | Role |
|---|---|
| `dinov2_experiment2_best.pth` | Knee X-ray classification |
| `t_score_random_forest.joblib` | T-score estimation |
| `z_score_gradient_boosting.joblib` | Z-score estimation |
| `model_metadata.json` | Model/configuration metadata |

Model weights are local files and are ignored by Git.

### 9.2 DINOv2 architecture

The current implementation uses:

```text
DINOv2 ViT-Small / 14
Input: 518 × 518
Feature dimension: 384
Output classes: 3
```

Classification head:

```text
LayerNorm(384)
→ Dropout(0.40)
→ Linear(384, 128)
→ GELU
→ Dropout(0.30)
→ Linear(128, 3)
```

### 9.3 Image preprocessing

```text
Input image
→ RGB conversion
→ aspect-ratio-preserving resize
→ LANCZOS interpolation
→ centered zero padding
→ 518 × 518
→ tensor conversion
→ ImageNet normalization
→ DINOv2
```

### 9.4 Class mapping

```text
1 → Normal
2 → Osteopenia
3 → Osteoporosis
```

The user does not enter the class manually.

### 9.5 Clinical feature vector

The V1 feature order is frozen as:

```text
[Age,
 Gender,
 BMI,
 Weight,
 Height,
 Joint Pain,
 Number of Pregnancies,
 Class,
 Pregnancy_Missing]
```

Current encodings:

```text
Gender:
Male = 0
Female = 1

Joint Pain:
No = 0
Yes = 1

Pregnancy_Missing = 0
```

The DINOv2 class is automatically inserted into the vector.

### 9.6 Pregnancy behavior

For male patients:

```text
Pregnancies = 0
field disabled in UI
```

For female patients:

```text
Pregnancies = required numeric input
```

### 9.7 BMI

```text
BMI = Weight / Height²
```

The frontend displays BMI as read-only. The backend recalculates BMI and uses its own calculated value for inference.

---

## 10. T-score and Z-score Estimation

### T-score

Model:

```text
Random Forest
```

### Z-score

Model:

```text
Gradient Boosting
```

### Empirical ranges

Current configured margins:

```text
T-score margin = ±0.3715
Z-score margin = ±1.2232
```

Therefore:

```text
T lower = prediction - 0.3715
T upper = prediction + 0.3715

Z lower = prediction - 1.2232
Z upper = prediction + 1.2232
```

These are empirical prediction-error margins from the project's trained models. They are **not clinical confidence intervals** and the values are **not measured DXA/QUS results**.

---

## 11. Persistence and Storage

### 11.1 Patient entity

```text
id
patient_code
name
created_at
```

### 11.2 Analysis entity

```text
id
patient_id
image_path
created_at

age
gender
height
weight
bmi
joint_pain
pregnancies

menopausal_status
smoking
alcohol
previous_fracture
long_term_steroid_use

predicted_class
predicted_diagnosis
normal_probability
osteopenia_probability
osteoporosis_probability
confidence

t_score
t_score_lower
t_score_upper

z_score
z_score_lower
z_score_upper

model_version
```

### 11.3 Relationship

```text
Patient 1 ───── N Analysis
```

### 11.4 Image storage

X-ray images are stored locally under:

```text
storage/uploads/
```

The database stores the image path/reference.

Patient deletion cascades through analyses and the storage layer removes associated local images.

---

## 12. Phase 2 Clinical Context

The following five fields were added without changing the V1 ML feature vector:

```text
Menopausal Status
Smoking
Alcohol
Previous Fracture
Long-term Steroid Use
```

Rules:

- Menopausal status is a controlled selection.
- Smoking is Yes/No.
- Alcohol is Yes/No.
- Previous fracture is Yes/No.
- Long-term steroid use is Yes/No.

These fields are persisted with the analysis and may contribute to retrieval/query context and Clinical Support generation.

---

## 13. RAG Corpus

Only these four documents are approved for the MVP:

| File | Organization | Year | Title |
|---|---|---:|---|
| `WHO_Fragility_Fractures.pdf` | WHO | 2024 | Fragility fractures |
| `ISBMR_Osteoporosis_Adults.pdf` | ISBMR | 2021 | ISBMR position statement for diagnosis and treatment of osteoporosis in adults |
| `IMS_Postmenopausal_Osteoporosis.pdf` | Indian Menopause Society | 2020 | Clinical practice guidelines on postmenopausal osteoporosis |
| `BHOF_Clinicians_Guide.pdf` | BHOF | 2022 | The clinician's guide to prevention and treatment of osteoporosis |

The PDFs are local-only and ignored by Git.

Document metadata retained internally includes:

```text
title
organization
publication_year
source_url
```

The UI displays only:

```text
Organization — Year
```

No patient data is stored in the RAG corpus.

---

## 14. RAG Ingestion

The ingestion command is:

```bash
python -m app.rag.ingest
```

Current pipeline:

```text
Local PDF
→ pypdf text extraction
→ chunking
→ metadata
→ SHA-256 checksum
→ local BGE embedding
→ PostgreSQL/pgvector
```

Current configurable chunk settings:

```text
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
```

The ingestion logic is designed to skip unchanged documents using the stored checksum and existing chunks.

Ingestion is manual/one-time and is not part of FastAPI request startup.

---

## 15. Embeddings

Current embedding model:

```text
BAAI/bge-base-en-v1.5
```

Runtime:

```text
Sentence Transformers
```

Embedding dimension:

```text
768
```

Embeddings run locally and are not sent to OpenRouter.

---

## 16. Vector Retrieval

The actual implemented retrieval flow is:

```text
Saved analysis
→ QueryBuilder
→ BGE query embedding
→ SQLAlchemy
→ PostgreSQL + pgvector
→ cosine similarity
→ top 5 chunks
```

The current RAG model stores embeddings as PostgreSQL `vector(768)` values.

### Important as-built clarification

The original Phase 2 specification requires LlamaIndex, and LlamaIndex dependencies are present in the repository. However, the current verified runtime retrieval implementation performs the vector search directly through **SQLAlchemy + PostgreSQL/pgvector**.

Therefore, this PRD does **not** claim that LlamaIndex is the active retrieval executor.

This distinction is intentional so the PRD documents the actual deployed code path rather than the originally planned path.

---

## 17. Query Builder

There is no user-facing free-text medical query box.

The backend automatically creates a concise evidence query from the saved analysis.

Current relevant context can include:

```text
Predicted diagnosis
Age
Gender
BMI
T-score
Z-score
Menopausal status
Smoking
Previous fracture
Long-term steroid use
```

Patient name, patient ID, image path, internal identifiers, and secrets are excluded from the retrieval/LLM request context.

---

## 18. Clinical Support API

### Endpoint

```text
POST /api/analyses/{analysis_id}/clinical-support
```

### Server-side flow

```text
analysis_id
→ load saved Analysis
→ build case context
→ QueryBuilder
→ RetrievalService
→ 3–5 chunks
→ OpenRouterService
→ structured parser
→ response schema
→ React
```

The client does not provide or override the ML prediction, T-score, Z-score, or retrieved evidence.

Generated Clinical Support is not persisted as a report.

### Response sections

```text
analysis_id
prediction_summary
explanation
what_you_can_do_now
talk_to_your_doctor_about
testing_and_follow_up
treatment_information
sources
grounding_note
disclaimer
```

---

## 19. OpenRouter and LLM

Provider:

```text
OpenRouter REST API
```

Configured initial model selector:

```text
openrouter/free
```

The model selector is environment configurable.

The backend uses `httpx` for the REST request.

Current request behavior includes:

- backend-only API key;
- 30-second client timeout;
- retry handling for null/empty model content;
- response-content fallback handling for model responses that place generated text in a reasoning field;
- structured response parsing;
- evidence-derived sources;
- no generated-report persistence.

---

## 20. Structured Response Parsing

The parser:

- searches the model output for a decodable JSON object;
- safely handles malformed or partial output;
- normalizes clinical support list fields to `list[str]`;
- defaults missing explanation content safely;
- derives sources from retrieved metadata rather than model-generated citations.

The model is not trusted to create the source list displayed to the user.

---

## 21. Clinical Support Content Rules

The LLM should:

1. Explain the existing analysis in simple language.
2. Provide evidence-grounded educational actions where supported.
3. Identify topics to discuss with a doctor.
4. Provide testing/follow-up considerations where supported.
5. Mention treatment information only when supported by retrieved evidence.
6. Avoid unsupported medical claims.
7. Avoid fabricated citations or source information.
8. Never prescribe medications or dosages.
9. Avoid presenting model estimates as direct clinical measurements.
10. Direct medical decisions to a doctor.

---

## 22. Privacy and Security

The OpenRouter request must not contain:

```text
Patient name
Patient ID
X-ray image
X-ray path
Filesystem paths
Internal database IDs
Database connection strings
API keys/secrets
```

The X-ray itself is never sent to OpenRouter.

RAG documents remain local.

The following are excluded from Git:

```text
.env
rag_documents/
patient uploads
.pth model weights
.joblib model weights
```

Secrets are supplied through environment configuration.

No authentication system is currently implemented.

---

## 23. Technology Stack

### Frontend

| Technology | Purpose |
|---|---|
| React | UI framework |
| TypeScript | Frontend language |
| Vite | Frontend build/dev tooling |
| React Router | Route navigation |
| Axios | API communication |
| CSS | UI styling |
| Oxlint | Frontend linting |

### Backend

| Technology | Purpose |
|---|---|
| Python | Backend/RAG/ML integration language |
| FastAPI | REST API |
| Uvicorn | ASGI server |
| Pydantic | Request/response validation |
| pydantic-settings | Environment configuration |
| SQLAlchemy | Database ORM/access |
| PyTorch | DINOv2 inference |
| timm | DINOv2 backbone |
| torchvision | Image transformation utilities |
| scikit-learn | Regression models |
| joblib | Load trained regression models |
| Pillow | Image loading/manipulation |
| Sentence Transformers | BGE embeddings |
| pypdf | PDF text extraction |
| pgvector | PostgreSQL vector operations |
| httpx | OpenRouter REST requests |

### Database / Infrastructure

| Technology | Purpose |
|---|---|
| PostgreSQL 15-compatible pgvector image | Application and vector database |
| pgAdmin | Database administration |
| Docker | Container runtime |
| Docker Compose | Local infrastructure orchestration |

### Development environment

- VS Code
- Git
- GitHub
- Node.js/npm for frontend development tooling
- Google Colab for model training

Node.js is not used as the backend runtime.

---

## 24. Repository Structure

```text
Knee-Osteoporosis-AI/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── health.py
│   │   │   ├── patients.py
│   │   │   ├── analyses.py
│   │   │   └── clinical_support.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── rag_models.py
│   │   ├── rag/
│   │   │   ├── ingest.py
│   │   │   ├── embeddings.py
│   │   │   ├── retrieval.py
│   │   │   ├── query_builder.py
│   │   │   └── llm_service.py
│   │   ├── schemas/
│   │   └── services/
│   │       ├── image_model.py
│   │       ├── clinical_model.py
│   │       ├── prediction_service.py
│   │       └── storage_service.py
│   ├── models/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home/
│   │   │   ├── Patients/
│   │   │   ├── PatientDetails/
│   │   │   ├── NewAnalysis/
│   │   │   ├── AnalysisResult/
│   │   │   └── ClinicalSupport/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
│
├── storage/
│   └── uploads/
│
├── docs/
│   ├── PHASE-2-PRD.md
│   └── DEVIN-PHASE-2-PROMPT.md
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── PRD.md
└── README.md
```

The exact file tree may evolve, but these responsibilities are the current architectural boundaries.

---

## 25. API Inventory

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

### Main responsibilities

`POST /api/analyses` performs the saved V1 analysis workflow with multipart image upload and clinical inputs.

`POST /api/analyses/{analysis_id}/clinical-support` generates Clinical Support on demand from the saved analysis.

---

## 26. Validation and Error Handling

The current application validates important inputs on the frontend and backend, including:

- positive age;
- supported gender;
- positive height/weight;
- supported joint-pain value;
- pregnancy rules;
- supported Phase 2 context values when provided;
- supported image extensions;
- maximum upload size.

User-facing failures should remain concise. Technical details remain in backend logs.

Relevant failure areas include:

```text
Missing patient
Invalid input
Invalid image format
Image too large
Database failure
Model loading failure
Inference failure
RAG retrieval failure
OpenRouter failure
Malformed LLM response
```

---

## 27. Docker and Database Configuration

Current Compose services:

```text
postgres
pgadmin
```

The database uses a pgvector-enabled PostgreSQL 15-compatible image.

Current Compose host mapping is:

```text
PostgreSQL host port: 5433
Container port: 5432
pgAdmin host port: 5050
```

The named PostgreSQL volume is:

```text
postgres_data
```

The same PostgreSQL instance is used for both relational data and vector data.

Do not create a second vector database.

Do not use:

```bash
Docker compose down -v
```

because it removes the named database volume.

---

## 28. Configuration

Important environment variables include:

```env
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT

STORAGE_PATH
MODEL_PATH
DINOV2_MODEL_NAME
T_SCORE_MODEL_NAME
Z_SCORE_MODEL_NAME
MODEL_METADATA_NAME

RAG_DOCUMENTS_PATH
EMBEDDING_MODEL
RAG_TOP_K
CHUNK_SIZE
CHUNK_OVERLAP

LLM_PROVIDER
LLM_MODEL
OPENROUTER_API_KEY
```

The OpenRouter API key is never stored in source control.

---

## 29. Testing and Acceptance

### 29.1 V1 regression

Required flow:

```text
Patient
→ Analysis
→ ML result
→ Persistence
→ Patient history
```

### 29.2 RAG verification

Verify:

- four approved PDFs available locally;
- text extraction succeeds;
- chunk creation succeeds;
- metadata is attached;
- 768-dimensional embeddings are stored;
- pgvector retrieval works;
- repeated unchanged ingestion is idempotent;
- no patient data is in the RAG index.

### 29.3 Clinical Support verification

Verify:

- Clinical Support button/navigation;
- saved analysis loading;
- automatic query building;
- 3–5 retrieved chunks;
- OpenRouter request;
- structured parser;
- evidence-derived sources;
- disclaimer;
- retry/regenerate behavior.

### 29.4 Frontend verification

Verify:

- all six routes load;
- patient creation/deletion;
- analysis history;
- X-ray preview;
- BMI calculation;
- pregnancy behavior;
- result rendering;
- Clinical Support rendering;
- responsive layouts.

### 29.5 Security verification

Verify that no:

```text
.env
API key
patient image
.pth
.joblib
RAG PDF
```

is committed to Git.

---

## 30. Verified Final State

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

These are implementation verification results, not clinical validation metrics.

---

## 31. Known Limitations

### 31.1 LlamaIndex runtime discrepancy

LlamaIndex is specified in the original Phase 2 requirements and its dependencies are present, but the active retrieval implementation uses direct SQLAlchemy + pgvector similarity search.

### 31.2 No XAI runtime

The current system does not generate image heatmaps or explain DINOv2 predictions visually.

### 31.3 No validated multimodal fusion classifier

The research concept is broader than the deployed classifier. The current application does not contain a separately trained patient-only classification branch followed by validated probability-level fusion.

### 31.4 Model-estimated T/Z values

T-score and Z-score are project model estimates, not direct densitometry measurements.

### 31.5 External LLM variability

`openrouter/free` may route to different upstream models and can return model-dependent response structures. Parser hardening reduces failure impact but does not control upstream behavior.

### 31.6 Research/local deployment

The current application is a local research/development system and is not presented as production clinical infrastructure.

---

## 32. Future Research Extensions

Potential future work includes:

- patient-data classification branch;
- validated probability-level multimodal fusion;
- explainable AI / Grad-CAM or other validated visual explanations;
- stronger quantitative retrieval evaluation;
- expert review protocols for Clinical Support;
- external clinical validation;
- governed expansion of the evidence corpus;
- optional production deployment controls.

These are future extensions and are not part of the current implemented product.

---

## 33. Final Viva Explanation

> A knee X-ray is uploaded through the React application together with the required clinical information. FastAPI validates the request and runs the DINOv2 image classifier, which produces a three-class screening result with class probabilities and confidence. The predicted class is automatically inserted into the fixed V1 clinical feature vector used by the T-score Random Forest and Z-score Gradient Boosting models. The system calculates empirical T/Z prediction-error ranges, saves the analysis and local image reference, and displays the result.
>
> For Clinical Support, the user explicitly opens the feature for a saved analysis. The backend loads the analysis and clinical context, builds a concise evidence query, creates a BGE embedding, and performs cosine-similarity retrieval against the approved medical corpus stored in PostgreSQL/pgvector. Three to five relevant evidence chunks are combined with permitted case context in a grounded OpenRouter prompt. The backend parses the returned structured response, derives source information from retrieved metadata, and sends the result to the Clinical Support UI with the grounding note and exact medical-safety disclaimer. The system supports screening and evidence review; it does not replace professional diagnosis or treatment decisions.

---

## 34. Exact Medical Disclaimer

**AI-assisted guidance for informational purposes. This does not replace a doctor's diagnosis or treatment decision. Discuss medical decisions with your doctor.**

---

## 35. Final Product Definition

The completed system is an AI-assisted osteoporosis screening application that combines:

```text
Knee X-ray
   ↓
DINOv2 classification
   ↓
V1 clinical-model estimation
   ↓
Saved analysis
   ↓
BGE evidence retrieval
   ↓
PostgreSQL/pgvector
   ↓
Grounded OpenRouter synthesis
   ↓
Structured Clinical Support
   ↓
Human review
```

The core design deliberately keeps four responsibilities separate:

```text
DINOv2              → X-ray classification
Random Forest       → T-score estimation
Gradient Boosting   → Z-score estimation
BGE + pgvector      → evidence retrieval
OpenRouter          → Clinical Support synthesis
React               → user interface
```

The human user remains responsible for interpretation and medical decisions.
