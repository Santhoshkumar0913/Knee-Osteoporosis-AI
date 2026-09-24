# Phase 3 Implementation — X-ray Visualization, Grad-CAM XAI, and PDF Clinical Support

> This file is an implementation tracker for the next project phase.
>
> The root `PRD.md` remains the authoritative product specification.
> This file does not replace `PRD.md`; it records the Phase 3 engineering plan and agent instructions.

---

## 1. Current Repository Status

Current development branch:

`feature/rag-llm`

Current implemented areas:

- V1 patient and analysis workflow
- DINOv2 knee X-ray classification
- T-score Random Forest estimation
- Z-score Gradient Boosting estimation
- Local X-ray storage
- Phase 2 clinical context fields
- PostgreSQL + pgvector RAG
- BGE embeddings
- OpenRouter Clinical Support
- Structured Clinical Support UI
- Responsive frontend polish

Not implemented yet:

- [ ] Safe original X-ray display from saved analysis
- [ ] Grad-CAM / XAI
- [ ] X-ray + heatmap visualization
- [ ] XAI integration into Clinical Support
- [ ] PDF Clinical Support report
- [ ] PDF download action

### Important as-built notes

- Current RAG runtime uses direct SQLAlchemy + PostgreSQL/pgvector similarity search.
- LlamaIndex dependencies are present, but LlamaIndex is not the active runtime retrieval executor.
- The existing DINOv2 checkpoint must be reused.
- Do not retrain the model for Grad-CAM.
- T-score and Z-score are model estimates, not measured DXA/QUS results.

---

## 2. Objective

Extend the application with:

1. Original knee X-ray visualization.
2. Grad-CAM explainability for the existing DINOv2 classifier.
3. Original X-ray + Grad-CAM overlay in the UI.
4. XAI information in Clinical Support.
5. On-demand PDF Clinical Support report generation.

The existing ML, RAG, and Clinical Support workflows must continue to work.

---

## 3. Required Existing Files to Inspect First

Before changing code, inspect the actual repository implementation, especially:

### Backend

`backend/app/services/image_model.py`

- DINOv2 architecture
- checkpoint loading
- preprocessing
- class mapping

`backend/app/services/storage_service.py`

- current X-ray storage
- path handling

`backend/app/api/analyses.py`

- analysis creation
- image persistence

`backend/app/api/clinical_support.py`

- Clinical Support request flow

`backend/app/services/clinical_model.py`

- T-score/Z-score models

`backend/app/rag/query_builder.py`

`backend/app/rag/retrieval.py`

`backend/app/rag/llm_service.py`

### Frontend

`frontend/src/pages/AnalysisResult/AnalysisResult.tsx`

`frontend/src/pages/ClinicalSupport/ClinicalSupport.tsx`

`frontend/src/services/api.ts`

`frontend/src/types/index.ts`

Inspect existing CSS conventions before adding new styles.

---

## 4. Implementation Order

Implement in this order and verify each phase before moving on.

### Phase 1 — Repository inspection

Report:

- exact DINOv2 model structure
- exact checkpoint loading
- target layer candidate for Grad-CAM
- required ViT token reshape
- existing image path/storage behavior
- existing API conventions
- existing frontend data types
- PDF/dependency options

Do not modify unrelated code.

### Phase 2 — Original X-ray API

Add a controlled backend endpoint following repository conventions.

Suggested:

`GET /api/analyses/{analysis_id}/image`

Requirements:

- verify analysis exists
- verify image exists
- return image safely
- do not expose arbitrary filesystem paths
- handle missing files cleanly
- support existing image types

### Phase 3 — Grad-CAM prototype

Create:

`backend/app/services/xai_service.py`

Use the exact existing DINOv2 model.

Do NOT:

- retrain
- replace DINOv2
- change classifier architecture
- create a second ML model

The current model uses:

- DINOv2 ViT-Small/14
- input size 518 × 518
- feature dimension 384
- 3 classes

Because this is a Vision Transformer, inspect the real model structure and implement the correct token-to-spatial reshape.

The expected patch grid is:

`518 / 14 = 37`

Therefore the patch map should correspond to approximately:

`37 × 37`

Do not assume a CNN-style Grad-CAM implementation is directly compatible.

