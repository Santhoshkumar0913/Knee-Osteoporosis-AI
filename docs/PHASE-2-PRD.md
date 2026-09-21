# Phase 2 PRD — RAG + LLM Clinical Support

**Repository:** `Santhoshkumar0913/Knee-Osteoporosis-AI`  
**Branch:** `feature/rag-llm`  
**Phase:** 2

> The existing root `PRD.md` remains the V1 source of truth. This document extends it for Phase 2. All V1 ML behavior and the existing patient/analysis workflow remain unchanged unless explicitly stated here.

## 1. Objective

Add an on-demand **Clinical Support** feature using the saved V1 analysis result, curated medical evidence, RAG, and an LLM. The feature provides patient-friendly evidence-based education and next-step guidance. It is not autonomous diagnosis or prescribing.

## 2. Workflow

```text
Home → Patients → Select/Create Patient → New Analysis
→ X-ray + clinical inputs → Run Analysis
→ DINOv2 → T-score/Z-score → Analysis Result
→ [View Clinical Support]
→ Clinical Support page
→ POST /api/analyses/{analysis_id}/clinical-support
→ load saved analysis/context
→ build retrieval query
→ LlamaIndex
→ PostgreSQL + pgvector
→ retrieve 3–5 relevant chunks
→ grounded prompt
→ OpenRouter REST API
→ structured patient-friendly support
→ display
```

Clinical Support is generated only on demand. Do not generate it automatically during analysis. Do not store generated Clinical Support text in PostgreSQL.

## 3. STRICT technology stack

### Application languages

- **Python** — FastAPI, RAG, document ingestion, embeddings, LLM integration.
- **TypeScript** — existing React frontend.
- **SQL** — PostgreSQL/pgvector.
- HTML/CSS through React/Vite.

No other application language is permitted. Do not introduce Java, C/C++, C#, Go, Rust, PHP, Ruby, Kotlin, Swift, etc.

Node.js is permitted only as Vite/npm development tooling. **Do not use Node/Express as the backend.**

### Required frameworks/services

| Area | Required technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| Backend | Python + FastAPI + Uvicorn |
| Validation/config | Pydantic + pydantic-settings |
| ORM/migrations | SQLAlchemy + Alembic |
| RAG | **LlamaIndex** |
| Embeddings | **BAAI/bge-base-en-v1.5** locally via Python/Sentence Transformers |
| Vector DB | **PostgreSQL + pgvector** |
| LLM API | **OpenRouter REST API** |
| Initial model selector | **openrouter/free** |
| Infrastructure | Docker + Docker Compose + pgAdmin |

Do not substitute Next.js, Flask, Express, LangChain, Haystack, Chroma, Pinecone, FAISS, Qdrant, Weaviate, Milvus, hosted embedding APIs, or another LLM provider without explicit approval.

## 4. RAG corpus

Use only these four MVP PDFs:

