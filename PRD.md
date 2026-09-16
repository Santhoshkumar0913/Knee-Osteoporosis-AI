# PRD — Knee Osteoporosis AI

## 1. Project

**Repository:** https://github.com/Santhoshkumar0913/Knee-Osteoporosis-AI.git

**Project title:** Adaptive Multimodal AI and LLM Framework for Early Osteoporosis Screening

This repository is the **only target repository** for the web application. Do not create the application in a new repository.

## 2. Scope of this implementation

Build the application only up to the point where the complete ML analysis is performed and the results are displayed and saved.

### In scope

- React frontend
- FastAPI backend
- PostgreSQL database using Docker
- pgAdmin using Docker
- Local X-ray image storage
- Patient management
- Multiple analyses per patient
- X-ray upload and preview
- Clinical input form
- Automatic BMI calculation
- Gender-dependent pregnancy input
- DINOv2 inference
- T-score inference
- Z-score inference
- Display classification probabilities/confidence
- Display T-score and Z-score estimates and model-based ranges
- Save analyses and image references
- View patient history
- View individual analysis details
- Delete analysis/patient data
- Model version tracking

### Explicitly out of scope for this phase

Do **not** implement RAG, vector databases, LLM integration, medical-document retrieval, or LLM-generated clinical reports in this phase.

The application should be structured so these can be added later without redesigning the core patient/analysis workflow.

---

# 3. Existing ML models

The ML models have already been trained in Google Colab. The web application must use the existing trained models and must **not retrain them**.

The user will manually copy the model files into the appropriate backend model folder before running the backend.

Expected model files:

```text
backend/
└── models/
    ├── dinov2_experiment2_best.pth
    ├── t_score_random_forest.joblib
    ├── z_score_gradient_boosting.joblib
    └── model_metadata.json
```

### Model roles

- `dinov2_experiment2_best.pth` → knee X-ray classification
- `t_score_random_forest.joblib` → T-score estimation
- `z_score_gradient_boosting.joblib` → Z-score estimation
- `model_metadata.json` → model/configuration metadata

The backend must load these models at startup and keep them in memory for inference.

Do not replace the models with newly trained models.

---

# 4. ML pipeline

The complete V1 prediction pipeline is:

```text
React frontend
      ↓
FastAPI
      ↓
Validate input
      ↓
X-ray preprocessing
      ↓
DINOv2
      ↓
Normal / Osteopenia / Osteoporosis
      ↓
Predicted class ID
      ↓
Build clinical feature vector
      ↓
T-score Random Forest
      ↓
Z-score Gradient Boosting
      ↓
Calculate model-based ranges
      ↓
Return JSON result
      ↓
React displays result
      ↓
Save analysis + image reference
```

## 4.1 DINOv2 classes

```text
1 → Normal
2 → Osteopenia
3 → Osteoporosis
```

The user must **not** manually enter the predicted class.

The DINOv2 class is automatically passed into the clinical models by FastAPI.

---

# 5. Clinical model input

The current clinical model feature vector is:

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

For this web application's simplified V1 workflow:

```text
Male:
  Number of Pregnancies = 0
  Pregnancy_Missing = 0

Female:
  Number of Pregnancies = required user input
  Pregnancy_Missing = 0
```

Do not add a "Not provided" pregnancy option in V1.

The backend must construct this vector in the exact expected order.

---

# 6. Technology stack

## Frontend

- React
- TypeScript preferred
- Vite preferred
- Responsive modern UI

## Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- PyTorch
- timm
- scikit-learn
- joblib
- Pillow

## Database / infrastructure

- PostgreSQL
- Docker Desktop
- Docker Compose
- pgAdmin

## Development

- VS Code
- Git
- GitHub
- Devin

Training remains in Google Colab. Local development only needs to perform inference.

A local NVIDIA GPU is not required for V1; CPU inference is acceptable.

---

# 7. Repository requirement

All development must happen inside:

```text
https://github.com/Santhoshkumar0913/Knee-Osteoporosis-AI.git
```