### Phase 4 — Visual validation

Generate Grad-CAM for multiple existing knee X-rays.

Verify:

- heatmap is not blank
- heatmap is not uniformly activated
- overlay dimensions are correct
- overlay is spatially aligned
- selected class is correct
- no obvious token reshape distortion
- no severe artifacts

A code path that executes without errors is not sufficient.

### Phase 5 — XAI API

Use repository conventions.

Suggested:

`GET /api/analyses/{analysis_id}/xai`

Possible response:

```json
{
  "analysis_id": 1,
  "predicted_class": "Osteoporosis",
  "confidence": 0.818,
  "original_image_url": "...",
  "heatmap_url": "...",
  "overlay_url": "...",
  "explanation_note": "Grad-CAM visualization showing image regions that contributed to the model's selected prediction."
}
```

Avoid duplicate APIs if an existing clean design can be extended.

### Phase 6 — Analysis Result UI

Update:

`frontend/src/pages/AnalysisResult/`

Display:

- Original X-ray
- Predicted class
- Confidence
- Class probabilities
- Model-estimated T-score + range
- Model-estimated Z-score + range
- Clinical context
- Grad-CAM visualization

Suggested wording:

**Model Explainability**

“Grad-CAM visualization showing image regions that contributed to the model's selected prediction.”

### Phase 7 — Clinical Support UI

Update:

`frontend/src/pages/ClinicalSupport/`

Display:

- Original X-ray
- Grad-CAM overlay
- model prediction
- clinical context
- existing structured Clinical Support
- sources
- grounding note
- disclaimer

Do not make XAI appear to be clinical evidence.

### Phase 8 — Clinical Support grounding safety

Preserve these rules:

1. T-score and Z-score must remain labeled as model estimates.
2. Never describe them as DXA, QUS, bone-density-test, or laboratory measurements.
3. The LLM must not use T-score/Z-score estimates to independently override the DINOv2 classification.
4. Grad-CAM must not be described as proof of disease.
5. Grad-CAM must not be treated as a confirmed anatomical pathology location.
6. Clinical Support remains informational/decision-support content, not autonomous diagnosis or treatment.

### Phase 9 — PDF generation

Create:

`backend/app/services/pdf_service.py`

Generate on demand.

Preferred behavior:

`request → generate PDF → stream response`

Do not persist generated reports unless existing architecture requires it.

Suggested endpoint:

`GET /api/analyses/{analysis_id}/clinical-support/pdf`

### Phase 10 — PDF contents

Include:

1. Project title
2. Patient information
3. Clinical context
4. Original X-ray
5. Model prediction
6. All class probabilities
7. Model-estimated T-score + empirical range
8. Model-estimated Z-score + empirical range
9. Grad-CAM overlay
10. XAI explanation note
11. Clinical Support explanation
12. What You Can Do Now
13. Talk to Your Doctor About
14. Testing and Follow-up
15. Treatment Information
16. Evidence sources
17. Grounding note
18. Existing medical disclaimer

Use the project's existing disclaimer exactly:

> AI-assisted guidance for informational purposes. This does not replace a doctor's diagnosis or treatment decision. Discuss medical decisions with your doctor.

### Phase 11 — PDF UI action

Add:

**Download PDF Report**

Handle:

- loading
- download success
- generation failure
- missing analysis
- missing X-ray
- missing Clinical Support

PDF failure must not break the Clinical Support page.

---

## 5. XAI Safety Wording

Do NOT use:

- “The heatmap proves osteoporosis.”
- “The highlighted area is definitely diseased.”
- “The heatmap confirms the diagnosis.”
- “The AI found the disease.”

Use:

- “Grad-CAM visualization showing image regions that contributed to the model's selected prediction.”
- “Model explainability visualization.”

Grad-CAM is an explanation aid only.

---

## 6. Storage

Current X-rays are stored locally under the existing storage system.

Do not duplicate or redesign image storage unnecessarily.

Generated XAI artifacts may be stored under a controlled generated-artifact directory, for example:

`storage/xai/<patient_code>/<analysis_id>/`

Possible artifacts:

- heatmap
- overlay

Do not modify the original X-ray file.

---

## 7. Performance

Keep normal prediction behavior unchanged.

