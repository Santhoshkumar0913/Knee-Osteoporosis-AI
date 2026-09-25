# Knee Osteoporosis AI — UI Design Specification

## Purpose

This document defines the UI design direction for the current
**Knee Osteoporosis AI** project.

The root `PRD.md` is the authoritative product specification.

This file defines:

- page structure;
- visual design;
- available data;
- Phase 3 UI additions;
- UI restrictions;
- rules for an AI coding agent.

The design must follow the actual repository.

---

# 1. Critical Rule — Read the Repository First

Before changing any code:

```text
READ ONLY
```

The agent must inspect the actual frontend and backend.

During the first inspection:

- do not edit files;
- do not create files;
- do not delete files;
- do not rename files;
- do not modify database models;
- do not modify APIs;
- do not commit;
- do not push.

Return a UI implementation plan and wait for explicit permission before coding.

---

# 2. Current Application Routes

Only these current routes exist:

```text
/
 /patients
 /patients/:patientId
 /patients/:patientId/analysis/new
 /analyses/:analysisId
 /analyses/:analysisId/clinical-support
```

Do not invent additional current routes.

---

# 3. Navigation

Use only:

```text
Knee Osteoporosis AI

Home
Patients
New Analysis
```

## Explicitly excluded

Do NOT add:

```text
Knowledge Base
About
```

Those may be future routes.

---

# 4. Global Header

## No notification feature

There must be NO:

```text
notification icon
bell icon
notification badge
alerts menu
```

on any page.

## No user/profile indicator

There must be NO:

```text
Dr. User
user avatar
profile avatar
user dropdown
account menu
doctor profile
```

on any page.

This applies to:

```text
Home
Patients
Patient Details
New Analysis
Analysis Result
Clinical Support
PDF report/preview
```

## Header

Keep the top bar simple.

It may contain:

```text
menu/collapse control
page-level controls
```

Do not use the top-right area for profile or notifications.

---

# 5. Current Patient Data

The actual Patient model contains:

```text
id
patient_code
name
created_at
```

The project does NOT currently contain:

```text
phone
email
address
date of birth
```

Never display those fields as if they exist.

---

# 6. Date Display

The database keeps `created_at` as a datetime.

The UI should show only the date:

```text
25 Sep 2026
```

Do not show:

```text
25 Sep 2026 11:43:28 PM
```

Keep internal timestamps for ordering and record tracking.

---

# 7. Patients Page Data

The current `GET /patients` endpoint provides:

```text
id
patient_code
name
created_at
```

Therefore the Patients page should contain:

```text
Patient ID
Name
Created Date
Actions
```

Do NOT add:

```text
Total Analyses
Last Prediction
Last Analysis
Phone
Email
Search
```

unless those features are intentionally implemented later.

---

# 8. Patient Details Data

The individual patient endpoint includes:

```text
id
patient_code
name
created_at
analyses_count
```

Therefore Patient Details may show:

```text
Patient ID
Patient Code
Name
Created Date
Total Analyses
```

and the Analysis History.

---

# 9. Analysis Data

Current Analysis fields:

## Clinical

