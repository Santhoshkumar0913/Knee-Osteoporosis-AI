# Devin Prompt — Phase 2 RAG + LLM Clinical Support

Repository: `Santhoshkumar0913/Knee-Osteoporosis-AI`
Target branch: `feature/rag-llm`

Read:
1. root `PRD.md` — V1 baseline
2. `docs/PHASE-2-PRD.md` — Phase 2 specification

## CRITICAL: ANALYZE FIRST — DO NOT IMPLEMENT

Your first task is **Phase 0 analysis only**.

Do not modify code, dependencies, Docker, database schema, frontend, backend, or Git state during Phase 0.

Inspect the actual repository/branch available to you and produce a **Current Project Analysis Report**. Then STOP and wait for explicit approval before starting Phase 2 implementation.

The user has additional changes in their local VS Code workspace that may not be pushed to GitHub, including:
- `rag_documents/` containing the four approved PDFs (local-only; do not commit or push);
- `.env` with the OpenRouter API key;
- other local API/folder/config changes.

If these changes are not visible in your environment, say so explicitly. Do not recreate or overwrite them blindly. The user may provide the local RAG PDFs separately in the Devin workspace if needed.

You may check whether `OPENROUTER_API_KEY` exists, but never print its value.

## RAG DOCUMENTS ARE LOCAL-ONLY

The four approved PDFs are intentionally NOT stored in GitHub because of file size/redistribution considerations. Do not commit, push, or recreate them in the repository. If the local files are available in your workspace, use them. Otherwise report them as missing and wait for the user to provide them.

Expected local files:
```text
rag_documents/
├── WHO_Fragility_Fractures.pdf
├── ISBMR_Osteoporosis_Adults.pdf
├── IMS_Postmenopausal_Osteoporosis.pdf
└── BHOF_Clinicians_Guide.pdf
```

The repository `.gitignore` must contain:
```gitignore
rag_documents/
```

Do not print or expose the OpenRouter API key. Read it only through environment configuration.

## LOCKED TECHNOLOGY STACK — DO NOT SUBSTITUTE

Application languages allowed:
- **Python** — all backend, RAG, ingestion, embeddings and LLM logic.
- **TypeScript** — existing React frontend.
- **SQL** — PostgreSQL/pgvector.
- HTML/CSS through React/Vite.

Do not introduce another application programming language: no Java, C, C++, C#, Go, Rust, PHP, Ruby, Kotlin, Swift, etc.

Node.js is permitted only for the existing Vite/npm frontend tooling. **Do not create a Node/Express backend.**

Required stack:
- React + TypeScript + Vite
- Python + FastAPI + Uvicorn
- Pydantic + pydantic-settings
- SQLAlchemy + Alembic
- **LlamaIndex** for RAG
- **BAAI/bge-base-en-v1.5** local embeddings
- Sentence Transformers/Python embedding runtime
- **PostgreSQL + pgvector**
- Docker + Docker Compose + pgAdmin
- **OpenRouter REST API**
- initial model selector: **`openrouter/free`**

Do not replace these with Next.js, Flask, Express, LangChain, Haystack, Chroma, Pinecone, FAISS, Qdrant, Weaviate, Milvus, hosted embeddings, or another LLM provider.

# PHASE 0 — REQUIRED CURRENT PROJECT REPORT

Inspect and report:

### 1. Git state
- current branch;
- current commit;
- `git status`;
- uncommitted changes;
- whether `feat/rag-llm` exists on the remote;
- relationship to `main`.

Never reset, clean, stash, force-push, or discard user work.

### 2. Repository structure
Inspect:
- `backend/`;
- `frontend/`;
- `storage/`;
- `docker-compose.yml`;
- `.env.example`;
- `.gitignore`;
- root `PRD.md`;
- docs;
- tests;
- model configuration.

### 3. Backend
Identify:
- FastAPI entry point;
- routes;
- schemas;
- database models;
- configuration;
- services;
- ML services;
- storage service;
- requirements;
- tests.

