# Phase 3 — As-Built X-ray Visualization, Experimental Grad-CAM, and PDF Clinical Support

## 1. Purpose

This document tracks the implemented Phase 3 state for the
**Knee Osteoporosis AI** project, including verification, research limitations,
and features intentionally excluded from Clinical Support and PDF.

It is subordinate to the root `PRD.md`.

The root project documents are:

```text
PRD.md
README.md
```

The root `PRD.md` is the single authoritative product specification for the
whole project. This file is the Phase 3 as-built implementation tracker.

---

## 2. Phase 3 Implemented Scope and Status

Phase 3 implementation state:

### Current Phase 3 status

| Phase 3 item | As-built status |
|---|---|
| DINOv2 runtime verification | Verified against the existing checkpoint and runtime model |
| One-image Grad-CAM prototype | Implemented; hooks removed in `finally`; model forwards serialized |
| Grad-CAM validation | Research visual validation completed; padding attribution is inconsistent and padding sensitivity changed at least one sample's prediction |
| Original X-ray API | Implemented and verified: `GET /api/analyses/{analysis_id}/image` |
| Original X-ray UI | Implemented in Analysis Result and Clinical Support |
| XAI API | Implemented on demand: `GET /api/analyses/{analysis_id}/xai` |
| Grad-CAM UI | Implemented experimentally on Analysis Result only, with research-only warning |
| Clinical Support Grad-CAM | Intentionally excluded |
| Clinical Support grounding correction/refinement | Implemented; model estimates remain distinct from the DINOv2 class; terminology and saved-context grounding safeguards are covered by tests |
| PDF generation/download | Implemented on demand in memory from the currently displayed Clinical Support response and saved original X-ray |
| Grad-CAM in PDF | Intentionally excluded |

This tracker distinguishes implementation from validation: Grad-CAM is
implemented and displayed experimentally, but it has not been clinically
validated and must not be represented as confirmed anatomical disease
localization.

### Current implementation status

Phase 3A runtime verification and Phase 3B one-image Grad-CAM prototype are
complete. Phase 3C research validation is complete. It found inconsistent
Grad-CAM attribution to letterbox padding, including disproportionate padding
attribution on some samples and measurable prediction sensitivity to padding
in at least one sample. The comparison covered `blocks[5].norm1`,
`blocks[8].norm1`, `blocks[10].norm1`, and `blocks[11].norm1` across multiple
representative X-rays, with content-region and padding attribution inspected.
The visualization remains experimental and is not clinical evidence or
confirmed anatomical disease localization. The only user-visible use is the
explicitly research-only overlay on Analysis Result. Keep the full attribution,
including padding attribution, visible.

Phase 3D added the controlled original saved X-ray API. Phase 3E integrates
that original image into Analysis Result, and the same original image is shown
in Clinical Support. Phase 3F implements an on-demand XAI API; Phase 3G shows
its experimental Grad-CAM overlay only on Analysis Result. Clinical Support
has no Grad-CAM UI, and PDF reports exclude Grad-CAM by design. The Phase 3C
padding-attribution limitation and research-only warning remain visible with
the Analysis Result visualization.

The Clinical Support grounding correction labels the DINOv2 class, both
clinical-model score estimates, and retrieved RAG evidence separately. The
retrieval query and LLM instructions name T/Z values as model estimates. The
response parser fails closed to a deterministic, analysis-grounded explanation
when generated content describes an estimate as a measurement or contradicts
the recorded DINOv2 class. Explanation generation also uses saved clinical
context and retrieved evidence for cautious interpretation, without inventing
perimenopausal status, fracture history, or other patient facts. Unit tests pass.
An earlier live OpenRouter generation used synthetic, non-patient validation
data to check terminology. The latest context-dependent Explanation refinement
is covered by backend tests; it has not been rechecked through a live
OpenRouter request. The local API server was unavailable during the synthetic
check, so the full HTTP endpoint and pgvector retrieval path were not exercised.

Phase 3I/3J generates the Clinical Support PDF on demand in memory. The
Clinical Support page posts its currently displayed response; the PDF endpoint
loads the saved analysis, patient, and original X-ray and does not call the LLM
again or persist the PDF. The report includes only existing patient and
analysis fields, probabilities, model-estimated scores and ranges, the current
Clinical Support sections, actual source metadata, grounding note, and
disclaimer. Grad-CAM remains deliberately excluded from the PDF; the
experimental Analysis Result visualization is not Clinical Support evidence.

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