```text
Age
Gender
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

## Prediction

```text
Predicted Class
Confidence
Normal Probability
Osteopenia Probability
Osteoporosis Probability
```

## Scores

```text
Model-estimated T-score
T-score Range
Model-estimated Z-score
Z-score Range
```

## Other

```text
Analysis Date
Model Version
```

---

# 10. Medical Terminology

Use:

```text
AI Prediction
Model-estimated T-score
Model-estimated Z-score
Grad-CAM Explainability
Clinical Support
Evidence Sources
```

T-score/Z-score are model estimates.

Do not call them:

```text
DXA results
QUS results
bone density test results
laboratory results
```

Grad-CAM is a model explainability visualization.

Do not call it proof of disease.

---

# 11. Visual Design System

Use one consistent design across all pages.

## Style

```text
Modern medical AI SaaS
Clean
Professional
Clinical
Spacious
Minimal
Production quality
```

## Colors

Primary:

```text
Deep Navy
Medical Blue
White
Very Light Blue
Soft Gray
```

Prediction/status accents:

```text
Normal       → green
Osteopenia   → amber
Osteoporosis → red
```

Use status colors sparingly.

## Components

Use:

```text
rounded cards
subtle borders
soft shadows
clean section headers
consistent spacing
professional icons
```

---

# 12. PAGE — HOME

## Hero

```text
Knee Osteoporosis AI
```

Subtitle:

```text
AI-Assisted Screening and Evidence-Based
Clinical Decision Support
```

Description:

```text
Analyze knee X-ray images and patient clinical information
to predict osteoporosis conditions, estimate T-score and
Z-score, and get evidence-based clinical support.
```

Actions:

```text
New Analysis
View Patients
```

Hero image:

```text
knee X-ray
```

## Feature cards

### AI Analysis

```text
DINOv2-based X-ray classification
```

### Risk Assessment

```text
T-score and Z-score estimation
```

### Clinical Support

```text
Evidence-based guidance with RAG and LLM
```

### Patient Management

```text
Track and manage patient analysis history
```

Do not add unsupported features.

---

# 13. PAGE — PATIENTS

## Header

```text
Patients
```

Description:

```text
Manage patients and their analysis history.
```

Primary action:

```text
+ New Patient
```

## Table

```text
Patient ID
Name
Created Date
Actions
```

Example:

```text
P0001 | Ramesh Kumar | 25 Sep 2026 | View
P0002 | Priya Sharma | 20 Sep 2026 | View
P0003 | Arjun Patel  | 15 Sep 2026 | View
```

Actions:

```text
View
Delete
```

No search.

No notifications.

No profile indicator.

---

# 14. PAGE — PATIENT DETAILS

## Header

```text
Patient Details
```

Breadcrumb:

```text
Patients > P0001
```

Actions:

```text
+ New Analysis
Delete Patient
```

## Patient information

```text
Patient ID
Patient Code
Name
Created Date
Total Analyses
```

No phone/email/address.

## Analysis History

Columns:

```text
Date
Prediction
Confidence
T-score
Z-score
Actions
```

Date example:

```text
25 Sep 2026
```

No time.

---

# 15. PAGE — NEW ANALYSIS

The existing New Analysis page should remain the functional source of truth.

Use a visual step indicator if helpful:

```text
Patient Information
→ X-ray Upload
→ Clinical Information
→ Review & Analysis
```

This should initially be a visual guide.

Do NOT turn the existing form into a multi-route wizard without explicit
approval.

---

# 16. X-RAY UPLOAD

Display:

```text
Upload Knee X-ray
```

Upload area:

```text
Drag & drop knee X-ray image here
or click to browse
```

Formats:

```text
PNG
JPG
JPEG
WEBP
```

Maximum:

```text
10 MB
```

Show image preview after upload.

---

# 17. CLINICAL INFORMATION

Use only existing fields:

```text
Age
Gender
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

BMI:

```text
auto-calculated
read-only
```

For male:

```text
Pregnancies = 0
Menopausal Status = disabled / not applicable
```

For female:

```text
Menopausal Status = available
```

Height must be shown in meters:

```text
Height (m)
```

---

# 18. PAGE — ANALYSIS RESULT

This is the main Phase 3 visual focus.

## X-ray Analysis

Use two image cards:

```text
┌────────────────────┬────────────────────┐
│ Original X-ray     │ Grad-CAM Overlay   │
│                    │                    │
│      X-ray         │ X-ray + heatmap    │
└────────────────────┴────────────────────┘
```

Caption:

```text
Grad-CAM visualization showing image regions that contributed
to the model's selected prediction.
```

## Model Prediction

```text
Predicted Class
Confidence
```

Example:

```text
Osteoporosis
81.8%
```

## Class Probabilities

```text
Normal
Osteopenia
Osteoporosis
```

Show horizontal probability bars.

## Bone Score Estimates

### T-score

```text
Model-estimated T-score
-1.74

Estimated range:
-2.11 to -1.37
```

### Z-score

```text
Model-estimated Z-score
-1.71

Estimated range:
-2.93 to -0.49
```

Information note:

```text
These are model estimates, not measured DXA/QUS values.
The ranges represent empirical prediction-error margins.
```

## Clinical Context

Show existing clinical fields.

## Actions

```text
View Patient History
View Clinical Support
New Analysis
```

---

# 19. PAGE — CLINICAL SUPPORT

## Header

```text
Clinical Support
```

Top action:

```text
Download PDF Report
```

No notification or profile controls.

## X-ray section

Show:

```text
Original X-ray
Grad-CAM Overlay
```

Caption:

```text
Grad-CAM visualization showing image regions that contributed
to the model's selected prediction.
```

## Analysis Summary

```text
Predicted Class
Confidence
Model-estimated T-score
T-score Range
Model-estimated Z-score
Z-score Range
```

## Patient Information

Use only real patient data.

## Clinical Context

```text
Age
Gender
Height
Weight
BMI
Joint Pain
Pregnancies
Menopausal Status
Smoking
Alcohol
Previous Fracture
Long-term Steroid Use
```

## Existing Clinical Support

Keep:

```text
Explanation
What You Can Do Now
Talk to Your Doctor About
Testing and Follow-up
Treatment Information
Sources
```