### 4. Frontend
Identify:
- routes;
- Home;
- Patients;
- Patient Details;
- New Analysis;
- Analysis Result;
- API client;
- types/components.

### 5. V1 API inventory
List endpoint + implementation file for every existing API route.

### 6. V1 ML inventory
Confirm from actual code:
- DINOv2 architecture/checkpoint;
- preprocessing;
- class mapping;
- clinical feature order;
- BMI handling;
- pregnancy handling;
- T-score model;
- Z-score model;
- T/Z range logic.

Do not change the ML pipeline during analysis.

### 7. Docker/database audit
Report:
- PostgreSQL image;
- port mapping;
- named volume;
- pgAdmin;
- database connection config;
- Alembic state;
- whether `vector` extension is installed.

Plan a safe PostgreSQL 15 + pgvector migration that preserves existing data.

**Never use `docker compose down -v`.**

### 8. RAG readiness
Check whether these are actually available:

```text
rag_documents/
├── WHO_Fragility_Fractures.pdf
├── ISBMR_Osteoporosis_Adults.pdf
├── IMS_Postmenopausal_Osteoporosis.pdf
└── BHOF_Clinicians_Guide.pdf
```

If missing, report the missing files. Do not substitute unrelated documents.

### 9. Environment readiness
Check existence of:
- `OPENROUTER_API_KEY`;
- `LLM_PROVIDER`;
- `LLM_MODEL`;
- `RAG_DOCUMENTS_PATH`;
- `EMBEDDING_MODEL`;
- existing DB/model/storage variables.

Never reveal secret values.

### 10. Dependency audit
Identify exact dependency changes required for:
- LlamaIndex;
- pgvector integration;
- BGE/Sentence Transformers;
- PDF extraction;
- OpenRouter REST.

Avoid unnecessary packages.

### 11. File-by-file Phase 2 plan
Report:

```text
CREATE:
...

MODIFY:
...

DELETE:
...

DATABASE:
...

API:
...

FRONTEND:
...

DOCKER:
...

DEPENDENCIES:
...

ENV:
...
```

### 12. Conflict report
List anything in the current repository that conflicts with the Phase 2 PRD.

### 13. STOP

After the report, **STOP and wait for explicit approval**. Do not implement Phase 2 before approval.

# AFTER APPROVAL — IMPLEMENT PHASE 2

Implement only on `feat/rag-llm` and in small verifiable stages.

## Phase 1 — PostgreSQL + pgvector

- preserve the current PostgreSQL named volume;
- use a PostgreSQL 15-compatible pgvector-enabled image/configuration;
- enable `vector`;
- verify existing V1 tables/data;
- verify FastAPI connectivity;
- do not create a second vector database;
- never use `docker compose down -v`.

