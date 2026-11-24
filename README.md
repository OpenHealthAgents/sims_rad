# SIMS Radiology AI Operating Agentic Platform

The SIMS Radiology AI Operating Agentic Platform is an enterprise-grade medical imaging AI platform designed following strict **Clean Architecture** principles. It integrates autonomous sub-agent orchestration (Deep Agents & LangGraph), clinical safety verification (NVIDIA NeMo Guardrails), pipeline orchestration (Kestra), explainability (SHAP), and healthcare domain standards (PyDICOM & FHIR Core).

---

## 🏛️ Architecture Overview

The codebase is organized as a monorepo adhering strictly to Uncle Bob's Clean Architecture dependency rule: dependencies only point inwards.

```
sims-radiology-platform/
├── apps/
│   ├── api/                     # FastAPI presentation layer (Ref: full-stack-fastapi-template)
│   │   ├── Dockerfile           # Production container build
│   │   └── src/
│   │       ├── endpoints/       # Health, Studies, Triage API routes
│   │       └── main.py          # Application entrypoint & middleware
│   └── web/                     # JavaScript / Lit frontend with A2UI web components (Ref: a2ui)
│       ├── package.json         # References local @a2ui/lit & @a2ui/web_core contracts
│       └── src/components/      # Lit-based Radiology Study Viewer & Findings surface
├── core/
│   ├── domain/                  # Enterprise business rules & entities (Zero framework dependencies)
│   │   ├── entities/            # RadiologyStudy, ImagingSeries, RadiologyReport, Finding
│   │   ├── values/              # StudyUID, AccessionNumber, PatientIdentifier, Modality, TriagePriority
│   │   └── exceptions/          # DomainException, InvalidDICOMMetadataError, GuardrailViolationError
│   ├── application/             # Use cases, interfaces (ports), DTOs, sub-agent tools
│   │   ├── dto/                 # Pydantic v2 data transfer contracts
│   │   ├── interfaces/          # StudyRepositoryInterface, GuardrailServiceInterface, AgentOrchestratorInterface
│   │   ├── tools/               # DicomHeaderExtractionTool, ShapAttributionTool, FhirDiagnosticReportTool
│   │   └── use_cases/           # IngestStudyUseCase, RunAiDiagnosticTriageUseCase
│   └── infrastructure/          # Outward adapters, DB models, config, telemetry
│       ├── config.py            # Pydantic Settings v2 environment validation schema
│       ├── db/                  # SQLAlchemy 2.0 models, asyncpg session, repository implementation
│       ├── celery/              # Celery task worker configuration for DICOM background tasks
│       ├── kestra/              # Kestra standalone pipeline API client
│       └── langfuse/            # Langfuse observability and LLM tracing client
├── agents/                      # Deep Agents harnesses & NeMo Guardrail rails
│   ├── deepagents/              # DeepAgentsDiagnosticHarness coordinating sub-agents & LangGraph transitions
│   └── guardrails/              # NVIDIA NeMo Guardrails configuration and clinical safety service
├── kestra/                      # Kestra flow definitions (YAML)
│   └── flows/                   # dicom_ingestion_and_triage.yml
├── tests/                       # Unit, integration, contract, and safety tests
│   ├── unit/                    # Domain entity and config validation tests
│   ├── integration/             # Live API endpoint tests
│   ├── contract/                # A2UI package and web component contract tests
│   └── safety/                  # NeMo Guardrails clinical safety tests
└── docker/                      # On-prem docker-compose stack definitions
    └── docker-compose.yml       # PostgreSQL 16, Redis 7, Kestra, Langfuse, and API scaffold
```

---

## ⚙️ Tech Stack & References

| Layer / Capability | Component | Reference / Source |
|---|---|---|
| **Presentation API** | FastAPI, Uvicorn, Pydantic v2 | `reference_repos/full-stack-fastapi-template` |
| **Frontend UI** | Lit Web Components, A2UI | `reference_repos/a2ui` |
| **Agentic Framework** | Deep Agents & LangGraph | `reference_repos/deepagents` & `reference_repos/langgraph` |
| **Safety & Policy Rails** | NVIDIA NeMo Guardrails | `reference_repos/NeMo-Guardrails` |
| **Workflow Orchestration** | Kestra Standalone | `reference_repos/kestra` |
| **Observability & Tracing** | Langfuse SDK & Server | `reference_repos/langfuse` |
| **Medical Domain Standards** | PyDICOM & FHIR-Core R4 | `reference_repos/pydicom` & `reference_repos/fhir-core` |
| **Explainability (XAI)** | SHAP Feature Attribution | `reference_repos/shap` |
| **Database & Task Broker** | PostgreSQL 16, Redis 7, Celery | `reference_repos/celery` |

---

## 🚀 Quickstart & Verification

### 1. Run Docker Compose Stack
```bash
docker compose up -d
```

### 2. Verify Health Check Endpoint
```bash
curl http://localhost:8000/health
```
Response (`200 OK`):
```json
{
  "status": "healthy",
  "project_name": "SIMS Radiology AI Operating Agentic Platform",
  "environment": "development",
  "api_version": "v1",
  "config_loaded": true,
  "subsystems": {
    "postgres": { "server": "postgres", "database": "sims_radiology", "status": "configured" },
    "redis_celery": { "host": "redis", "port": 6379, "status": "configured" },
    "langfuse": { "host": "http://langfuse:3000", "enabled": true, "status": "configured" },
    "kestra": { "host": "http://kestra:8080", "namespace": "sims.radiology", "status": "configured" },
    "guardrails": { "framework": "NVIDIA NeMo Guardrails", "status": "initialized" },
    "agentic_framework": { "framework": "Deep Agents & LangGraph", "status": "initialized" }
  }
}
```

### 3. Run the Automated Test Suite
```bash
pytest tests -v
```
All 14 unit, integration, safety, and contract tests pass out-of-the-box.
