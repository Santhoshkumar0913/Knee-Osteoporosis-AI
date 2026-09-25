# Phase 3 — X-ray Visualization, Grad-CAM XAI, and PDF Clinical Support

## 1. Purpose

This document defines the next implementation phase for the
**Knee Osteoporosis AI** project.

It is subordinate to the root `PRD.md`.

The root project documents are:

```text
PRD.md
README.md
```

The root `PRD.md` is the single authoritative product specification for the
whole project. This file is the Phase 3 implementation plan and tracker.

---

## 2. Phase 3 Scope

Phase 3 adds:

1. Original saved knee X-ray display.
2. Grad-CAM explainability for the existing DINOv2 classifier.
3. X-ray + Grad-CAM visualization.
4. XAI information in Analysis Result.
5. XAI information in Clinical Support.
6. PDF Clinical Support report generation.
7. PDF report download from the Clinical Support page.

### Phase 3 status at the start of this document

```text
Original saved X-ray display    NOT IMPLEMENTED
Grad-CAM                        NOT IMPLEMENTED
X-ray + heatmap visualization  NOT IMPLEMENTED
XAI API                        NOT IMPLEMENTED
Clinical Support XAI UI        NOT IMPLEMENTED
PDF generation                 NOT IMPLEMENTED
PDF download                   NOT IMPLEMENTED
```

Do not describe these features as already implemented.

---

## 3. Current Verified Architecture

The current analysis workflow is:

```text
POST /api/analyses
    ↓
Validate patient + uploaded image
    ↓
PredictionService.run_analysis
    ↓
DINOv2 preprocessing and classification
    ↓
Normal / Osteopenia / Osteoporosis
    ↓
Build existing V1 clinical feature vector
    ↓
Random Forest T-score
    ↓
Gradient Boosting Z-score
    ↓
Create Analysis database row
    ↓
Save original X-ray locally
    ↓
Return Analysis to frontend
```

Clinical Support:

```text
Analysis Result
    ↓
POST /api/analyses/{analysis_id}/clinical-support
    ↓
Load saved analysis/context
    ↓
Build retrieval query
    ↓
BGE embedding
    ↓
PostgreSQL + pgvector similarity search
    ↓
Retrieve top evidence chunks
    ↓
OpenRouter
    ↓
Structured Clinical Support
    ↓
Clinical Support UI
```

Important as-built clarification:

```text
Current runtime RAG retrieval:
SQLAlchemy + PostgreSQL + pgvector

LlamaIndex:
dependency present, but NOT the active runtime retrieval executor
```

---

## 4. Repository Inspection Findings

### DINOv2

Current source:

```text
backend/app/services/image_model.py
```

The project constructs:

```python
timm.create_model(
    "vit_small_patch14_dinov2",
    num_classes=0,
    pretrained=False
)
```

Custom classifier:

```text
LayerNorm(384)
→ Dropout(0.40)
→ Linear(384 → 128)
→ GELU
→ Dropout(0.30)
→ Linear(128 → 3)
```

Configured input:

```text
518 × 518
```

Feature dimension:

```text
384
```

Classes:

```text
1 → Normal
2 → Osteopenia
3 → Osteoporosis
```

Checkpoint:

```text
backend/models/dinov2_experiment2_best.pth
```

### Important verification status

The exact runtime timm module structure must be verified before implementing
Grad-CAM.

The earlier inspection environment did not have `timm` installed, so these
details must NOT be assumed:

```text
exact target layer
exact token count
special/register token count
exact activation shape
```

---

## 5. Existing Image Storage

Current X-rays are stored locally.

The existing storage flow is:

```text
uploaded image bytes
    ↓
StorageService.save_analysis_image(...)
    ↓
storage/uploads/<patient_code>/<analysis_id>_xray.<extension>
```

The database stores:

```text
Analysis.image_path
```

There is currently:

```text
no image-serving endpoint
no static image mount
```

`get_full_image_path()` exists as a helper but is not currently used to serve
images to the frontend.

Therefore, original X-ray display is a backend integration task, not a
frontend-only change.

---

# 6. Phase 3 Architecture

Target workflow:

```text
Saved Analysis
    ├── Prediction
    ├── T-score
    ├── Z-score
    ├── Clinical Context
    └── Original X-ray
             ↓
        XAI Service
             ↓
          Grad-CAM
             ↓
   Original + Heatmap Overlay
             ↓
      Analysis Result
             ↓
      Clinical Support
             ↓
        PDF Report
```

---

# 7. Phase 3A — Runtime DINOv2 Verification

## Objective

Verify the exact runtime ViT architecture before writing Grad-CAM code.

## Requirements

Use the existing model construction and checkpoint.

Do not change:

```text
model architecture
classifier architecture
checkpoint
training weights
prediction preprocessing
```

Inspect:

```text
backbone module names
backbone blocks
target layer candidates
forward output
forward_features behavior
activation shape
token count
special-token count
patch grid
```

The expected patch grid may be:

```text
518 / 14 = 37
37 × 37 = 1369 patch positions
```

But this must be verified at runtime.

## Candidate target layer

A late transformer normalization layer such as:

```text
backbone.blocks[-1].norm1
```

is a candidate.

It is NOT approved until its actual runtime activation shape is inspected.

## Required output from verification

Record:

```text
Exact target layer:
Activation shape:
Total tokens:
Patch tokens:
Class token:
Register/special tokens:
Embedding dimension:
Patch grid:
Required reshape:
```

Stop if the model/checkpoint cannot be instantiated correctly.

---

# 8. Phase 3B — Grad-CAM Prototype

## Rules

Do not retrain.

Do not replace DINOv2.

Do not change the trained classifier.

Reuse the exact existing preprocessing.

The preprocessing path must remain:

```text
RGB
→ aspect-ratio-preserving resize
→ LANCZOS
→ centered zero padding
→ 518 × 518
→ ToTensor
→ ImageNet normalization
```

## Target

Grad-CAM must be generated against the selected model class.

For the normal workflow:

```text
selected class = model predicted class
```

Do not allow the UI to silently claim an explanation for another class.

## ViT reshape

Only use the reshape after runtime verification.

Conditional example:

```text
[1, 1370, 384]
    ↓ remove class token
[1, 1369, 384]
    ↓
[1, 37, 37, 384]
    ↓ permute
[1, 384, 37, 37]
```

If runtime inspection finds additional special tokens, remove the verified
non-patch tokens instead.

Do not hard-code assumptions without verification.

---

# 9. Grad-CAM Implementation

Preferred initial approach:

```text
small custom Grad-CAM implementation
```

Reason:

- ViT token-to-spatial conversion is explicit.
- target class selection remains visible.
- hook lifetime can be controlled.
- request-scoped activation/gradient state can be managed explicitly.
- unnecessary dependency growth is avoided.

An established Grad-CAM package may be used instead if runtime testing shows
it is safer and integrates cleanly.

Do not add a new dependency merely because it is convenient.

---

# 10. Hook and Concurrency Requirements

The current DINOv2 model is exposed through a process-level singleton.

Do NOT store temporary activation/gradient state on the singleton in a way
that can leak across requests.

Requirements:

```text
register hook
→ execute one Grad-CAM request
→ collect activations/gradients
→ remove hook in finally
```

Avoid persistent request state on the model object.

If concurrent Grad-CAM requests are possible, isolate or serialize the
Grad-CAM execution so one request cannot mix activations or gradients with
another.

Normal prediction behavior must remain unaffected.

---

# 11. Phase 3C — Original X-ray Endpoint

Add a controlled endpoint following existing API conventions.

Suggested:

```text
GET /api/analyses/{analysis_id}/image
```

Requirements:

- validate analysis exists;
- verify an image path is present;
- resolve the image safely;
- verify the target file exists;
- return the image;
- support PNG/JPG/JPEG/WEBP;
- reject path traversal;
- do not expose raw filesystem paths;
- use appropriate HTTP errors.

Do not expose arbitrary storage files.

---

# 12. Phase 3D — XAI Endpoint

Suggested:

```text
GET /api/analyses/{analysis_id}/xai
```

The exact response contract should follow project conventions.

Possible shape:

```json
{
  "analysis_id": 1,
  "predicted_class": "Osteoporosis",
  "confidence": 0.818,
  "original_image_url": "/api/analyses/1/image",
  "heatmap_url": "/api/analyses/1/xai/heatmap",
  "overlay_url": "/api/analyses/1/xai/overlay",
  "explanation_note": "Grad-CAM visualization showing image regions that contributed to the model's selected prediction."
}
```

Do not create duplicate endpoints unnecessarily.

The final contract should be chosen after inspecting the current API style.

---

# 13. XAI Artifact Handling

The original X-ray must remain unchanged.

Generated XAI artifacts may use a controlled location such as:

```text
storage/xai/<patient_code>/<analysis_id>/
```

Possible outputs:

```text
heatmap
overlay
```

Prefer on-demand generation unless the implementation demonstrates a clear
benefit to persistent caching.

Do not save sensitive or unnecessary duplicate information.

---

# 14. XAI Medical Language

Use:

```text
Grad-CAM visualization showing image regions that contributed
to the model's selected prediction.
```

Do NOT use:

```text
The heatmap proves osteoporosis.
The highlighted region is definitely diseased.
The heatmap confirms the diagnosis.
The AI found the disease.
```

