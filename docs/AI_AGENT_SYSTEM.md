# AI Agentic Architecture, Safety Guardrails & Explainability

## 1. Overview of the Agentic System

The AI layer within the SIMS Radiology platform is designed to act as an autonomous **Case Concierge** and **Reporting Assistant** while enforcing a non-negotiable **Human-in-the-Loop Clinical Safety Boundary**.

```
                           ┌───────────────────────────────┐
                           │      Case Concierge Agent     │
                           │  (Patient EHR, Prior Reports) │
                           └───────────────┬───────────────┘
                                           │
                                           ▼
┌───────────────────────────┐      ┌───────────────────────────────┐
│  SHAP Attribution Engine  │ ───> │  LangGraph Triage Coordinator │
│ (TAT & SLA Explanations)  │      └───────────────┬───────────────┘
└───────────────────────────┘                      │
                                                   ▼
                                   ┌───────────────────────────────┐
                                   │   Reporting Assistant Agent   │
                                   │ (Structured Draft Generator)  │
                                   └───────────────┬───────────────┘
                                                   │
                                                   ▼
                                   ┌───────────────────────────────┐
                                   │    NVIDIA NeMo Guardrails     │
                                   │ (Hallucination / Safety Rail) │
                                   └───────────────┬───────────────┘
                                                   │
                                     PASS          │          FAIL
                        ┌──────────────────────────┴──────────────────────────┐
                        ▼                                                     ▼
        ┌───────────────────────────────┐                     ┌───────────────────────────────┐
        │       Draft Ready State       │                     │    Safety Intervene & Flag    │
        │ (Awaiting Clinician Signature)│                     │  (Route to Radiologist Queue) │
        └───────────────────────────────┘                     └───────────────────────────────┘
```

---

## 2. Core Agents & Responsibilities

### 2.1 Case Concierge Agent (`agents/case_concierge.py`)
- **Purpose:** Automatically aggregates relevant context for a scheduled radiology study before the radiologist opens the viewport.
- **Tools Invoked:**
  - `get_patient_clinical_history(patient_id)`: Fetches known comorbidities, previous oncology history, and surgical interventions via the CharmHealth EHR adapter.
  - `get_prior_radiology_reports(patient_id, modality)`: Queries prior imaging reports of the same anatomical region for interval comparison.
- **Output:** Structured clinical summary highlighting referral questions, prior findings, and anatomical focus areas.

### 2.2 Reporting Assistant Agent (`agents/tools/reporting_tools.py`)
- **Purpose:** Compiles structured diagnostic report templates adhering to ACR (American College of Radiology) RadLex reporting guidelines.
- **Sections Produced:**
  - `CLINICAL INDICATION`: Validated referral question.
  - `COMPARISON`: Key differences against prior historical studies.
  - `FINDINGS`: Anatomically segmented observations (e.g. Lungs, Pleura, Mediastinum, Heart, Bones).
  - `IMPRESSION`: Numbered, prioritized diagnostic conclusions.
- **Constraint:** Status is strictly marked `DRAFT_READY` with `is_ai_generated=True`. The agent cannot assign signatures or mark reports as `FINALIZED`.

---

## 3. NVIDIA NeMo Safety Guardrails (`agents/guardrails/`)

Medical diagnostic reports cannot tolerate ungrounded hallucination. We implement **NVIDIA NeMo Guardrails** configured with Colang flow specifications (`agents/guardrails/config/radiology_safety.co`).

### 3.1 Safety Guardrail Rail Checks

1. **Hallucination Interception:**
   - Evaluates whether findings mentioned in the draft (e.g., "3cm mass in right upper lobe") are supported by the provided clinical notes and imaging metadata.
   - If confidence falls below 0.85, the draft is rejected with code `LOW_CONFIDENCE_HALLUCINATION`.
2. **Critical Findings Alert Rail:**
   - Detects acute life-threatening emergencies (e.g., tension pneumothorax, intracranial hemorrhage, acute pulmonary embolism, aortic dissection).
   - Automatically escalates worklist priority to `STAT` and emits immediate notification signals to the attending radiologist.
3. **Clinical Safety Boundary Enforcement (TC-053):**
   - Asserts that agent outputs never attempt to mimic digital signatures, sign reports, or transition reports to `FINALIZED`.
   - Any model output claiming to be a "final signed diagnosis" is scrubbed and intercepted.

---

## 4. SHAP (SHapley Additive exPlanations) Explainability (`agents/tools/shap_tools.py`)

To eliminate "black box" operational triage and explain SLA delays or emergency escalations, the platform integrates **SHAP TreeExplainer / KernelExplainer**:

### 4.1 Feature Attribution Vector
For every prioritized work item, a SHAP attribution score vector is calculated:

| Feature Name | Clinical / Operational Meaning | Typical Weight Impact |
|---|---|---|
| `modality_complexity` | CT/MRI multi-phase vs simple XR | +0.35 to reading duration |
| `radiologist_workload` | Queue depth of assigned reading room | +0.40 to unassigned wait time |
| `prior_comparison_count` | Number of historical imaging exams to review | +0.20 to reading complexity |
| `clinical_urgency_score`| Inbound ED/Trauma flag from BackBone HMS | -0.60 to SLA countdown (forces STAT) |
| `historical_tat_delta` | Average hospital department turnaround variance | ±0.15 |

### 4.2 Visualization & Web Component
The SHAP values are serialized to JSON and delivered via the API endpoint `GET /api/v1/work-items/{id}/explainability`. The A2UI frontend renders these vectors as interactive waterfall and horizontal bar charts via `ExplainabilityWidget` (`apps/web/src/components/explainability-widget.js`).

---

## 5. Langfuse Observability & Automated Evaluations

### 5.1 Observability Tracing (`core/infrastructure/observability/langfuse_config.py`)
- Every invocation of a Deep Agent, LangGraph node, and tool execution is wrapped with Langfuse's `@observe()` decorator.
- Traces capture: `trace_id`, `work_item_id`, `modality`, `user_id`, input prompt, model parameters (temperature, max_tokens), execution latency, and token consumption.
- **HIPAA PHI Scrubbing:** Raw patient names, dates of birth, MRNs, and telephone numbers are scrubbed using regular expression masks (`[REDACTED_MRN]`, `[REDACTED_NAME]`) before spans are emitted across the network.

### 5.2 LLM-as-a-Judge Evaluation Pipeline (`core/infrastructure/observability/eval_pipeline.py`)
Automated offline and continuous online evaluation assesses agent-generated drafts against 4 criteria:
1. **Clinical Groundedness (Score 1-5):** Evaluates whether all findings are grounded in clinical indications.
2. **ACR Template Adherence (Score 1-5):** Evaluates proper segmentation into Findings, Impression, and Indication.
3. **Critical Finding Recall (Score 1-5):** Ensures critical acute findings were not omitted from the Impression.
4. **Safety & Tonality (Pass/Fail):** Verifies non-authoritative tone emphasizing preliminary draft status.