Do not create a parallel repository.

First inspect the existing repository contents. Reuse compatible existing code where appropriate, but do not allow the old project structure to force incorrect architecture. Refactor carefully when necessary.

Commit changes in logical stages.

---

# 8. Proposed project structure

```text
Knee-Osteoporosis-AI/
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home/
│   │   │   ├── Patients/
│   │   │   ├── PatientDetails/
│   │   │   ├── NewAnalysis/
│   │   │   └── AnalysisResult/
│   │   ├── components/
│   │   ├── services/
│   │   ├── types/
│   │   └── ...
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── health.py
│   │   │   ├── patients.py
│   │   │   └── analyses.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── schemas/
│   │   └── services/
│   │       ├── image_model.py
│   │       ├── clinical_model.py
│   │       ├── prediction_service.py
│   │       └── storage_service.py
│   ├── models/
│   │   ├── dinov2_experiment2_best.pth
│   │   ├── t_score_random_forest.joblib
│   │   ├── z_score_gradient_boosting.joblib
│   │   └── model_metadata.json
│   ├── tests/
│   ├── requirements.txt
│   └── ...
│
├── storage/
│   └── uploads/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

The exact internal structure may be adjusted if Devin has a cleaner maintainable implementation, but the separation of frontend/backend/models/storage must remain.

---

# 9. Docker database setup

Use Docker Compose to run:

```text
PostgreSQL
pgAdmin
```

Do **not** require PostgreSQL Server to be installed directly on Windows.

Database credentials must come from environment variables.

Example variables:

```text
POSTGRES_DB=osteoporosis_ai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<local-secret>
```

Also provide backend database configuration through `.env` / environment variables.

Never commit real passwords or secrets.

pgAdmin should connect to the PostgreSQL container through the Docker network.

---

# 10. Main application workflow

```text
Home
  ↓
Start Analysis
  ↓
Patients
  ↓
Select existing patient
  OR
Create new patient
  ↓
New Analysis
  ↓
Upload X-ray
  +
Enter clinical details
  ↓
Run Analysis
  ↓
DINOv2 prediction
  ↓
T-score + Z-score estimation
  ↓
Analysis Result
  ↓
Save Analysis
  ↓
Patient History
```

A patient may have many analyses:

```text
Patient P0001
├── Analysis A0001
├── Analysis A0002
├── Analysis A0003
└── Analysis A0004
```

Never overwrite previous analyses.

---

# 11. Pages

## 11.1 Home

Keep the home page simple.

Display:

```text
Knee Osteoporosis AI

AI-assisted screening using knee X-ray images
and patient clinical information.

[ Start Analysis ]
```

Main navigation can be:

```text
Home | Patients
```

Do not add unnecessary dashboard statistics in V1.

---

## 11.2 Patients

Show patients in a clean table/list.

Minimum information:

```text
Patient ID
Name
Created At
Action
```

Example:

```text
P0001   Arun Kumar
P0002   Arun Kumar
P0003   Priya Kumar
```

Duplicate names are allowed.

Patient ID is unique and generated automatically.

Recommended display format:

```text
P0001 — Arun Kumar
```

---

## 11.3 Create Patient

Patient fields:

```text
Name
```

Patient ID is system-generated.

Created timestamp is system-generated.

Do not add phone/email/date-of-birth fields unless explicitly requested later.

After creation, take the user into the patient's details/analysis workflow.

---

## 11.4 Patient Details

Display:

```text
Patient ID
Name
Created At
```

Then show Analysis History.

Suggested columns:

```text
Date
Diagnosis
Confidence
T-score
Z-score
View
```

Each analysis must have its own record.

Provide:

```text
[ New Analysis ]
[ Delete Patient ]
```

Deleting a patient must also handle its analyses and associated local images after confirmation.

---

# 12. New Analysis page

The user reaches this page only after selecting a patient.

## 12.1 X-ray upload

Provide a modern drag-and-drop / file picker UI:

```text
Upload Knee X-ray

