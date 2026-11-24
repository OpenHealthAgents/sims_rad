# SIMS Radiology AI Operating Agentic Platform

[![CI Full Test Suite](https://img.shields.io/badge/pytest-174%20passed-brightgreen.svg)](https://github.com/OpenHealthAgents/sims_rad)
[![Coverage](https://img.shields.io/badge/coverage-87%25-green.svg)](https://github.com/OpenHealthAgents/sims_rad)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture%20%2F%20DDD-orange.svg)](docs/ARCHITECTURE.md)
[![Compliance](https://img.shields.io/badge/Compliance-HIPAA%20%7C%20FDA%2021%20CFR%20Part%2011-purple.svg)](docs/SECURITY_AND_COMPLIANCE.md)

An enterprise-grade, on-premises radiology AI operating platform built with **Clean Architecture**, **Domain-Driven Design (DDD)**, and **Hexagonal (Ports and Adapters) Architecture**. 

The platform orchestrates autonomous multi-agent clinical context compilation, structured draft reporting with strict **NVIDIA NeMo Guardrails**, deterministic order and accession reconciliation, **SHAP** feature explainability for turnaround times, and transactional outbox event delivery to hospital electronic health record systems.

---

## 📚 Table of Contents

- [Architectural Highlights](#-architectural-highlights)
- [Monorepo Directory Layout](#-monorepo-directory-layout)
- [Comprehensive Documentation Suite](#-comprehensive-documentation-suite)
- [Clinical & Operational Capabilities](#-clinical--operational-capabilities)
- [Technology Stack](#-technology-stack)
- [Quickstart: Local Development](#-quickstart-local-development)
- [Production On-Premises Packaging (Docker Compose)](#-production-on-premises-packaging-docker-compose)
- [Database Backup & Disaster Recovery (RPO ≤ 15m / RTO ≤ 4h)](#-database-backup--disaster-recovery)
- [Automated Verification & Test Plan](#-automated-verification--test-plan)
- [Security, Cryptographic Signatures & Governance](#-security-cryptographic-signatures--governance)
- [API Reference Matrix](#-api-reference-matrix)
- [Contributing & License](#-contributing--license)

---

## 🏛️ Architectural Highlights

1. **Strict Clean Architecture & Dependency Inversion:**
   - Domain layer (`core/domain/`) contains **zero framework dependencies**.
   - Application use cases (`core/application/`) operate strictly against port interfaces.
   - Persistence, adapters, and frameworks are outer plugins in `core/infrastructure/`.
2. **Clinical Safety Boundary & Human-in-the-Loop:**
   - AI sub-agents compile structured findings and impressions into `DRAFT_READY` state.
   - Autonomous sign-off is strictly prohibited. Finalizing a report requires credentialed radiologist sign-off (`REPORTING_RADIOLOGIST` or `RADIOLOGY_DIRECTOR`).
3. **Medical-Legal Append-Only Immutability (TC-033):**
   - Finalized report versions (`report_versions`) are strictly append-only.
   - Dual enforcement via SQLAlchemy ORM listeners and PostgreSQL database triggers prevents `UPDATE` or `DELETE` on finalized versions.
4. **Transactional Outbox Pattern & SKIP LOCKED Polling:**
   - Eliminates dual-write inconsistencies between PostgreSQL and Celery/Kestra.
   - Celery workers poll unprocessed outbox events via `SELECT ... FOR UPDATE SKIP LOCKED` for lock-free horizontal scalability.
5. **A2UI Protocol Engine (Agent-to-UI):**
   - Real-time Server-Sent Events (SSE) stream dynamic Lit 3 Web Components directly from AI agents into the radiologist's browser workbench.

---

## 📁 Monorepo Directory Layout

```
sims_rad/
├── agents/                      # AI Agentic Layer (Deep Agents, LangGraph, NeMo, SHAP)
│   ├── case_concierge.py        # Case Concierge sub-agent (EHR history & prior report synthesizer)
│   ├── radiology_orchestrator.py# LangGraph multi-agent diagnostic orchestration state graph
│   ├── guardrails/              # NVIDIA NeMo Guardrails configuration & clinical safety service
│   ├── tools/                   # Clinical history, reporting, and SHAP attribution tools
│   └── evals/                   # Automated LLM-as-a-judge evaluation rubric pipeline
├── apps/
│   ├── api/                     # FastAPI backend REST API & SSE streaming
│   │   ├── Dockerfile           # Multi-stage Python 3.12 production container
│   │   ├── middleware/          # Server-side RBAC, correlation ID, and security middleware
│   │   ├── routes/              # Clean Architecture v1 endpoints (work-items, reports, metrics)
│   │   └── src/                 # Main FastAPI application entrypoint & health probes
│   └── web/                     # Lit 3 + Google A2UI frontend application
│       ├── Dockerfile           # Multi-stage Node builder + Nginx Alpine production image
│       ├── nginx.conf           # Reverse proxy configuration with SSE streaming tuning
│       └── src/components/      # WorklistTable, CaseConciergePanel, ReportEditor, Explainability
├── core/
│   ├── domain/                  # Pure Enterprise Business Rules & Entities (Zero Frameworks)
│   │   ├── entities/            # Patient, RadiologyStudy, WorkItem, Report, ReportVersion, AuditLog
│   │   ├── state_machine.py     # Deterministic clinical lifecycle state machine engine
│   │   ├── values/              # Identifiers, TriagePriority, Modality value objects
│   │   └── exceptions.py        # Domain-specific typed exceptions
│   ├── application/             # Application Business Rules, Use Cases, Port Interfaces & DTOs
│   │   ├── use_cases/           # IngestStudyUseCase, RunAiDiagnosticTriageUseCase
│   │   ├── interfaces/          # StudyRepository, AgentOrchestrator, GuardrailService ports
│   │   └── tools/               # DICOM extraction, FHIR mapping, SHAP explainers
│   └── infrastructure/          # Outward Interface Adapters & Persistence Tier
│       ├── persistence/         # SQLAlchemy 2.0 Async models, repositories, outbox worker, seed
│       ├── adapters/            # PACS (DICOMweb), BackBone HMS, and CharmHealth EHR adapters
│       ├── celery/              # Celery task queue configuration for asynchronous outbox jobs
│       ├── kestra/              # Kestra standalone workflow orchestrator client
│       └── observability/       # Langfuse tracing, prompt management, and PHI sanitization
├── docs/                        # Comprehensive Master Documentation Suite
│   ├── ARCHITECTURE.md          # Clean Architecture specifications and layer boundaries
│   ├── DATA_MODEL.md            # PostgreSQL relational schema, ER diagrams, triggers, indexes
│   ├── AI_AGENT_SYSTEM.md       # Deep Agents, LangGraph, NeMo guardrails, and SHAP explainability
│   ├── SECURITY_AND_COMPLIANCE.md# HIPAA, FDA 21 CFR Part 11, cryptographic HMAC signatures, RBAC
│   ├── INTEGRATIONS_GUIDE.md    # PACS (QIDO/WADO), BackBone HMS, and CharmHealth FHIR R4 guides
│   ├── TESTING_STRATEGY.md      # Test plan matrix TC-001 through TC-056 across all test tiers
│   └── RUNBOOK.md               # Master Operational Runbook: deployment, secret rotation, DR
├── kestra/flows/                # Declarative YAML workflow pipelines (ingestion, retries, TAT SLA)
├── scripts/
│   └── backup_restore.sh        # PostgreSQL backup & restore script (RPO <= 15m / RTO <= 4h)
├── sims-radiology-marketing/    # Next-generation stakeholder showcase & marketing application
├── tests/                       # Complete automated test suite (TC-001 to TC-056)
│   ├── unit/                    # Unit tests for domain entities, state machine, outbox (20 tests)
│   ├── integration/             # Persistence, repositories, API endpoints, Kestra (10 tests)
│   ├── contract/                # PACS, BackBone, and CharmHealth adapter contract tests (10 tests)
│   ├── security/                # RBAC, clinical safety boundary, NeMo, PHI scrubbing (9 tests)
│   └── e2e/                     # End-to-end full study lifecycle validation (3 tests)
├── docker-compose.prod.yml      # Production on-prem 7-microservice compose configuration
└── pyproject.toml               # Python packaging, dependencies, Hatchling build, pytest configs
```

---

## 📖 Comprehensive Documentation Suite

For exhaustive architectural and operational deep dives, refer to our dedicated documentation guides:

| Guide | Description | Key Focus Areas |
|---|---|---|
| [**Architecture Specification**](docs/ARCHITECTURE.md) | Clean Architecture & DDD design | Dependency rule, layer responsibilities, sequence diagrams |
| [**Data Model & Persistence**](docs/DATA_MODEL.md) | Relational database schema | ER diagram, append-only triggers (TC-033), Transactional Outbox |
| [**AI Agentic System**](docs/AI_AGENT_SYSTEM.md) | Agentic layer & safety rails | Deep Agents, LangGraph, NeMo Guardrails, SHAP feature vectors |
| [**Security & Governance**](docs/SECURITY_AND_COMPLIANCE.md) | Healthcare compliance & crypto | HIPAA PHI sanitization, HMAC-SHA256 signatures, RBAC matrix |
| [**Integrations Guide**](docs/INTEGRATIONS_GUIDE.md) | Healthcare vendor adapters | DICOMweb QIDO/WADO, BackBone HMS reconciliation, CharmHealth FHIR R4 |
| [**Testing Strategy**](docs/TESTING_STRATEGY.md) | Test plan execution matrix | TC-001 through TC-056 mapping, coverage reports, regression tests |
| [**Master Operational Runbook**](docs/RUNBOOK.md) | Production operations manual | Microservices bootstrapping, secret rotation, DLQ, disaster recovery |

---

## ⚡ Quickstart: Local Development

### 1. Prerequisites
- Python 3.11, 3.12, or 3.14
- PostgreSQL 16 (running on port 5432)
- Redis 7 (running on port 6379)
- Node.js 20+ and npm (for web frontend development)

### 2. Environment Setup
```bash
# Clone repository
git clone https://github.com/OpenHealthAgents/sims_rad.git
cd sims_rad

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
```

### 3. Initialize Database
```bash
# Run Alembic migrations to create tables and append-only constraints
alembic upgrade head

# Seed synthetic test patients, studies, and worklist items
python -m core.infrastructure.persistence.seed
```

### 4. Run Development Servers
```bash
# Terminal 1: Run FastAPI Backend
uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Run Celery Outbox Worker
celery -A core.infrastructure.celery.app.celery_app worker --loglevel=info -Q default,outbox,high_priority

# Terminal 3: Run Lit / Vite Web Frontend
cd apps/web
npm install
npm run dev
```

Visit the interactive web workbench at `http://localhost:5173` and the OpenAPI Swagger documentation at `http://localhost:8000/docs`.

---

## 🐳 Production On-Premises Packaging (Docker Compose)

The production configuration packages 7 microservices across 3 segmented networks:

```bash
# Boot the full production microservices stack in background
docker compose -f docker-compose.prod.yml up --build -d

# Verify all containers are UP and Healthy
docker compose -f docker-compose.prod.yml ps
```

### Microservices Status Matrix
| Service | Container Name | Port Mapping | Health Probe URL | Network |
|---|---|---|---|---|
| **Nginx Web Gateway** | `sims_web_prod` | `80:80` | `http://localhost/health` | `sims_frontend_net` |
| **FastAPI Backend** | `sims_api_prod` | `8000` (internal) | `http://localhost:8000/health` | `frontend`, `backend`, `data` |
| **Celery Outbox Worker**| `sims_celery_worker_prod`| Internal | `celery inspect ping` | `sims_backend_net`, `sims_data_net` |
| **Kestra Orchestrator** | `sims_kestra_prod` | `8080:8080` | `http://localhost:8080/api/v1/health` | `sims_backend_net`, `sims_data_net` |
| **Langfuse Observability**| `sims_langfuse_prod` | `3000:3000` | `http://localhost:3000/api/public/health`| `sims_backend_net`, `sims_data_net` |
| **PostgreSQL 16** | `sims_postgres_prod` | `5432:5432` | `pg_isready -U sims_user` | `sims_data_net` |
| **Redis 7 Broker** | `sims_redis_prod` | `6379:6379` | `redis-cli ping` | `sims_backend_net`, `sims_data_net` |

---

## 💾 Database Backup & Disaster Recovery

The automated script [scripts/backup_restore.sh](scripts/backup_restore.sh) verifies **RPO ≤ 15 minutes** and **RTO ≤ 4 hours**:

```bash
# 1. Create compressed backup with SHA-256 checksum (RPO <= 15m)
bash scripts/backup_restore.sh backup

# 2. Verify SLA compliance of the latest available snapshot
bash scripts/backup_restore.sh verify-rpo

# 3. List available backup archives
bash scripts/backup_restore.sh list

# 4. Run automated non-destructive disaster recovery drill (restores to temporary drill DB)
bash scripts/backup_restore.sh drill

# 5. Restore specific backup to target database (RTO <= 4h)
bash scripts/backup_restore.sh restore ./backups/postgres/sims_radiology_backup_<TIMESTAMP>.dump.gz
```

---

## 🧪 Automated Verification & Test Plan

The platform includes 174 automated tests covering 100% of the Test Plan specifications (TC-001 through TC-056):

```bash
# Execute full test suite
pytest

# Results:
# ====================== 174 passed, 13 warnings in 34.25s ======================
```

### Breakdown of Test Suites
- **`tests/unit/` (20 tests):** Pure domain entity validation, state machine transitions, and concurrency version checks.
  - `TC-011`: Ingest duplicate inbound event -> Asserts idempotency (no duplicate work items).
  - `TC-012`: Ingest ambiguous patient match -> Asserts quarantine in exception queue.
  - `TC-017`: Reject invalid state transitions (`ready` -> `delivered` without finalization).
- **`tests/integration/` (10 tests):** SQLAlchemy async persistence, Transactional Outbox workers, FastAPI REST routes.
  - `TC-033`: Reject update or deletion on signed report versions via append-only constraints.
- **`tests/contract/` (10 tests):** External system mock contracts for PACS DICOMweb, BackBone HMS, and CharmHealth EHR.
- **`tests/security/` (9 tests):** Server-side RBAC, clinical safety boundaries, NeMo guardrails, and HIPAA PHI sanitization.
  - `TC-053`: Asserts AI agents cannot sign reports or autonomously finalize clinical records.
  - `TC-055`: Asserts patient names and MRNs are scrubbed before emitting Langfuse traces.
- **`tests/e2e/` (3 tests):** Complete study lifecycle walkthroughs from DICOM ingestion to radiologist sign-off and EHR delivery.

---

## 🔒 Security, Cryptographic Signatures & Governance

1. **Server-Side RBAC Enforcement:** Every REST route and state transition validates the active user role against the role-permission matrix.
2. **Cryptographic Signatures:** Finalized reports generate an HMAC-SHA256 signature using the clinician's credentials and canonical structured findings text.
3. **PHI Scrubbing:** All LLM prompts and outbound observability traces pass through regex scrubbers redacting names, MRNs, dates of birth, SSNs, and phone numbers.
4. **Audit Logging:** Every transition, assignment, draft, and sign-off generates an immutable, non-truncatable audit record in `audit_events`.

---

## 🌐 API Reference Matrix

| Method | Endpoint | Description | Required Role |
|---|---|---|---|
| `GET` | `/health` | Scaffold Liveness & Readiness Probe | Public |
| `GET` | `/api/v1/health` | Comprehensive Subsystems Health Probe | Public |
| `GET` | `/api/v1/work-items` | Filtered, paginated radiologist worklist | Any Authenticated |
| `GET` | `/api/v1/work-items/{id}` | Detailed work item view + Case Concierge summary | Any Authenticated |
| `GET` | `/api/v1/work-items/{id}/explainability` | SHAP feature importance vectors for TAT/SLA | Any Authenticated |
| `POST`| `/api/v1/work-items/{id}/assignments` | Assign or reassign case with reason code | `COORDINATOR`, `DIRECTOR` |
| `POST`| `/api/v1/work-items/{id}/transitions` | Request deterministic workflow transition | Any Authenticated |
| `POST`| `/api/v1/work-items/{id}/report-drafts` | Create structured report draft (`DRAFT_READY`) | `RESIDENT`, `RADIOLOGIST`, `DIRECTOR` |
| `POST`| `/api/v1/work-items/{id}/report-signoff`| Cryptographically sign & finalize report | `REPORTING_RADIOLOGIST`, `DIRECTOR` |
| `GET` | `/api/v1/agent/stream` | Server-Sent Events (SSE) dynamic UI stream | Any Authenticated |
| `GET` | `/api/v1/metrics/turnaround-times` | Turnaround time (TAT) and queue depth metrics | Any Authenticated |
| `GET` | `/api/v1/integrations/health` | Capability matrix & Outbox backlog monitor | `ADMINISTRATOR`, `DIRECTOR` |

---

## 📄 Contributing & License

Developed by the **SIMS Radiology AI Engineering Team** under the **Apache-2.0 License**.  
For inquiries and clinical integration onboarding, consult [docs/RUNBOOK.md](docs/RUNBOOK.md) or contact `ai-eng@sims-radiology.internal`.