Original X-ray display in Analysis Result:

```text
Analysis Result loads saved Analysis
    ↓
GET /api/analyses/{analysis_id}/image
    ↓
Resolve and serve that analysis's saved image
    ↓
Display original X-ray
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

### Verified runtime structure

Runtime inspection using the existing model and checkpoint verified:

```text
Backbone: timm VisionTransformer, 12 blocks, embedding dimension 384
Target layer: backbone.blocks[11].norm1
Activation shape: [1, 1370, 384]
Total tokens: 1370
Patch tokens: 1369
Class tokens: 1
Register tokens: 0
Patch grid: 37 × 37
Reshape: remove class token → [1, 1369, 384] → [1, 37, 37, 384] → [1, 384, 37, 37]
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

There is now:

```text
GET /api/analyses/{analysis_id}/image
controlled per-analysis image serving; no static image mount
```

`get_full_image_path()` exists as a helper but is not currently used to serve
images to the frontend.

Analysis Result and Clinical Support load this endpoint using the analysis ID.
Analysis Result separately requests the experimental Grad-CAM endpoint; the
original image endpoint itself serves only the saved original X-ray.

---

# 6. As-Built Phase 3 Architecture

Current workflow (the Grad-CAM branch is separate from Clinical Support and PDF):

```text
Saved Analysis
    ├── Prediction
    ├── T-score
    ├── Z-score
    ├── Clinical Context
    └── Original X-ray
             ├── GET /api/analyses/{analysis_id}/image
             │        ├── Analysis Result
             │        └── Clinical Support
             └── GET /api/analyses/{analysis_id}/xai
                      ↓
                 Grad-CAM overlay
                      ↓
              Analysis Result only

Clinical Support response currently displayed
             ↓
POST /api/analyses/{analysis_id}/clinical-support/pdf
             ↓
     In-memory PDF download
     (original X-ray included;
      Grad-CAM excluded)
```

---

# 7. Phase 3A — Runtime DINOv2 Verification

## Verified Runtime Result

The existing model construction and checkpoint were instantiated and inspected
at runtime before the Grad-CAM prototype was implemented. The verified model
is DINOv2 ViT-Small/14 with 518 × 518 input, embedding dimension 384, and
three output classes.

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

The verified patch grid is:

```text
518 / 14 = 37
37 × 37 = 1369 patch positions
```

The selected and runtime-verified target layer is:

```text
backbone.blocks[11].norm1
```

```text
Activation shape: [1, 1370, 384]
Total tokens: 1370
Patch tokens: 1369
Class tokens: 1
Register tokens: 0
Patch grid: 37 × 37
Grad-CAM reshape: [1, 1370, 384] → remove class token → [1, 1369, 384] → [1, 37, 37, 384] → [1, 384, 37, 37]
```

No model, checkpoint, preprocessing, or classifier changes were made for this
verification.

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

# 9. Grad-CAM Implementation — As Built

The implementation uses:

```text
small custom Grad-CAM implementation
```

The custom implementation keeps:

- ViT token-to-spatial conversion explicit;
- target class selection tied to the model-selected class;
- hook lifetime scoped and removed in `finally`;
- activation/gradient state request-scoped;
- no additional Grad-CAM dependency.

---

# 10. Hook and Concurrency Behavior

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

# 11. Phase 3D — Original X-ray Endpoint (Implemented and Verified)

Implemented endpoint:

```text
GET /api/analyses/{analysis_id}/image
```

The route validates the analysis and image, resolves the per-analysis image
through the storage service, supports PNG/JPG/JPEG/WEBP, and does not expose
arbitrary storage files or raw filesystem paths.

---

# 11A. Phase 3E — Original X-ray in Analysis Result

The completed Analysis Result integration uses:

```text
GET /api/analyses/{analysis_id}/image
```

Phase 3E displayed the saved original X-ray and kept image errors local to the
image section. Phase 3G later added the separate experimental Grad-CAM panel.

---

# 12. Phase 3F — XAI Endpoint (Implemented; Research Only)

Implemented endpoint:

```text
GET /api/analyses/{analysis_id}/xai
```

The endpoint resolves the original image through the existing storage service,
generates Grad-CAM on demand, verifies the model-selected class against the
saved analysis prediction, and returns one PNG data URL. It does not accept a
user-selected class, expose filesystem paths, or store generated files.