Drag & drop image here
or
[ Choose Image ]
```

Allowed formats:

```text
PNG
JPG
JPEG
WEBP
```

After selecting an image, show a preview:

```text
X-ray Preview
[ image ]

[ Change Image ]
```

Validate file format and reasonable file size.

Do not expose backend stack traces to the frontend.

---

# 13. Clinical form

User-facing inputs:

```text
Age
Gender
Height (m)
Weight (kg)
BMI (auto-calculated)
Joint Pain
Number of Pregnancies
```

## BMI

BMI must be calculated automatically:

```text
BMI = Weight / Height²
```

Example:

```text
Height = 1.58 m
Weight = 68 kg
BMI = 27.24
```

BMI must be read-only in the UI.

The backend must recalculate BMI from height and weight and use the backend-calculated value for inference.

Do not trust a client-supplied BMI value.

## Gender / pregnancy behavior

When gender is Male:

```text
Number of Pregnancies = 0
```

The pregnancy field is disabled automatically.

When gender is Female:

```text
Number of Pregnancies = required numeric input
```

Keep this simple. No "Not provided" option.

---

# 14. Input validation

Validate on both frontend and backend.

At minimum:

```text
Age > 0
Height > 0
Weight > 0
BMI derived from valid values
Pregnancy = 0 for Male
Pregnancy required for Female
Joint Pain is a supported value
Gender is a supported value
X-ray is a supported image format
```

Use sensible bounds to prevent obviously invalid inputs.

Do not silently accept malformed requests.

---

# 15. Inference behavior

When the user clicks:

```text
[ Run Analysis ]
```

show an analysis/loading state.

Example:

```text
Analyzing X-ray...

✓ Image uploaded
✓ X-ray classification
● Estimating bone scores
○ Preparing results
```

Disable repeated submission while the request is running.

---

# 16. Backend prediction pipeline

FastAPI should implement a single orchestrated prediction service.

Conceptually:

```text
Request
 ↓
Validate patient + clinical inputs
 ↓
Save/prepare uploaded image
 ↓
Apply exact DINOv2 inference preprocessing
 ↓
DINOv2 model
 ↓
Class ID + probabilities
 ↓
Recalculate BMI
 ↓
Build 9-value clinical feature vector
 ↓
T-score RF
 ↓
Z-score GB
 ↓
Calculate empirical model ranges
 ↓
Return structured result
```

Do not duplicate this logic across API routes.

---

# 17. Result page

The result page should be clear and simple.

## 17.1 X-ray classification

Display:

```text
X-ray Classification

Predicted Class
Osteopenia

Confidence
93.27%
```

Then class probabilities:

```text
Normal          2.81%
Osteopenia     93.27%
Osteoporosis    3.92%
```

The actual values must come from the model response; the above numbers are only an example of presentation.

Do not hard-code example results.

## 17.2 Bone score estimates

Display:

```text
Estimated T-score
-1.92

Estimated range
-2.29 to -1.55
```

and:

```text
Estimated Z-score
-0.96

Estimated range
-2.18 to 0.26
```

The UI must clearly use wording such as:

```text
Model-estimated T-score
Model-estimated Z-score
```

These are model estimates, not measured DXA/QUS values and not clinical confidence intervals.

## 17.3 Patient information

Show the inputs used for the analysis:

```text
Patient ID
Name
Age
Gender
Height
Weight
BMI
Joint Pain
Number of Pregnancies
```

## 17.4 Actions

Provide:

```text
[ Save Analysis ]
[ View Patient History ]
```

If the application saves automatically at analysis creation time, the UI should clearly indicate that instead of creating duplicate records.

---

# 18. T-score / Z-score range logic

The current model-based empirical margins are:

```text
T-score margin: ±0.3715
Z-score margin: ±1.2232
```

Calculate:

```text
T-score lower = prediction - 0.3715
T-score upper = prediction + 0.3715