Preferred behavior:

Normal analysis:
`prediction only`

XAI request:
`prediction context + Grad-CAM`

Clinical Support:
`reuse saved prediction`

PDF:
`reuse saved prediction + XAI + Clinical Support`

Reuse the existing model instance where the current architecture permits it.

Avoid loading the model independently on every request.

---

## 8. Testing

Add/extend tests for:

### Image API

- valid analysis
- missing analysis
- missing image
- supported image types

### XAI

- valid analysis
- selected class mapping
- heatmap generation
- output dimensions
- overlay generation
- missing image handling
- model/XAI error handling

### PDF

- valid generation
- required content
- missing Clinical Support
- missing X-ray
- invalid analysis
- HTTP response/download behavior

### Regression

Existing features must still pass:

- patient creation
- analysis creation
- DINOv2 prediction
- T-score
- Z-score
- history
- deletion
- RAG ingestion
- pgvector retrieval
- Clinical Support
- OpenRouter response parsing

Frontend:

```bash
npm run build
npm run lint
```

Document existing lint warnings if they remain.

---

## 9. Security

Never expose or send:

- database credentials
- API keys
- .env contents
- raw filesystem paths
- private model paths
- internal database IDs when not required
- patient names to OpenRouter
- patient IDs to OpenRouter
- X-ray images to OpenRouter

The X-ray must remain outside the external LLM request.

---

## 10. Agent Rules

Before coding:

1. Inspect the actual repository.
2. Identify the smallest set of required files.
3. Explain the implementation plan.
4. Start with the smallest safe phase.

During coding:

- do not rewrite unrelated files
- do not replace working ML models
- do not retrain
- do not change the existing RAG architecture unless necessary
- do not create duplicate functionality
- preserve current API conventions
- preserve current UI styling conventions

After every logical feature:

1. run tests
2. report changed files
3. report verification result
4. stop if something fails
5. continue only when the phase is verified

---

## 11. Git Workflow

Branch:

`feature/rag-llm`

Do not modify `main` directly.

After each completed logical feature:

```bash
git status
git add <specific files>
git commit -m "<simple one-line message>"
git push origin feature/rag-llm
```

Preferred commit messages:

- `add xray image endpoint`
- `add grad cam visualization`
- `add xai analysis endpoint`
- `update analysis result xai`
- `add clinical support visualization`
- `add clinical support pdf`

No emojis, prefixes, Co-authored-by lines, or unrelated changes.

---

## 12. Definition of Done

- [ ] Original X-ray endpoint works
- [ ] Original X-ray shown in Analysis Result
- [ ] Original X-ray shown in Clinical Support
- [ ] Grad-CAM works with existing DINOv2 checkpoint
- [ ] No retraining required
- [ ] Grad-CAM visually validated on multiple X-rays
- [ ] Heatmap aligns with original image
- [ ] Correct target class used
- [ ] XAI wording is medically cautious
- [ ] T/Z remain model estimates
- [ ] Clinical Support grounding remains intact
- [ ] PDF generated successfully
- [ ] PDF includes original X-ray
- [ ] PDF includes Grad-CAM
- [ ] PDF includes prediction/probabilities
- [ ] PDF includes T/Z estimates and ranges
- [ ] PDF includes clinical context
- [ ] PDF includes Clinical Support
- [ ] PDF includes sources
- [ ] PDF includes grounding note
- [ ] PDF includes disclaimer
- [ ] Existing tests pass
- [ ] New tests pass
- [ ] Frontend build passes
- [ ] Frontend lint passes or warnings are documented
- [ ] Git working tree is clean
- [ ] Changes pushed to `feature/rag-llm`

---

## 13. First Agent Command

Start with Phase 1 only.

Use this instruction:

> Inspect the current `feature/rag-llm` repository and report the exact files, classes, and functions involved in:
>
> 1. DINOv2 model construction
> 2. checkpoint loading
> 3. image preprocessing
> 4. image storage
> 5. Analysis Result
> 6. Clinical Support
> 7. API routing
> 8. frontend API/types
> 9. PDF/dependency structure
>
> Then identify the most appropriate Grad-CAM target layer and required ViT token reshape for the exact current DINOv2 model.
>
> Do not modify code yet.