Grad-CAM is an explainability aid, not a diagnostic proof or confirmed
anatomical pathology map.

---

# 15. Phase 3E — Analysis Result UI

Update the existing:

```text
frontend/src/pages/AnalysisResult/
```

Add a clear X-ray section.

Recommended:

```text
X-ray Analysis

┌────────────────────┬────────────────────┐
│ Original X-ray     │ Grad-CAM Overlay   │
│                    │                    │
│      image         │   image + heatmap  │
└────────────────────┴────────────────────┘
```

Below the visualization:

```text
Grad-CAM visualization showing image regions that contributed
to the model's selected prediction.
```

Keep existing result information:

```text
Predicted Class
Confidence
Class Probabilities
Model-estimated T-score
T-score Range
Model-estimated Z-score
Z-score Range
Clinical Context
```

Keep existing actions:

```text
View Patient History
View Clinical Support
New Analysis
```

---

# 16. Phase 3F — Clinical Support UI

Update:

```text
frontend/src/pages/ClinicalSupport/
```

Add:

```text
Original X-ray
Grad-CAM Overlay
```

Keep the current structured Clinical Support sections:

```text
Explanation
What You Can Do Now
Talk to Your Doctor About
Testing and Follow-up
Treatment Information
Sources
```

Also retain:

```text
Grounding Note
Disclaimer
Regenerate
```

Add:

```text
Download PDF Report
```

No notification icon.

No user/profile indicator.

---

# 17. Clinical Support Grounding Rules

The LLM must preserve the distinction between:

```text
DINOv2 model prediction
```

and:

```text
model-estimated T-score
model-estimated Z-score
```

Never describe model-estimated T/Z values as:

```text
DXA results
QUS results
bone-density test results
laboratory results
```

The LLM must not treat Grad-CAM as medical evidence.

The LLM must not describe highlighted image regions as confirmed disease.

The LLM must not independently override the DINOv2 prediction based only on
the model-estimated T/Z values.

---

# 18. Phase 3G — PDF Generation

Create a dedicated PDF service, for example:

```text
backend/app/services/pdf_service.py
```

Use on-demand generation.

Preferred:

```text
GET PDF request
→ load saved analysis
→ obtain current Clinical Support response
→ obtain X-ray/XAI assets
→ generate PDF
→ stream response
```

Avoid permanent PDF storage unless later requirements justify it.

---

# 19. PDF Content

The report should contain:

## Header

```text
Knee Osteoporosis AI
Clinical Support Report
```

## 1. Patient Information

Use only real patient fields:

```text
Patient ID
Patient Code
Name
Age
Gender
Analysis Date
```

Do NOT include:

```text
Phone
Email
Address
Date of Birth
```

## 2. Clinical Context

```text
Height
Weight
BMI
Joint Pain
Number of Pregnancies
Menopausal Status
Smoking
Alcohol
Previous Fracture
Long-term Steroid Use
```

## 3. X-ray Analysis

```text
Original X-ray
Grad-CAM Overlay
```

## 4. Model Prediction

```text
Predicted Class
Confidence
Normal Probability
Osteopenia Probability
Osteoporosis Probability
```

## 5. Bone Score Estimates

```text
Model-estimated T-score
T-score Range

Model-estimated Z-score
Z-score Range
```

## 6. Clinical Support

```text
Explanation
What You Can Do Now
Talk to Your Doctor About
Testing and Follow-up
Treatment Information
```

## 7. Evidence Sources

Use actual retrieved metadata.

Do not invent citations.

## 8. Grounding Note

Use the Clinical Support grounding note.

## 9. Disclaimer

Use:

```text
AI-assisted guidance for informational purposes.
This does not replace a doctor's diagnosis or treatment decision.
Discuss medical decisions with your doctor.
```

---

# 20. Clinical Support / PDF Consistency

Current Clinical Support is generated on demand and is not stored.

Therefore the preferred behavior is:

```text
Clinical Support generated
        ↓
Displayed in UI
        ↓
Download PDF
        ↓
PDF uses the response currently displayed
```

Do not silently call the LLM again for the same PDF when the current response
is already available.

If a future implementation needs the PDF endpoint to work independently
without a current frontend response, define that behavior explicitly and
document the possibility of regenerated content.

---

# 21. Height Display Correction

The backend stores height in meters.

Use:

```text
Height: 1.73 m
```

Do not display:

```text
Height: 1.73 cm
```

The New Analysis page already uses meters, and Analysis Result uses meters.
Clinical Support must follow the same convention.

---

# 22. Date Display

Keep the database `created_at` datetime fields.

Display dates as date-only in the UI:

```text
25 Sep 2026
```

Do not display the time unless a later requirement explicitly needs it.

---

# 23. PDF Dependency