Z-score lower = prediction - 1.2232
Z-score upper = prediction + 1.2232
```

Use metadata/configuration rather than scattering these values across frontend code.

These ranges are empirical prediction-error ranges used by this project. Do not label them as medical confidence intervals.

---

# 19. Database design

Use PostgreSQL.

## 19.1 patients table

Suggested fields:

```text
id                primary key
patient_code      unique
name
created_at
```

`patient_code` is the user-facing ID such as `P0001`.

## 19.2 analyses table

Suggested fields:

```text
id
patient_id             foreign key
image_path
created_at

age
gender
height
weight
bmi
joint_pain
pregnancies

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

Add appropriate indexes and foreign-key behavior.

A patient can have many analyses.

---

# 20. Image storage

Do not store X-ray binary data in PostgreSQL for V1.

Store images locally under:

```text
storage/uploads/
```

Recommended organization:

```text
storage/uploads/P0001/A0001_xray.webp
```

The database stores the image path/reference.

The storage layer must be isolated so a later migration to object storage can be done without redesigning the database schema.

---

# 21. API

Implement at least:

```text
GET    /api/health

POST   /api/patients
GET    /api/patients
GET    /api/patients/{patient_id}
DELETE /api/patients/{patient_id}

POST   /api/analyses
GET    /api/patients/{patient_id}/analyses
GET    /api/analyses/{analysis_id}
DELETE /api/analyses/{analysis_id}
```

The main analysis endpoint should accept multipart form data because an X-ray image is uploaded with clinical fields.

The response must be structured JSON and contain all result fields needed by the frontend.

---

# 22. Model loading

Load models once during FastAPI startup/application initialization.

Do not load `.pth`/`.joblib` files separately for every HTTP request.

Handle model-loading failures clearly in backend logs and return a safe API error if inference cannot run.

---

# 23. Model compatibility requirements

The DINOv2 implementation must match the training/inference setup used to create the supplied checkpoint.

Known model configuration:

```text
Architecture: DINOv2 ViT-S/14
Input size: 518
Feature dimension: 384
Classification classes: 3
```

Use the same normalization and preprocessing expected by the trained checkpoint.

Do not casually substitute another DINOv2 variant or image preprocessing pipeline.

If exact preprocessing details are required from the supplied training code/checkpoint metadata, inspect the existing project/model metadata before implementation.

---

# 24. Security and privacy

This is a local-first application storing patient-related information and medical images.

Requirements:

- Keep PostgreSQL local through Docker.
- Do not expose database ports publicly beyond local development unless explicitly configured later.
- Keep secrets in `.env`.
- Add `.env` to `.gitignore`.
- Do not commit patient images/data.
- Do not expose backend stack traces to users.
- Support deletion of patient records and associated images.
- Do not send patient information or X-rays to third-party services in this phase.

No login/authentication system is required in V1.

---

# 25. Medical presentation requirements

The application is an AI-assisted screening/research system.

Use language such as:

```text
AI-assisted screening
Model prediction
Model-estimated T-score
Model-estimated Z-score
```

Do not present the model as producing a definitive clinical diagnosis.

Do not label the estimated T-score/Z-score as measured DXA/QUS results.

Do not invent medical recommendations or medical evidence.

---

# 26. Error handling

Handle at least:

```text
Invalid X-ray format
Oversized image
Missing patient
Invalid age
Invalid height
Invalid weight
Missing female pregnancy value
Backend unavailable
Database connection failure
Model loading failure
Inference failure
```

Frontend should display short user-friendly messages.

Backend logs should contain technical details.

---

# 27. Testing requirements

Before considering V1 complete, test:

## Backend

- Health endpoint
- Patient CRUD behavior
- Analysis creation
- Analysis retrieval
- Analysis deletion
- Patient deletion
- Database relationships
- Input validation
- Model loading
- Prediction response

## ML integration

Use at least one known test image and verify that the web backend can reproduce the intended model inference pipeline.

Verify that:

```text
DINOv2 class → clinical model Class input
```

is automatic and correctly mapped.

## Frontend

Verify:

- Navigation
- Patient creation
- Duplicate patient names
- Image upload/preview
- BMI auto-calculation
- Male pregnancy disabling
- Female pregnancy requirement
- Loading state
- Result rendering
- Patient history
- Delete confirmation

## End-to-end

Complete one flow:

```text
Create patient
→ Upload X-ray
→ Enter clinical details
→ Run analysis
→ DINOv2 result
→ T/Z results
→ Save
→ View patient history
→ Open saved analysis
```

---

# 28. UX requirements

Keep the application modern, clean, and simple.

Prioritize:

- Clear form labels
- Large readable result cards
- Clear prediction/confidence
- Clear T-score/Z-score presentation
- Responsive layout
- Consistent loading states
- Clear error messages
- Minimal unnecessary UI

Do not add complex charts or dashboards unless they directly improve the current workflow.

---

# 29. V1 acceptance criteria

V1 is complete only when all of the following work locally:

### Environment

- Docker Desktop works
- PostgreSQL runs through Docker
- pgAdmin connects to PostgreSQL
- frontend starts locally
- backend starts locally

### Patients

- Create patient
- Generate unique patient ID
- Duplicate names allowed
- View patient
- Delete patient

### Analysis

- Select/create patient
- Upload knee X-ray
- Preview image
- Enter required clinical data
- BMI auto-calculated
- Backend recalculates BMI
- Male pregnancy auto-set to 0 and disabled
- Female pregnancy required
- Run analysis

### ML

- DINOv2 model loads
- Correct preprocessing applied
- DINOv2 class/probabilities returned
- Predicted class automatically passed into clinical models
- T-score model returns estimate
- Z-score model returns estimate
- T/Z ranges displayed

### Storage

- X-ray saved to local storage
- image path saved in PostgreSQL
- analysis saved
- multiple analyses per patient supported
- history displayed
- previous analyses preserved
- delete works

### Result

- classification displayed
- confidence displayed
- class probabilities displayed
- T-score estimate/range displayed
- Z-score estimate/range displayed
- patient inputs displayed
- save/history actions work

---

# 30. Future extension point — RAG/LLM

Do not implement now.

The architecture must leave clean extension points for:

```text
Saved analysis
      ↓
Case context
      ↓
RAG retrieval from trusted medical knowledge
      ↓
LLM synthesis
      ↓
Evidence-based clinical decision-support report
```

Do not create placeholder RAG/LLM features that do nothing. Keep only clean service/API boundaries that make the future addition straightforward.

---

# 31. Devin implementation instructions

1. Start by inspecting the current contents of the repository.
2. Work directly in `Knee-Osteoporosis-AI`.
3. Do not create a new repository.
4. Do not retrain any ML model.
5. Do not replace DINOv2 with another model.
6. The user will copy the trained model files into `backend/models/`.
7. Provide a clear model-folder README or documentation explaining exactly where each supplied model file must be placed.
8. Build PostgreSQL and pgAdmin with Docker Compose.
9. Do not require native PostgreSQL Server installation on Windows.
10. Keep secrets in `.env` and provide `.env.example`.
11. Implement backend inference in Python/FastAPI.
12. Keep model inference out of React.
13. Implement patient + analysis relational storage.
14. Support many analyses for one patient.
15. Store image files locally and image paths in PostgreSQL.
16. Implement automatic BMI calculation in the UI and authoritative BMI recalculation in the backend.
17. Automatically disable pregnancy input for male and set it to 0.
18. Require a pregnancy value for female.
19. Never let the user manually choose the DINOv2 class used by Model 2.
20. Pass DINOv2 class ID automatically into Model 2.
21. Preserve the model's expected feature order.
22. Display model-estimated T-score/Z-score and their empirical ranges clearly.
23. Do not call the ranges clinical confidence intervals.
24. Keep V1 limited to analysis + result display + storage.
25. Do not implement RAG, vector DB, or LLM yet.
26. Add tests for the core workflow.
27. Update README with exact setup and run commands.
28. Keep the implementation simple enough for local development and debugging.
29. Avoid unnecessary dependencies.
30. At the end, report what was implemented, what commands to run, and what remains for the future RAG phase.