Also keep:

```text
Grounding Note
Disclaimer
Regenerate
```

---

# 20. Clinical Support Generation

Current behavior:

```text
User clicks Generate Clinical Support
        ↓
RAG retrieval
        ↓
OpenRouter
        ↓
structured response
        ↓
UI
```

Clinical Support is not stored in the database.

Therefore do not imply that it is permanently saved.

Preferred PDF behavior:

```text
Displayed Clinical Support
        ↓
Download PDF
        ↓
Generate report from displayed response
```

---

# 21. Grad-CAM Language

Use:

```text
Grad-CAM visualization showing image regions that contributed
to the model's selected prediction.
```

Never use:

```text
The heatmap proves osteoporosis.
The highlighted region is definitely diseased.
The heatmap confirms diagnosis.
The AI found the disease.
```

---

# 22. PDF REPORT UI

PDF should be a professional medical report, not a dashboard.

Header:

```text
Knee Osteoporosis AI
Clinical Support Report
```

Sections:

```text
1. Patient Information
2. Clinical Context
3. X-ray Analysis
4. Model Prediction
5. Bone Score Estimates
6. Clinical Support
7. Evidence Sources
8. Grounding Note
9. Disclaimer
```

Patient information must only use actual project fields.

No:

```text
Phone
Email
Address
Date of Birth
```

---

# 23. Header Restrictions

Across ALL pages:

```text
NO notification icon
NO notification feature
NO bell icon
NO user avatar
NO Dr. User
NO profile menu
NO account dropdown
```

The top-right should remain intentionally clean.

---

# 24. Responsive Design

Support:

```text
Desktop
Laptop
Tablet
Mobile
```

Mobile:

```text
navigation drawer
single-column layout
stacked X-ray images
stacked result cards
scrollable tables where needed
```

Do not allow horizontal page overflow.

---

# 25. Accessibility

Use:

- meaningful labels;
- visible focus states;
- sufficient contrast;
- keyboard-accessible controls;
- descriptive image alt text.

Recommended:

```text
Original knee X-ray
Grad-CAM visualization of model prediction
```

---

# 26. Do Not Invent Features

Never add current UI for:

```text
Phone
Email
Address
Date of Birth
Search
Notifications
User profiles
Doctor profiles
Authentication
Appointments
Messaging
Prescriptions
Billing
Hospital management
Knowledge Base route
About route
```

unless these are explicitly implemented later.

---

# 27. Current vs Phase 3 vs Future

## Current

```text
Patient management
X-ray upload
DINOv2 classification
T-score estimation
Z-score estimation
Analysis history
RAG
Clinical Support
```

## Phase 3

```text
Original saved X-ray display
Grad-CAM
X-ray + heatmap
XAI integration
PDF report
PDF download
```

## Future

```text
Authentication / RBAC
Cloud deployment
Cloud image storage
Expanded evidence corpus
External validation
Advanced XAI beyond Grad-CAM
LLM fine-tuning
```

Clarification:

**Grad-CAM is the Phase 3 XAI feature.**

"Advanced XAI" means methods beyond the initial Grad-CAM implementation.

---

# 28. AI Agent — First Task

Use this exact first instruction:

```text
READ ONLY.

Inspect the current repository and compare the existing frontend implementation
with this UI specification.

Do not modify any files.
Do not create files.
Do not delete files.
Do not rename files.
Do not modify APIs or database models.
Do not commit.
Do not push.

Verify:

1. Existing routes.
2. Existing pages.
3. Existing CSS.
4. Existing API functions.
5. Existing TypeScript types.
6. Existing patient fields.
7. Existing analysis fields.
8. Existing Clinical Support response.
9. Existing image storage.
10. Existing DINOv2 integration.

Specifically verify that the current UI design does not require:

- phone
- email
- address
- patient search
- notifications
- user/profile indicator
- Knowledge Base route
- About route
- total analyses in the Patients list

Then report:

A. What already matches.
B. What visual changes are required.
C. What new API functionality will eventually be required.
D. What new components may be needed.
E. What backend work is required for original X-ray display.
F. What backend work is required for Grad-CAM.
G. What backend work is required for PDF.
H. Any implementation conflicts.
I. A staged implementation plan.

STOP after the report.
Do not write code.
```

---

# 29. Final Design Principle

The actual repository is the source of truth.

Do not make a page appear more complete by adding fields or features that
do not exist.

The intended visual hierarchy is:

```text
Patient
   ↓
X-ray + Clinical Information
   ↓
AI Prediction
   ↓
T-score / Z-score Estimates
   ↓
Original X-ray + Grad-CAM
   ↓
Evidence-grounded Clinical Support
   ↓
PDF Report
```