```text
Local-only RAG source directory (do not commit or push the PDFs):

```text
rag_documents/
├── WHO_Fragility_Fractures.pdf
├── ISBMR_Osteoporosis_Adults.pdf
├── IMS_Postmenopausal_Osteoporosis.pdf
└── BHOF_Clinicians_Guide.pdf
```

The four PDFs are supplied locally by the user. Do not upload or commit them to GitHub. Add `rag_documents/` to `.gitignore`. The application must be configurable through `RAG_DOCUMENTS_PATH` so the ingestion command can use the local folder.

Retain metadata for every chunk:

- document title
- organization
- publication year
- original source URL

UI source display must be **Organization — Year**. No page/section citation is required in the MVP.

Do not scrape unrelated websites or add the previously rejected redundant guideline document.

## 5. Ingestion

Ingestion is manual/one-time, not a FastAPI startup task.

Recommended command:

```bash
python -m app.rag.ingest
```

Pipeline:

```text
PDF → text extraction → cleaning → chunking → metadata
→ BAAI/bge-base-en-v1.5 → PostgreSQL + pgvector
```

Requirements:

- safe to rerun;
- idempotent for unchanged documents;
- checksum/hash or equivalent duplicate/change detection;
- no duplicate unchanged chunks;
- clear document/chunk logs;
- clear missing/unreadable-PDF errors;
- no silent replacement of missing documents;
- no OCR unless actually required;
- chunk size/overlap configurable in one place.

The embedding model runs locally. Do not send document text to OpenRouter during ingestion.

## 6. Retrieval

Retrieve **3–5 relevant chunks** for each Clinical Support request.

The retrieval query is created automatically by FastAPI. There is no user query box.

Relevant case context can include:

- Age, Gender, BMI, Weight, Height, Joint Pain, Number of Pregnancies;
- Menopausal Status, Smoking, Alcohol, Previous Fracture, Long-term Steroid Use;
- DINOv2 predicted class, probabilities, confidence;
- model-estimated T-score and empirical range;
- model-estimated Z-score and empirical range.

Do not blindly concatenate every field. Build a concise clinical evidence query.

Do not send patient name, patient ID, internal IDs/paths, API keys, or the X-ray image to OpenRouter.

## 7. Additional Clinical Support fields

Add to **New Analysis**:

```text
Menopausal Status
Smoking
Alcohol
Previous Fracture
Long-term Steroid Use
```

Smoking, alcohol, fracture history, and long-term steroid use use **Yes/No** controls. Menopausal status uses a controlled selection validated by FastAPI.

These five fields are **RAG/context fields only**. They must NOT be added to the existing ML feature vector and must not trigger retraining.

Persist these five fields with the analysis so saved analyses retain complete clinical context.

## 8. Existing V1 ML must remain unchanged

Keep the current mapping:

```text
1 → Normal
2 → Osteopenia
3 → Osteoporosis
```

Keep the current clinical feature order:

```text
Age
Gender
BMI
Weight
Height
Joint Pain
Number of Pregnancies
Class
Pregnancy_Missing
```

Do not move or duplicate ML inference inside the RAG service. Clinical Support should read the saved analysis results.

## 9. PostgreSQL + pgvector

The current V1 Compose file uses PostgreSQL 15 with a named `postgres_data` volume. Phase 2 must use a PostgreSQL 15-compatible pgvector-enabled setup while preserving existing data.

Requirements:

1. Inspect the current Compose file and volume.
2. Replace/adapt PostgreSQL to a pgvector-enabled PostgreSQL 15 configuration.
3. Preserve the existing named volume.
4. Enable the `vector` extension.
5. Verify V1 tables/data remain accessible.
6. Verify FastAPI still connects.
7. Use the same PostgreSQL instance; do not create another vector DB.
8. **Never use `docker compose down -v`.**
9. Use Alembic for Phase 2 schema changes.

Verify with:

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';
```

## 10. RAG storage

Use LlamaIndex with PostgreSQL/pgvector. Each chunk must carry title, organization, publication year, and source URL metadata.

A small ingestion registry/checksum table may be used for idempotency. Do not store patient data in the RAG index.

## 11. OpenRouter

Use the **OpenRouter REST API from Python only**.

Initial model selector:

```text
openrouter/free
```

Keep the model configurable in environment variables.

Example:

```env
OPENROUTER_API_KEY=
LLM_PROVIDER=openrouter
LLM_MODEL=openrouter/free
RAG_DOCUMENTS_PATH=rag_documents
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
RAG_TOP_K=5
```

The API key is backend-only and must never appear in frontend code, GitHub, logs, tests, prompts, PRD, or README.

Handle missing key, timeout, API errors, and rate limits safely.

## 12. Clinical Support API

Add:

```text
POST /api/analyses/{analysis_id}/clinical-support
```

The request should only identify the analysis; the backend loads the case from PostgreSQL.

Flow:

```text
analysis_id → load analysis/context → build query
→ retrieve 3–5 chunks → grounded prompt → OpenRouter
→ validate structured result → return JSON
```

Do not persist the generated response.

Recommended response structure:

```json
{
  "analysis_id": 1,
  "prediction_summary": {
    "class": "Osteopenia",
    "confidence": 0.93,
    "t_score": -1.92,
    "t_score_lower": -2.29,
    "t_score_upper": -1.55,
    "z_score": -0.96,
    "z_score_lower": -2.18,
    "z_score_upper": 0.26
  },
  "explanation": "...",
  "what_you_can_do_now": ["..."],
  "talk_to_your_doctor_about": ["..."],
  "testing_and_follow_up": ["..."],
  "treatment_information": ["..."],
  "sources": [{"organization": "WHO", "year": 2022}],
  "grounding_note": "...",
  "disclaimer": "AI-assisted guidance for informational purposes. This does not replace a doctor's diagnosis or treatment decision. Discuss medical decisions with your doctor."
}
```