Implemented response shape:

```json
{
  "analysis_id": 1,
  "predicted_class": 3,
  "predicted_diagnosis": "Osteoporosis",
  "confidence": 0.818,
  "overlay_image_data_url": "data:image/png;base64,...",
  "explanation_note": "Grad-CAM visualization showing image regions that contributed to the model's selected prediction.",
  "research_only_warning": "This visualization is for research/explainability purposes only and is not a confirmed anatomical disease localization."
}
```

---

# 13. XAI Artifact Handling — As Built

The original X-ray must remain unchanged.

The XAI endpoint generates the overlay on demand and returns it as a PNG data
URL. Heatmaps and overlays are not written to persistent storage. The saved
original X-ray is resolved through the existing per-analysis storage service.

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

# 15. Phase 3G — Analysis Result XAI UI (Implemented; Experimental/Research Only)

The Analysis Result page keeps its Original X-ray section and shows the
experimental Grad-CAM overlay beside it. Loading and errors remain local to
the XAI section so ordinary analysis results and actions remain usable. The
page shows the model-selected prediction, confidence, exact explanation note,
and exact research-only warning. A failure to match the saved prediction
returns a conflict instead of displaying a mismatched explanation.

The implemented Analysis Result contains:

```text
X-ray Analysis

┌────────────────────┬────────────────────┐
│ Original X-ray     │ Grad-CAM Overlay   │
│                    │                    │
│      image         │   image + heatmap  │
└────────────────────┴────────────────────┘
```

The visualization displays this explanation note and the research-only
warning from the API response:

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

# 16. Phase 3H — Clinical Support XAI (Intentionally Excluded)

Grad-CAM is intentionally excluded from Clinical Support. The page displays
the original saved X-ray and structured Clinical Support, but no heatmap or
XAI explanation. The same exclusion applies to PDF reports. Grad-CAM must not
be treated as retrieved evidence or used to generate Clinical Support.

The implemented Clinical Support sections remain:

```text
Explanation
What You Can Do Now
Talk to Your Doctor About
Testing and Follow-up
Treatment Information
Sources
```

The page also retains:

```text
Grounding Note
Disclaimer
Regenerate
```

The page provides:

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

Both values are estimates from the application's clinical models. Patient
context may be discussed only when it is present in the saved analysis and
supported by retrieved evidence. Retrieved source labels are constructed from
retrieved chunk metadata, not generated citations.

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

# 18. Phase 3I — PDF Generation (Implemented)

The dedicated PDF service is implemented at:

```text
backend/app/services/pdf_service.py
```

Generation runs on demand.

Implemented flow:

```text
POST /api/analyses/{analysis_id}/clinical-support/pdf with the currently displayed Clinical Support response
→ load saved analysis and patient
→ resolve original saved X-ray
→ generate PDF in memory
→ stream response without permanent storage
```

The generated PDF is streamed and not permanently stored.

---

# 19. PDF Content

The implemented report contains:

## Header

```text
Knee Osteoporosis AI
Clinical Support Report
```

## 1. Patient Information

It uses only existing patient fields:

```text
Patient ID
Patient Code
Name
Age
Gender
Analysis Date
```

It does not include:

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
```

Do not include Grad-CAM in the PDF. The Analysis Result visualization remains
research-only and is not Clinical Support evidence.

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

The displayed source list uses actual retrieved metadata.

Do not invent citations.

## 8. Grounding Note

The report includes the Clinical Support grounding note.

## 9. Disclaimer

The report includes this disclaimer:

```text
AI-assisted guidance for informational purposes.
This does not replace a doctor's diagnosis or treatment decision.
Discuss medical decisions with your doctor.
```

---

# 20. Clinical Support / PDF Consistency

Current Clinical Support is generated on demand and is not stored.

The implemented behavior is:

```text
Clinical Support generated
        ↓
Displayed in UI
        ↓
Download PDF
        ↓
