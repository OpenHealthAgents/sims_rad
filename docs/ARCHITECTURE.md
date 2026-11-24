# System Architecture & Clean Architecture Specification

## 1. Executive Summary & Design Philosophy

The **SIMS Radiology AI Operating Agentic Platform** is built from first principles following **Robert C. Martin's Clean Architecture**, **Domain-Driven Design (DDD)**, and **Hexagonal (Ports and Adapters) Architecture**. 

Radiology workflows operate under stringent clinical, operational, and regulatory constraints:
- **Zero Hallucination Toleration:** AI agents must never autonomously finalize or sign clinical reports without explicit credentialed radiologist sign-off.
- **Strict Clinical Invariants:** State transitions across study lifecycles (from ingestion to delivery) must be deterministic and irreversible.
- **Data Immutability & Auditability:** Every finalized diagnostic report version must be cryptographically immutable, append-only, and fully traceable with millisecond-precision audit logs.
- **Loose Coupling with Downstream Systems:** PACS (DICOMweb), Hospital Information Systems (BackBone HMS), and Electronic Health Records (CharmHealth FHIR R4) interact strictly through boundary adapters and asynchronous transactional outbox queues.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Frameworks & Drivers                            │
│   (FastAPI, PostgreSQL, Redis, Celery, Kestra, Langfuse, Lit/A2UI)     │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                    Interface Adapters                          │   │
│   │     (Controllers, Gateways, Presenters, REST Routes)           │   │
│   │   ┌────────────────────────────────────────────────────────┐   │   │
│   │   │                 Application Layer                      │   │   │
│   │   │    (Use Cases, DTOs, Agent Harness, Port Interfaces)   │   │   │
│   │   │   ┌────────────────────────────────────────────────┐   │   │   │
│   │   │   │                Domain Layer                    │   │   │   │
│   │   │   │   (Entities, Value Objects, State Machine)     │   │   │   │
│   │   │   └────────────────────────────────────────────────┘   │   │   │
│   │   └────────────────────────────────────────────────────────┘   │   │
│   └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer-by-Layer Architectural Breakdown

### 2.1 The Domain Layer (`core/domain/`)
The Domain Layer is the core of the platform. It contains pure business logic, domain entities, value objects, domain exceptions, and state machine transitions.
- **Zero External Dependencies:** Contains no framework dependencies (no FastAPI, no SQLAlchemy, no Pydantic BaseModels, no HTTP clients).
- **Core Entities:**
  - `Patient`: Patient demographics, master patient index (MRN) matching, clinical history references.
  - `Study`: Radiology study entity encapsulating DICOM Study Instance UID, Accession Number, Modality, Procedure Description, and series metadata.
  - `WorkItem`: Workflow unit assigned to radiologists, tracking SLA countdown, triage priority, assignment status, and review lifecycle.
  - `Report` & `ReportVersion`: Structured diagnostic report aggregate. Once a report version transitions to `FINALIZED`, it is cryptographically signed and immutable.
  - `AuditLog`: Append-only security and operational audit trail records.
- **Deterministic State Machine (`core/domain/state_machine.py`):**
  - Enforces explicit legal transitions:
    `RECEIVED` → `QUARANTINED` | `READY`  
    `READY` → `ASSIGNED`  
    `ASSIGNED` → `IN_REVIEW`  
    `IN_REVIEW` → `DRAFT_READY` | `PRELIMINARY`  
    `DRAFT_READY` → `FINALIZED` (Requires human clinician sign-off)  
    `FINALIZED` → `DELIVERED`  
  - Illegal transitions (e.g. attempting to jump from `READY` directly to `DELIVERED`, or attempting to mutate a `FINALIZED` report) raise explicit domain exceptions (`InvalidStateTransitionError`).

### 2.2 The Application Layer (`core/application/`)
The Application Layer defines the application's orchestrations, use case boundaries, Data Transfer Objects (DTOs), and Port Interfaces (Dependency Inversion).
- **Use Cases:**
  - `IngestStudyUseCase`: Orchestrates inbound DICOM/HMS study payloads, executes deterministic accession and MRN reconciliation, detects ambiguities, and transitions clean studies to `READY` state or flags conflicting records into `QUARANTINED`.
  - `RunAIDiagnosticTriageUseCase`: Invokes Deep Agent triage pipelines, computes SHAP feature importance vectors for queue prioritization, and prepares preliminary clinical summaries.