Use Pydantic validation. The exact schema may be refined while retaining these sections.

## 13. Grounding and safety

Retrieved RAG evidence is the primary factual basis for clinical claims.

The LLM must:

- explain the application's existing result in simple language;
- personalize guidance to the case;
- not invent citations, evidence, organizations, or years;
- not claim model-estimated T/Z are measured DXA/QUS values;
- not call empirical T/Z error ranges clinical confidence intervals;
- not diagnose beyond the application's model result;
- not prescribe medication or dosage;
- direct treatment decisions to a doctor.

If retrieval is insufficient, do not fabricate support. Cautious general education may be used only when appropriate and must be clearly identified as not directly supported by retrieved documents.

The application must derive displayed sources from retrieved metadata, not trust model-generated citations.

## 14. Clinical Support UI

Add a separate **Clinical Support** page reached from Analysis Result through:

```text
[ View Clinical Support ]
```

Display:

### Patient
- Name
- Patient ID

### AI prediction
- predicted class
- confidence
- class probabilities

### Bone scores
- model-estimated T-score + range
- model-estimated Z-score + range

### Clinical context
- Age
- Gender
- Height
- Weight
- BMI
- Joint Pain
- Number of Pregnancies
- Menopausal Status
- Smoking
- Alcohol
- Previous Fracture
- Long-term Steroid Use

### Evidence-Based Support
- Explanation
- What you can do now
- Talk to your doctor about
- Testing/follow-up considerations
- Treatment information where supported

### Sources
Actual retrieved sources shown as:

```text
Organization — Year
```

### Disclaimer

> AI-assisted guidance for informational purposes. This does not replace a doctor's diagnosis or treatment decision. Discuss medical decisions with your doctor.

Use loading/retry/error states. Do not expose stack traces or secrets.

## 15. Privacy

OpenRouter is an external service. Do not send:

- patient name;
- patient ID;
- X-ray image;
- image path;
- database/internal IDs;
- filesystem paths;
- connection strings;
- API keys.

Send only the minimum clinical context required for the LLM response.

## 16. Explicitly out of scope

Do not implement in Phase 2:

- model retraining or changes to the existing ML artifacts;
- XAI/Grad-CAM/heatmaps;
- image explanation by LLM;
- doctor/researcher mode;
- authentication/login;
- PDF export;
- cloud image storage;
- cloud vector DB;
- second vector database;
- local Ollama implementation;
- multilingual support;
- arbitrary user medical-question chat;
- automatic web scraping;
- autonomous diagnosis;
- medication prescription/dosage;
- automatic treatment decisions;
- storing generated Clinical Support reports.

## 17. Testing and acceptance

### V1 regression

Verify:

```text
patient → analysis → ML result → history
```

Existing predictions must continue to work.

### RAG

Verify all four PDFs, text extraction, chunk creation, metadata, 768-dimension embeddings, pgvector storage, and idempotent rerun.

### Retrieval

Representative osteoporosis cases should return 3–5 relevant chunks with correct source metadata.

### OpenRouter

Verify backend-only key loading, `openrouter/free` request, error/rate-limit handling, and absence of key leakage.

### API/UI

Verify Clinical Support button, loading/error/retry, structured response, sources, disclaimer, and patient/context display.

### Security

No `.env`, API key, patient image, `.pth`, `.joblib`, or other large model artifact may be committed.

## 18. Implementation order

```text
Phase 0  → repository analysis/report
Phase 1  → PostgreSQL + pgvector
Phase 2  → RAG dependencies/config
Phase 3  → PDF ingestion
Phase 4  → BGE embeddings
Phase 5  → LlamaIndex retrieval
Phase 6  → OpenRouter service
Phase 7  → clinical context/query builder
Phase 8  → Clinical Support API
Phase 9  → new clinical fields
Phase 10 → Clinical Support UI
Phase 11 → end-to-end integration
Phase 12 → regression/security/docs
```

Do not start Phase 1 until the Phase 0 report has been provided and explicitly approved.