PDF uses the response currently displayed
```

The implemented download posts that displayed structured response to the PDF
endpoint. The endpoint uses it as-is with the saved analysis and original
image; it does not regenerate Clinical Support and keeps the PDF in memory.

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

The backend uses ReportLab for report generation. `pypdf` remains used for
RAG document text extraction and is not the report-generation library.

ReportLab is declared as `reportlab>=4.2.0` in
`backend/requirements.txt`. The endpoint streams an in-memory PDF and does not
write a permanent report file.

---

# 24. Verification Coverage and Results

## Runtime DINOv2

Verified:

- checkpoint loads;
- target layer exists;
- activation shape is as expected;
- token count is verified;
- reshape is valid.

## Grad-CAM

Covered by implementation and endpoint tests:

- correct target class;
- finite values;
- non-empty heatmap;
- expected dimensions;
- overlay generation;
- repeated requests do not leak state;
- concurrent requests cannot mix state.

## Image endpoint

Covered by endpoint tests:

- valid analysis;
- missing analysis;
- missing image;
- unsupported image;
- traversal rejection.

## Grad-CAM research limitation

Phase 3C validation found inconsistent attribution to the artificial
letterbox padding. Some samples assigned a disproportionate share of
attribution to padding, and a padding sensitivity experiment measurably
changed the prediction for at least one sample. Preserve full attribution for
research inspection; the Analysis Result UI retains the full attribution and
displays a research-only warning. This research visualization is not a
validated clinical explanation and is not confirmed anatomical disease
localization. No clinical validation is claimed.

## PDF

Coverage includes valid reports, required sections, original X-ray inclusion,
Grad-CAM exclusion, the displayed Clinical Support response, source metadata,
disclaimer, and error handling.

Current verification: the full backend suite passes (44 tests and 61
subtests), including Clinical Support, PDF, Grad-CAM, original-image, and XAI
endpoint coverage. A synthetic QA report was rendered locally as a 3-page PDF
and visually inspected. The PDF endpoint was exercised directly with a
database stub and temporary saved-image fixture; a full live HTTP + local
pgvector retrieval run was not available in the final verification.

## Regression

The full backend suite covers the existing functionality:

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

Phase 3E verification: `npm run build` succeeds. `npm run lint` exits
successfully with warnings in Patients, PatientDetails, AnalysisResult,
ClinicalSupport, and NewAnalysis. The AnalysisResult hook warnings come from
its existing data-loading effect pattern, which predates the original-image
display.

---

# 25. Phase 3C Research Validation Findings

Visual validation was performed across several representative X-rays and
candidate target layers `blocks[5].norm1`, `blocks[8].norm1`,
`blocks[10].norm1`, and `blocks[11].norm1`. It compared the original
preprocessed image, full attribution, content-region attribution, and
letterbox/padding attribution. Padding received inconsistent and sometimes
disproportionate attribution; a padding sensitivity experiment changed the
prediction for at least one sample. The full attribution remains visible for
research inspection rather than silently masking the padding.

This is a research validation finding, not clinical validation. The current
Grad-CAM visualization is unsuitable to present as confirmed anatomical
disease localization.

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

# 27. Phase 3 Implementation Record

```text
Phase 3A — Runtime DINOv2 verification (verified)
        ↓
Phase 3B — One-image Grad-CAM prototype (implemented)
        ↓
Phase 3C — Research visual validation (completed; padding limitation found)
        ↓
Phase 3D — Original X-ray endpoint (implemented and verified)
        ↓
Phase 3E — Original X-ray in Analysis Result (implemented)
        ↓
Phase 3F — On-demand XAI API (implemented; research-only)
        ↓
Phase 3G — Analysis Result XAI UI (implemented; experimental/research-only)
        ↓
Phase 3H — Clinical Support XAI (intentionally excluded)
        ↓
Phase 3I — PDF service (implemented on demand)
        ↓
Phase 3J — PDF download UI (implemented; posts the current response)
        ↓
Phase 3K — Regression verification (completed)
```

---

# 28. Current Phase 3 Completion Status

- Runtime DINOv2 structure, target layer, activation, token count, and reshape verified.
- Grad-CAM prototype, XAI endpoint, and Analysis Result visualization implemented; all remain experimental/research-only and not clinically validated.
- Original X-ray endpoint and display on Analysis Result and Clinical Support implemented.
- Clinical Support grounding correction/refinement implemented; T/Z estimates remain separate from the DINOv2 prediction and retain measurement safeguards.
- Clinical Support PDF generation and download implemented and verified; the original X-ray and currently displayed response are included, and Grad-CAM is excluded.
- Full backend suite: 44 tests and 61 subtests passed. Frontend build and lint passed in prior Phase 3 verification.
- Clinical Support XAI and PDF Grad-CAM are intentionally excluded, not unfinished implementation tasks.