- **Port Interfaces (Abstract Base Classes):**
  - `StudyRepository`: Contract for persisting and retrieving studies and worklist items.
  - `AgentOrchestrator`: Contract for multi-agent case context and draft report generation.
  - `GuardrailService`: Contract for NeMo safety interventions.

### 2.3 The Infrastructure Layer (`core/infrastructure/`)
The Infrastructure Layer implements the technical capabilities required by the application ports:
- **Persistence (`core/infrastructure/persistence/`):**
  - SQLAlchemy 2.0 Async engine with `asyncpg` driver for PostgreSQL 16.
  - Append-only immutability enforced both at the ORM listener level and PostgreSQL database trigger level on `report_versions`.
  - Transactional Outbox pattern implemented via table `outbox_events` to ensure zero message loss between database transactions and Celery/Kestra pipelines.
- **External Adapters (`core/infrastructure/adapters/`):**
  - `PACSAdapter`: DICOMweb client implementing `QIDO-RS` (metadata query) and `WADO-RS` (frame retrieve). Never stores raw bulk pixel data in the relational database.
  - `BackBoneAdapter`: BackBone HMS integration handling ADT order entry, accession matching, and webhook signatures.
  - `CharmHealthAdapter`: FHIR R4 client formatting `DiagnosticReport` resources with LOINC and SNOMED-CT terminologies.
- **Observability (`core/infrastructure/observability/`):**
  - Langfuse integration with `@observe()` decorators.
  - Automatic PHI/PII sanitization (HIPAA safe-harbor scrubbing of patient names, dates of birth, SSNs, phone numbers) before emitting traces to Langfuse.

### 2.4 Presentation & API Layer (`apps/api/`)
- FastAPI modern async framework providing clean REST endpoints.
- Role-Based Access Control (RBAC) middleware verifying permissions on every route:
  - `RADIOLOGY_DIRECTOR`: Full administrative and reporting privileges.
  - `REPORTING_RADIOLOGIST`: Can claim studies, draft reports, sign/finalize reports.
  - `RADIOLOGY_RESIDENT`: Can prepare draft reports; cannot autonomously finalize without attending co-signature.
  - `RADIOGRAPHER`: Ingestion and modality verification.
  - `COORDINATOR`: Ingestion reconciliation and study reassignment.
  - `ADMINISTRATOR`: System configuration, secret rotation, and audit review.
- Real-time Server-Sent Events (SSE) streaming (`GET /api/v1/agent/stream`) streaming dynamic UI widgets emitted by Deep Agents directly to the browser.

### 2.5 User Interface Layer (`apps/web/`)
- Native Web Components built using Lit 3 and the Google A2UI (Agent-to-UI) framework.
- Dynamically rendered components:
  - `WorklistTable`: Reactive queue with modality filters, status badges, and SLA warning clocks.
  - `CaseConciergePanel`: AI-compiled clinical summary, prior report comparisons, and relevant lab values.
  - `ReportEditorWidget`: Structured findings and impression editor with real-time NeMo guardrails indicator.
  - `ExplainabilityWidget`: Visual SHAP feature attribution waterfall and bar charts.
  - `MetricsDashboardWidget`: Platform turnaround time (TAT), queue depth, and delivery retry charts.

---

## 3. Asynchronous Processing & Outbox Flow

```
[ FastAPI Endpoint ] ──> writes in single DB transaction ──> [ Postgres DB ]
                                                               ├─ work_items
                                                               ├─ reports
                                                               └─ outbox_events
                                                                       │
                                              ┌────────────────────────┘
                                              ▼ (Polls via SKIP LOCKED)
                                    [ Celery Outbox Worker ]
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
             [ Kestra Flow ]                                [ CharmHealth EHR ]
       (Ingestion / SLA Tracking)                         (FHIR DiagnosticReport)
```

1. **Transactional Outbox Guarantee:** All domain events destined for downstream message queues or external systems are written to `outbox_events` within the *same database transaction* as the entity state update.
2. **Concurrency Safety:** The Celery outbox polling worker utilizes PostgreSQL `FOR UPDATE SKIP LOCKED` query syntax. Multiple distributed workers can poll concurrently without duplicate task processing or deadlocks.
3. **At-Least-Once Delivery:** Events are only marked `processed_at = now()` after downstream acknowledgment. In failure scenarios, exponential backoff retries are executed up to the configured DLQ threshold.