## 19. Phase 0 required report

Before any modification, Devin must report:

### Git
- branch, commit, status, uncommitted changes;
- whether `feat/rag-llm` exists remotely;
- relationship to `main`.

### Project
- frontend/backend folder tree;
- existing routes, services, schemas, models, tests;
- current dependencies.

### V1 APIs
List each route and implementation file.

### V1 ML
Confirm DINOv2 loading/preprocessing, class mapping, feature order, BMI/pregnancy behavior, T-score/Z-score models, and ranges.

### Docker/database
Report PostgreSQL image, ports, volume, pgAdmin, Alembic state, current `vector` extension state, and safe migration plan.

### RAG readiness
Verify the four PDFs are visible.

### Environment
Verify required variables exist without revealing secrets.

### Plan
Give a file-by-file plan for CREATE/MODIFY/DELETE plus database/API/frontend/Docker/dependency/env changes.

### Conflict report
List all conflicts between actual repo state and this PRD.

**STOP after the report and wait for explicit approval.**

## 20. Git safety

Work only on `feat/rag-llm`. Never modify `main` directly. Never force-push, reset away user work, clean uncommitted changes, delete the PostgreSQL volume, or commit `.env`, API keys, patient images, `.pth`, `.joblib`, or other model weights.

Review the diff before every commit.

## 21. Final target architecture

```text
React + TypeScript + Vite
          ↓
      FastAPI/Python
          ↓
Clinical Support Service
     ┌────┼──────────────┐
     ↓    ↓              ↓
PostgreSQL  Query Builder  LlamaIndex
 patient/analysis           ↓
                         pgvector
                            ↓
                        3–5 chunks
                            ↓
                      grounded prompt
                            ↓
                 OpenRouter REST API
                    openrouter/free
                            ↓
                structured Clinical Support
                            ↓
                 React Clinical Support UI
```


## 12. Clinical Support content

The Clinical Support page must include:

- Patient name and patient ID
- Predicted class
- Confidence and class probabilities
- Model-estimated T-score and empirical range
- Model-estimated Z-score and empirical range
- Full clinical context, including the five Phase 2 context fields
- Evidence-based explanation in simple English
- What you can do now
- Talk to your doctor about
- Testing/follow-up considerations
- Treatment/medication information only where supported by retrieved evidence, with a clear instruction to discuss medical decisions with a doctor
- Sources displayed as organization and year
- The exact disclaimer: **AI-assisted guidance for informational purposes. This does not replace a doctor's diagnosis or treatment decision. Discuss medical decisions with your doctor.**

Do not provide autonomous diagnosis, prescribing, dosage instructions, or definitive treatment decisions.

## 13. Clinical Support API

Add an endpoint equivalent to:

```text
POST /api/analyses/{analysis_id}/clinical-support
```

The endpoint must load the saved analysis and build the Clinical Support context server-side. The client must not supply or override the ML prediction, T-score, Z-score, or retrieved evidence.

The response must be structured JSON suitable for direct rendering by React. Prefer typed Pydantic response models.

## 14. LLM grounding and safety

The generated answer must be grounded primarily in the retrieved RAG evidence plus the saved analysis context. The prompt must instruct the LLM:

- Do not invent citations, facts, diagnoses, medication instructions, or unsupported claims.
- Do not claim that the X-ray model explains why a prediction was made; XAI is out of scope for Phase 2.
- Do not expose internal IDs, file paths, prompts, API keys, or system details.
- Clearly indicate when a statement is general educational information rather than directly supported by the retrieved documents.
- Keep the output patient-friendly and concise.
- Treatment decisions must be framed as topics to discuss with a doctor.

No user-entered free-text clinical query is required.

## 15. Clinical Support is not stored

Do not create a database table for generated Clinical Support reports in Phase 2. The existing patient/analysis data remains persistent; generated LLM content is generated on demand and returned to the client.

## 16. Local-first and privacy

RAG documents and embeddings remain local to the application database/environment. Patient names, patient IDs, X-ray images, image paths, and internal database identifiers must not be included in the OpenRouter request unless explicitly required by a future approved design.

The X-ray image itself must never be sent to OpenRouter in Phase 2.

The OpenRouter API key is local configuration only and must never be committed to GitHub.
