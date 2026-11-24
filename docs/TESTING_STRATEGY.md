# Automated Testing Strategy & Test Plan Specification

## 1. Testing Pyramid & Verification Targets

The test suite enforces 100% verification of all requirements in the SIMS Radiology Test Plan (TC-001 through TC-056):

```
                       / \
                      /   \
                     / E2E \       TC-001 - TC-003 (Full Study Lifecycle)
                    /───────\
                   / Contract\     TC-039 - TC-048 (PACS, BackBone, CharmHealth)
                  /───────────\
                 /  Security   \   TC-049 - TC-056 (RBAC, NeMo Safety, PHI Scrubbing)
                /───────────────\
               /   Integration   \ TC-021 - TC-038 (DB, Outbox, API, Kestra)
              /───────────────────\
             /        Unit         \ TC-001 - TC-020 (State Machine, Entities, Celery)
            /───────────────────────\
```

---

## 2. Test Plan Matrix (TC-001 through TC-056)

### 2.1 Unit Tests (`tests/unit/` - TC-001 to TC-020)
- **TC-001 - TC-010:** Pure domain entity validation (`Patient`, `Study`, `WorkItem`, `Report`, `AuditLog`). Validates mandatory fields, timestamp defaults, and immutable ID generation.
- **TC-011:** Duplicate inbound event idempotency. Submitting an existing accession number with identical attributes does not create duplicate work items.
- **TC-012:** Ingestion reconciliation ambiguity quarantine. Submitting conflicting patient identifiers for an existing accession quarantines the study in `QUARANTINED` status with reason `AMBIGUOUS_PATIENT_MATCH`.
- **TC-013 - TC-016:** Worklist priority calculation. Validates STAT countdown (15m), URGENT countdown (60m), and ROUTINE countdown (24h).
- **TC-017:** State machine illegal transition rejection. Attempting to transition from `READY` directly to `DELIVERED` raises `InvalidStateTransitionError`.
- **TC-018 - TC-020:** Celery background task harness and outbox batch serialization.

### 2.2 Integration Tests (`tests/integration/` - TC-021 to TC-038)
- **TC-021 - TC-024:** Database repositories CRUD via SQLAlchemy 2.0 Async (`PatientRepository`, `StudyRepository`, `WorkItemRepository`, `ReportRepository`).
- **TC-025 - TC-028:** Outbox worker polling loop with `FOR UPDATE SKIP LOCKED`. Asserts batch processing and `processed_at` timestamp updates.
- **TC-029 - TC-032:** FastAPI presentation layer endpoints (`/work-items`, `/assignments`, `/transitions`, `/report-drafts`, `/report-signoff`).
- **TC-033:** Append-only report version immutability. Attempting to execute an `UPDATE` or `DELETE` on a finalized report version is rejected by database constraints.
- **TC-034 - TC-038:** Kestra declarative pipeline dry-runs and Langfuse trace integration.

### 2.3 Contract Tests (`tests/contract/` - TC-039 to TC-048)
- **TC-039 - TC-042:** PACS DICOMweb mock server contract tests. Verifies `QIDO-RS` response format and `WADO-RS` multipart streaming.
- **TC-043 - TC-045:** BackBone HMS ADT/ORM inbound webhook contract tests. Verifies HMAC header signatures and accession reconciliation.
- **TC-046 - TC-048:** CharmHealth EHR FHIR R4 contract tests. Validates `DiagnosticReport` schema validation against FHIR Core models.

### 2.4 Security & Safety Tests (`tests/security/` - TC-049 to TC-056)
- **TC-049 - TC-052:** Server-side RBAC authorization. Asserts residents cannot finalize reports, radiographers cannot draft reports, and unauthorized tokens return `401 Unauthorized`.
- **TC-053:** Clinical Safety Boundary. AI agents cannot sign reports or transition items to `FINALIZED`.
- **TC-054:** NVIDIA NeMo Guardrail hallucination and ungrounded finding rejection.
- **TC-055:** HIPAA PHI / PII sanitization. Asserts patient names and MRNs are redacted from outbound traces.
- **TC-056:** SQL injection and XSS payload resistance in structured findings.

### 2.5 End-to-End Tests (`tests/e2e/test_full_study_lifecycle.py`)
- Full lifecycle walkthrough:
  1. Post synthetic CT DICOM payload to BackBone ingest endpoint.
  2. Verify reconciliation creates `WorkItem` in `READY` state.
  3. Invoke Deep Agent Case Concierge to compile clinical summary and prior reports.
  4. Generate structured report draft via AI reporting tool passing NeMo safety guardrails (`DRAFT_READY`).
  5. Execute clinician sign-off via API with authorized radiologist credentials.
  6. Confirm state becomes `FINALIZED`, HMAC signature is created, and version becomes immutable.
  7. Confirm outbox event triggers delivery to CharmHealth EHR adapter.

---

## 3. Running the Test Suite

```bash
# Execute full test suite
pytest

# Execute specific test suites with verbose output
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/contract/ -v
pytest tests/security/ -v
pytest tests/e2e/ -v

# Measure coverage (must exceed 85%)
pytest --cov=core --cov=agents --cov-report=term-missing
```