Verify with:

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';
```

## Phase 2 — RAG dependencies

Add only the dependencies needed for LlamaIndex, pgvector, BGE embeddings, PDF ingestion, and OpenRouter REST calls.

All RAG/LLM code must be Python.

## Phase 3 — PDF ingestion

Create a manual command such as:

```bash
python -m app.rag.ingest
```

Use only the four approved PDFs.

Requirements:
- extract text;
- chunk text;
- attach title/organization/year/source URL metadata;
- create local BGE embeddings;
- store in PostgreSQL/pgvector;
- checksum/idempotency;
- no duplicate unchanged content;
- clear logs/errors;
- no ingestion on FastAPI startup.

## Phase 4 — embeddings

Required model:

`BAAI/bge-base-en-v1.5`

Run locally. Do not send embeddings to OpenRouter. Do not commit model weights.

## Phase 5 — retrieval

Use LlamaIndex + PostgreSQL/pgvector.

Retrieve **3–5 relevant chunks** per Clinical Support request.

Keep retrieval separate from the API route.

## Phase 6 — OpenRouter

Use OpenRouter REST API from Python.

Default:

`openrouter/free`

Use environment variables only. Never expose/log the key.

Handle missing key, timeout, API failure, rate limit, and malformed output.

## Phase 7 — clinical context/query builder

Read the saved analysis and the additional context fields.

Relevant context may include:
- age;
- gender;
- BMI;
- weight;
- height;
- joint pain;
- pregnancies;
- menopausal status;
- smoking;
- alcohol;
- previous fracture;
- long-term steroid use;
- predicted class;
- probabilities/confidence;
- model-estimated T/Z and ranges.

Build a concise clinical evidence query. Do not blindly concatenate fields.

Do not send patient name/ID, internal IDs/paths, X-ray, or secrets to OpenRouter.

## Phase 8 — Clinical Support API

Add:

```text
POST /api/analyses/{analysis_id}/clinical-support
```

Flow:

```text
analysis_id
→ load analysis/context
→ build retrieval query
→ LlamaIndex
→ 3–5 chunks
→ grounded prompt
→ OpenRouter
→ Pydantic validation
→ structured JSON
```

Do not persist the generated response.

## Phase 9 — additional clinical fields

Add to New Analysis:
- Menopausal Status;
- Smoking;
- Alcohol;
- Previous Fracture;
- Long-term Steroid Use.

Smoking/alcohol/fracture/steroid use: Yes/No.
Menopausal status: controlled selection + backend validation.

Persist these five fields with the analysis.

**Do not add them to the existing ML feature vector.**

## Phase 10 — Clinical Support UI

Add a separate Clinical Support page reached from Analysis Result by:

`[ View Clinical Support ]`

Display:
- patient name and ID;
- predicted class;
- confidence and class probabilities;
- model-estimated T/Z and ranges;
- full clinical context;
- Explanation;
- What you can do now;
- Talk to your doctor about;
- Testing/follow-up considerations;
- Treatment information where supported;
- Sources as Organization — Year;
- exact disclaimer specified in the Phase 2 PRD.

Use loading/error/retry states.

No XAI. No automatic generation. No researcher/doctor mode.

## Phase 11 — grounding/safety

Retrieved RAG evidence is the primary factual basis.

Never:
- fabricate evidence or citations;
- invent source metadata;
- prescribe medication or dosage;
- make automatic treatment decisions;
- call model-estimated T/Z ranges clinical confidence intervals;
- represent model estimates as DXA/QUS measurements.

The application must derive displayed sources from retrieved metadata.

If evidence is insufficient, do not fabricate support.

## Phase 12 — testing

Run:

### V1 regression
`patient → analysis → ML result → history`

### RAG ingestion
- four PDFs detected;
- extraction succeeds;
- chunks created;
- metadata correct;
- 768-dimension embeddings;
- vectors stored;
- repeated ingestion is idempotent.

### Retrieval
Representative cases return 3–5 relevant chunks and correct source metadata.

### OpenRouter
Successful request with `openrouter/free`; errors/rate limits handled; key not leaked.

### API/UI
Clinical Support endpoint, button, loading/error/retry, structured sections, sources, disclaimer, context display.

### Security
No `.env`, API key, patient images, `.pth`, `.joblib`, or other model weights committed.

Do not claim a test passed unless you actually ran it.

# FINAL IMPLEMENTATION REPORT

After implementation, report:

1. files created;
2. files modified;
3. files deleted, if any;
4. DB/migration changes;
5. API changes;
6. frontend changes;
7. Docker changes;
8. dependencies;
9. env variables;
10. ingestion command;
11. tests actually run and results;
12. unresolved issues;
13. commits created;
14. confirmation `main` was not modified;
15. confirmation `.env`, API keys, patient images, and ML weights were not committed.

# GIT SAFETY

Work only on `feat/rag-llm`.

Never:
- force-push;
- reset away user work;
- clean/discard uncommitted changes;
- delete PostgreSQL volume;
- modify `main` directly;
- commit `.env`;
- commit API keys;
- commit patient images;
- commit `.pth`/`.joblib` model artifacts.

Review the diff before every commit.