Current backend dependencies include `pypdf`, but:

```text
pypdf = PDF text extraction
```

It is NOT a PDF report-generation solution.

Before implementation, choose a suitable PDF-generation method and add only
the required dependency.

Possible approaches may include:

```text
ReportLab
HTML/CSS → PDF renderer
```

The selected approach must work reliably in the project's environment.

---

# 24. Testing Requirements

## Runtime DINOv2

Test:

- checkpoint loads;
- target layer exists;
- activation shape is as expected;
- token count is verified;
- reshape is valid.

## Grad-CAM

Test:

- correct target class;
- finite values;
- non-empty heatmap;
- expected dimensions;
- overlay generation;
- repeated requests do not leak state;
- concurrent requests cannot mix state.

## Image endpoint

Test:

- valid analysis;
- missing analysis;
- missing image;
- unsupported image;
- traversal rejection.

## PDF

Test:

- valid report;
- required sections;
- X-ray included;
- Grad-CAM included;
- Clinical Support included;
- sources included;
- disclaimer included;
- error handling.

## Regression

Existing functionality must continue to work:

```text
patient creation
patient listing
patient details
analysis creation
DINOv2 prediction
T-score
Z-score
patient history
analysis deletion
RAG retrieval
Clinical Support
OpenRouter parsing
```

Frontend:

```bash
npm run build
npm run lint
```

---

# 25. Visual Validation

Grad-CAM is not complete merely because the API returns an image.

Generate and inspect several representative X-rays.

Verify:

```text
heatmap is not blank
heatmap is not uniformly active
overlay aligns with X-ray
dimensions are correct
selected class is correct
no obvious token reshape distortion
no severe artifacts
```

Keep visual validation evidence with the implementation notes.

---

# 26. Do Not Change Unrelated Areas

Do not:

- rewrite the existing frontend;
- replace DINOv2;
- retrain the model;
- modify the existing T-score model;
- modify the existing Z-score model;
- replace PostgreSQL/pgvector;
- replace the RAG architecture;
- add authentication;
- add notifications;
- add user profiles;
- add phone/email;
- add patient search;
- add Knowledge Base route;
- add About route;
- add fake medical data.

---

# 27. Phase 3 Implementation Order

```text
Phase 3A
Runtime DINOv2 verification
        ↓
Phase 3B
One-image Grad-CAM prototype
        ↓
Phase 3C
Visual Grad-CAM validation
        ↓
Phase 3D
Original X-ray endpoint
        ↓
Phase 3E
XAI endpoint
        ↓
Phase 3F
Analysis Result UI
        ↓
Phase 3G
Clinical Support UI
        ↓
Phase 3H
PDF service
        ↓
Phase 3I
PDF download UI
        ↓
Phase 3J
Full regression
```

---

# 28. Agent Operating Rules

Before each implementation phase:

1. Inspect relevant existing code.
2. Make the smallest change necessary.
3. Reuse existing conventions.
4. Run targeted tests.
5. Report changed files.
6. Report verification results.
7. Stop if a required assumption fails.

Do not move to the next phase after a failed verification.

---

# 29. Git Workflow

Use:

```text
feature/rag-llm
```

Do not modify:

```text
main
```

After each completed logical feature:

```bash
git status
git add <specific files>
git commit -m "<simple one-line message>"
git push origin feature/rag-llm
```

Preferred commit messages:

```text
add xray image endpoint
add grad cam prototype
add xai endpoint
update analysis result xai
update clinical support xai
add clinical support pdf
add pdf download
```

Do not add emojis, prefixes, or unrelated commit information.

---

# 30. Definition of Done

```text
[ ] Runtime DINOv2 structure verified
[ ] Exact Grad-CAM target verified
[ ] Exact token reshape verified
[ ] Grad-CAM prototype works
[ ] Grad-CAM visually validated
[ ] Original X-ray endpoint works
[ ] Original X-ray shown in Analysis Result
[ ] Grad-CAM shown in Analysis Result
[ ] X-ray and Grad-CAM shown in Clinical Support
[ ] Clinical Support grounding rules preserved
[ ] T/Z remain clearly model estimates
[ ] PDF generation works
[ ] PDF contains original X-ray
[ ] PDF contains Grad-CAM
[ ] PDF contains predictions/probabilities
[ ] PDF contains T/Z estimates and ranges
[ ] PDF contains clinical context
[ ] PDF contains Clinical Support
[ ] PDF contains sources
[ ] PDF contains grounding note
[ ] PDF contains disclaimer
[ ] Frontend build passes
[ ] Frontend lint passes or existing warnings documented
[ ] Backend tests pass
[ ] Regression tests pass
[ ] Git working tree clean
[ ] Changes pushed to feature/rag-llm
```
