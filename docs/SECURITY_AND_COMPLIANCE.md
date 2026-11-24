# Security, Compliance & Governance Specification

## 1. Compliance Mandates & Threat Modeling

The SIMS Radiology platform processes Protected Health Information (PHI) subject to:
- **HIPAA Privacy & Security Rules (45 CFR Part 160 and Part 164)**
- **FDA 21 CFR Part 11 (Electronic Records; Electronic Signatures)**
- **HITECH Act Breach Notification Rule**
- **SOC 2 Type II Trust Services Criteria (Security, Confidentiality, Availability)**

---

## 2. Role-Based Access Control (RBAC) Matrix

Access permissions are enforced strictly server-side on every REST route and agent interaction via FastAPI dependencies (`apps/api/middleware/auth.py`).

| Permission / Action | RADIOLOGY_DIRECTOR | REPORTING_RADIOLOGIST | RADIOLOGY_RESIDENT | RADIOGRAPHER | COORDINATOR | ADMINISTRATOR |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `worklist:view` | Yes | Yes | Yes | Yes | Yes | Yes |
| `worklist:assign` | Yes | Yes | No | No | Yes | Yes |
| `worklist:reconcile` | Yes | No | No | Yes | Yes | Yes |
| `study:metadata_read` | Yes | Yes | Yes | Yes | Yes | Yes |
| `report:draft_create` | Yes | Yes | Yes | No | No | No |
| `report:finalize_sign`| Yes | Yes | No | No | No | No |
| `report:addendum` | Yes | Yes | No | No | No | No |
| `audit:trail_read` | Yes | No | No | No | No | Yes |
| `system:configure` | Yes | No | No | No | No | Yes |

### 2.1 Resident vs. Attending Sign-Off Protocol
- A `RADIOLOGY_RESIDENT` is permitted to create preliminary structured report drafts (`DRAFT_READY`).
- Attempting to finalize a report without the role `REPORTING_RADIOLOGIST` or `RADIOLOGY_DIRECTOR` is rejected with `HTTP 403 Forbidden` (`INSUFFICIENT_PERMISSIONS_FOR_SIGNATURE`).

---

## 3. Cryptographic Signature & Append-Only Immutability

### 3.1 Report Finalization Hashing Algorithm
When an authorized radiologist signs a report (`POST /api/v1/work-items/{id}/report-signoff`):
1. The structured text elements (`clinical_indication`, `findings`, `impression`, `recommendations`) are normalized into a canonical representation.
2. An HMAC-SHA256 digest is generated using the platform's root signing key concatenated with the signing clinician's user ID and timestamp:
   $$\text{Digest} = \text{HMAC-SHA256}(K_{\text{sign}}, \text{CanonicalText} \parallel \text{UserID} \parallel \text{Timestamp})$$
3. The cryptographic signature is recorded in `report_versions.cryptographic_signature`.
4. The version record is stamped with `finalized_at = NOW()`.
5. Database triggers immediately block any subsequent `UPDATE` or `DELETE` statements on that row.

---

## 4. PHI & PII Sanitization Safeguards

To prevent Protected Health Information from leaking to third-party LLM providers or external trace collectors (e.g. Langfuse):

### 4.1 HIPAA 18 Safe-Harbor De-Identification Rules
All outbound traces and prompt completions pass through the regex-based scrubber `sanitize_phi()` in `core/infrastructure/observability/langfuse_config.py`:
- **Names:** Scrubbed to `[PATIENT_NAME_REDACTED]`.
- **Medical Record Numbers (MRN):** Scrubbed to `[MRN_REDACTED]`.
- **Dates of Birth / Exact Ages > 89:** Scrubbed to `[DOB_REDACTED]`.
- **Phone Numbers, Emails, SSNs:** Scrubbed to `[CONTACT_REDACTED]` and `[SSN_REDACTED]`.
- **DICOM Accessions:** Normalized to non-identifying hash references.

---

## 5. Audit Logging Architecture (`core/domain/entities/audit_log.py`)

Every security-sensitive operation creates an immutable row in `audit_events`:
- **Fields Captured:**
  - `id`: Unique event UUID.
  - `timestamp`: UTC microsecond timestamp.
  - `user_id`: Authenticated user who performed the action.
  - `user_role`: Active role during invocation.
  - `action`: Specific operation (`STUDY_INGESTED`, `WORKLIST_CLAIMED`, `REPORT_DRAFTED`, `REPORT_SIGNED`, `STUDY_QUARANTINED`, `EMERGENCY_OVERRIDE`).
  - `resource_type` & `resource_id`: Target entity.
  - `ip_address`: Originating client IP address.
  - `correlation_id`: Distributed trace ID linking frontend SSE, REST requests, and Celery outbox tasks.
- **Retention:** Audit logs cannot be truncated or dropped; retained for a minimum of 7 years in compliance with healthcare data governance.