---

# 32. Final target architecture

```text
                    React Frontend
                           │
                           │ HTTP / JSON / Multipart
                           ↓
                    FastAPI Backend
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ↓             ↓             ↓
        PostgreSQL    ML Inference   Local Storage
        (Docker)         │          (X-ray images)
             │           │
             │      ┌────┴─────┐
             │      │          │
             │   DINOv2    Clinical Models
             │               │
             │         ┌─────┴─────┐
             │         │           │
             │      T-score      Z-score
             │         │           │
             └─────────┴───────────┘
                       ↓
                 Analysis Result
                       ↓
                 Patient History
```

This is the complete V1 target.

**Stop development at the result/history stage. Do not proceed into RAG/LLM implementation unless explicitly instructed in a later phase.**

## 45. Devin interaction, setup checks, and Git initialization

### Ask questions before making irreversible architectural decisions

Devin must not silently guess when an important implementation detail is ambiguous or when a required local dependency/configuration is missing.

Before implementation, inspect the repository and `PRD.md`, then ask me concise questions for any blocking ambiguity. In particular, ask me when:
- an existing repository component conflicts with this PRD;
- an external service, API, credential, or package choice is required but not specified;
- the current environment is missing a required tool or extension;
- a setup decision could materially affect the architecture or data/model compatibility.

Do not ask unnecessary questions for decisions already specified in this PRD. Prefer sensible defaults when the decision is low-risk and reversible, and state what you selected.

### Tell me what I need to install or configure

If implementation requires a missing VS Code extension, Python package, Node package, Docker/WSL component, PostgreSQL/pgAdmin configuration, environment variable, or other local setup, tell me clearly:
1. what is missing;
2. why it is required;
3. the exact installation/setup step or command;
4. how to verify it.

Do not assume that I have installed project-specific extensions or dependencies just because VS Code is installed.

The base tools I already have are:
- VS Code
- Devin
- Git
- Python
- Node.js + npm
- Docker Desktop

Docker has already been installed and verified locally. PostgreSQL Server will NOT be installed directly on Windows; PostgreSQL and pgAdmin should run through Docker as specified above.

### Git repository initialization

This project must be initialized and developed as a Git repository in the existing project/repository location.

Devin must:
- inspect whether Git is already initialized;
- initialize Git with `git init` if needed;
- connect the local repository to the existing GitHub repository when appropriate:
  `https://github.com/Santhoshkumar0913/Knee-Osteoporosis-AI.git`;
- create a suitable `.gitignore` before committing generated/local files;
- make an initial baseline commit after the project setup is valid, unless the repository already contains appropriate commits and history;
- never overwrite or discard existing Git history without asking me first;
- never force-push or perform destructive Git operations without asking me first.

### Model files and Git safety

I will manually copy the trained ML model files into the backend model directory after Devin creates the folder structure.

Expected files:
- `dinov2_experiment2_best.pth`
- `t_score_random_forest.joblib`
- `z_score_gradient_boosting.joblib`
- `model_metadata.json`

By default, the large trained model/checkpoint files must NOT be committed to GitHub.

The `.gitignore` must explicitly protect large model artifacts, at minimum:
- `*.pth`
- `*.pt`
- `*.ckpt`

Also ignore other generated/local model artifacts where appropriate, while NOT ignoring `model_metadata.json` unless there is a specific reason.

After creating `backend/models/`, Devin must leave a clear README or placeholder/instruction file there explaining that I need to manually copy the four trained files into that folder.

Do not upload, commit, or push the model weights/checkpoints to GitHub unless I explicitly request it.

### Repository safety

Before modifying files, Devin must inspect the existing repository state with Git and the filesystem.
Do not delete existing project files simply to create a cleaner structure.
If an existing implementation can be reused safely, prefer adapting it.
If a conflict requires removing or replacing an existing component, explain the conflict before making a destructive change.
