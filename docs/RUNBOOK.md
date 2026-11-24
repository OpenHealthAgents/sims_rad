# SIMS Radiology AI Operating Agentic Platform - Master Operational Runbook

**Document Version:** 1.0.0-PROD  
**Target Architecture:** On-Premises Containerized Microservices  
**Compliance & Governance:** HIPAA, DICOMweb Standard, HL7 FHIR R4, SOC2 Type II  
**Recovery Objectives:** RPO ≤ 15 minutes | RTO ≤ 4 hours  

---

## 1. System Architecture & Network Topology

The SIMS Radiology AI Operating Agentic Platform is packaged as an on-premises microservices cluster orchestrating imaging ingestion, clinical context aggregation, autonomous draft reporting with NVIDIA NeMo guardrails, and EHR diagnostic delivery.

### 1.1 Microservices Inventory

| Container Name | Service | Image / Base | Internal Network | Exposed Ports | Health Check Probe |
|---|---|---|---|---|---|
| `sims_web_prod` | Nginx SPA & Reverse Proxy | `nginx:1.27-alpine` | `frontend-net` | `80:80` | `wget -q -O - http://127.0.0.1:80/health` |
| `sims_api_prod` | FastAPI REST & Agent Streaming | `python:3.12-slim` | `frontend-net`, `backend-net`, `data-net` | `8000` (internal) | `curl -f http://localhost:8000/health` |
| `sims_celery_worker_prod` | Celery Outbox & Async Tasks | `python:3.12-slim` | `backend-net`, `data-net` | None | `celery inspect ping` |
| `sims_kestra_prod` | Kestra Workflow Engine | `kestra/kestra:latest` | `backend-net`, `data-net` | `8080:8080` | `curl -f http://localhost:8080/api/v1/health` |
| `sims_langfuse_prod` | Langfuse Observability & Evals | `langfuse/langfuse:latest` | `backend-net`, `data-net` | `3000:3000` | `curl -f http://localhost:3000/api/public/health` |
| `sims_postgres_prod` | PostgreSQL 16 Persistence Tier | `postgres:16-alpine` | `data-net` | `5432:5432` | `pg_isready -U sims_user -d sims_radiology` |
| `sims_redis_prod` | Redis 7 Celery Broker & Cache | `redis:7-alpine` | `backend-net`, `data-net` | `6379:6379` | `redis-cli ping` |

### 1.2 Multi-Tier Network Segmentation

To prevent lateral movement and enforce strict security boundaries, network segmentation is configured in `docker-compose.prod.yml`:
- **`frontend-net` (Perimeter Network):** External traffic reaches only `sims_web_prod` on port 80/443. Nginx terminates client requests, enforces HTTPS/TLS, serves compiled Vite/Lit SPA assets, and reverse-proxies `/api/` and SSE streams `/api/v1/agent/stream` to `sims_api_prod`.
- **`backend-net` (Application Mesh):** Encrypted inter-service communication between `sims_api_prod`, `sims_celery_worker_prod`, `sims_kestra_prod`, and `sims_langfuse_prod`.
- **`data-net` (Isolated Persistence Layer):** Restricted strictly to PostgreSQL and Redis. Direct external access to database ports is denied in production firewalls.

```
       [ Radiologist / PACS / EHR Clients ]
                        │
                        ▼ Port 80 / 443
               ┌─────────────────┐
               │  sims_web_prod  │ (Nginx Reverse Proxy & A2UI SPA)
               └────────┬────────┘
                        │ frontend-net
                        ▼
               ┌─────────────────┐
               │  sims_api_prod  │ (FastAPI & Deep Agents Engine)
               └────────┬────────┘
     backend-net        │        backend-net
  ┌─────────────────────┼─────────────────────┐
  ▼                     ▼                     ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
│  sims_kestra │ │ sims_langfuse│ │sims_celery_worker_prod│
└──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘
       │                │                    │
  data-net              │ data-net           │ data-net
  └─────────────────────┴─────────┬──────────┘
                                  ▼
                    ┌───────────────────────────┐
                    │  sims_postgres_prod (16)  │
                    │  sims_redis_prod (7)      │
                    └───────────────────────────┘
```

---

## 2. Production Deployment & Bootstrapping

### 2.1 Host Prerequisites
- OS: Ubuntu 22.04 LTS / RHEL 9 / Windows Server 2022 with Docker Engine 26+ and Docker Compose v2.24+.
- Hardware: Minimum 8 vCPUs, 32 GB RAM, 250 GB NVMe storage (for PostgreSQL data volume and local PACS cache).
- Time Synchronization: Host `chrony` or `ntp` configured to maintain clock drift < 50ms (critical for JWT validation and DICOM timestamps).

### 2.2 Environment Configuration File (`.env.production`)
Create `.env.production` alongside `docker-compose.prod.yml` with sanitized production secrets:

```bash
# Environment
ENVIRONMENT=production
PROJECT_NAME="SIMS Radiology AI Operating Agentic Platform"
API_V1_STR=/api/v1

# Security & Secrets
SECRET_KEY="<GENERATE_64_CHAR_HEX_RANDOM_SECRET>"
ACCESS_TOKEN_EXPIRE_MINUTES=480

# PostgreSQL Tier
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
POSTGRES_USER=sims_user
POSTGRES_PASSWORD="<GENERATE_STRONG_DB_PASSWORD>"
POSTGRES_DB=sims_radiology

# Redis Broker Tier
REDIS_HOST=redis
REDIS_PORT=6379

# Celery Task URLs
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Langfuse Observability
LANGFUSE_HOST=http://langfuse:3000
LANGFUSE_PUBLIC_KEY="pk-lf-prod-sims-001"
LANGFUSE_SECRET_KEY="sk-lf-prod-sims-001"
NEXTAUTH_SECRET="<GENERATE_32_CHAR_SECRET>"
SALT="<GENERATE_SALT_STRING>"
ENCRYPTION_KEY="0000000000000000000000000000000000000000000000000000000000000000"

# Kestra Orchestrator
KESTRA_API_HOST=http://kestra:8080
KESTRA_NAMESPACE=sims.radiology

# Vendor Integrations
PACS_BASE_URL=https://pacs.simshospital.internal/dicomweb
BACKBONE_BASE_URL=https://hms.simshospital.internal/api/v1
CHARMHEALTH_BASE_URL=https://ehr.charmhealth.internal/fhir/r4
```

### 2.3 Starting the Production Cluster
Execute the production build and container startup:

```bash
# Pull base images and build local production microservices
docker compose -f docker-compose.prod.yml --env-file .env.production up --build -d

# Verify all containers are UP and Healthy
docker compose -f docker-compose.prod.yml ps
```

### 2.4 Running Database Migrations
Initialize database tables, append-only constraints, and outbox schema:

```bash
docker exec -it sims_api_prod alembic upgrade head
```

### 2.5 Health Check Matrix Verification
Verify readiness probes across all services:

```bash
# 1. Web Gateway
curl -i http://localhost/health
# Expected: HTTP/1.1 200 OK {"status":"healthy","service":"web"}

# 2. REST API Subsystems
curl -i http://localhost/api/v1/health
# Expected: HTTP/1.1 200 OK {"status":"healthy", "subsystems": {...}}

# 3. Integrations Matrix & Outbox Backlog
curl -i http://localhost/api/v1/integrations/health \
  -H "Authorization: Bearer <ADMIN_OR_DIRECTOR_TOKEN>"
# Expected: HTTP/1.1 200 OK {"overall_status":"HEALTHY","outbox_status":"HEALTHY"}

# 4. Kestra Orchestrator
curl -i http://localhost:8080/api/v1/health
# Expected: HTTP/1.1 200 OK {"status":"OK"}

# 5. Langfuse Observability
curl -i http://localhost:3000/api/public/health
# Expected: HTTP/1.1 200 OK {"status":"OK"}
```

---

## 3. Vendor Integration Onboarding Procedures

### 3.1 PACS / DICOMweb Adapter Onboarding
The PACS adapter connects to hospital imaging archives via standard DICOMweb protocols:
- **`QIDO-RS` Endpoint:** `GET /studies?StudyDate={date}&Modality={modality}` (Retrieves study header metadata).
- **`WADO-RS` Endpoint:** `GET /studies/{studyUID}/metadata` and `GET /studies/{studyUID}/rendered` (Retrieves frames and metadata without raw pixel storage in primary DB).

#### Setup Checklist:
1. Obtain the PACS DICOMweb Base URL and Application Entity (AE) Title from the radiology PACS administrator.
2. Ensure bidirectional firewall traversal on port 443/8042 between `sims_api_prod` and the PACS server.
3. Import hospital root CA certificates into `/usr/local/share/ca-certificates/` in `sims_api_prod` if self-signed certificates are used.
4. Verify metadata query via CLI:
   ```bash
   curl -k -H "Accept: application/dicom+json" \
     "https://pacs.simshospital.internal/dicomweb/studies?limit=1"
   ```

### 3.2 BackBone HMS Ingestion & Order Reconciliation
The BackBone HMS publishes ADT (Admission, Discharge, Transfer) and ORM (Order Entry) events:
- **Inbound Endpoint:** `POST /api/v1/integrations/backbone/ingest`
- **Reconciliation Logic:** Deterministic accession matching. If an accession is missing, patient identifiers conflict, or inbound payload is malformed, the system routes the study to the **Exception Quarantine Queue** (`quarantine_reason="AMBIGUOUS_PATIENT_MATCH"` or `"MISSING_ACCESSION"`).

#### Handshake Validation:
```bash
curl -X POST http://localhost:8000/api/v1/integrations/backbone/ingest \
  -H "Content-Type: application/json" \
  -H "X-BackBone-Signature: <HMAC_SHA256_PAYLOAD_SIGNATURE>" \
  -d '{
    "event_id": "EVT-TEST-001",
    "accession_number": "ACC-TEST-999",
    "patient_id": "MRN-10023",
    "modality": "CT",
    "procedure_code": "CT-CHEST"
  }'
```

### 3.3 CharmHealth EHR Diagnostic Report Delivery
Finalized and cryptographically signed radiology reports are dispatched to CharmHealth EHR via HL7 FHIR R4:
- **Target FHIR Resource:** `DiagnosticReport` (Status: `final`, Code: LOINC `18748-4`, Category: `RAD`).
- **Authentication:** OAuth2 Client Credentials (`client_id`, `client_secret`) with 3600-second token lifecycle.
- **Delivery Protocol:** Dispatched via Transactional Outbox worker with exponential backoff (retries: 1m, 5m, 15m, 60m).

---

## 4. Secret Rotation Policy & Procedures

Security policy mandates rotating all platform credentials every **90 days**, or immediately upon suspected compromise.

| Secret Type | Variable Name | Rotation Frequency | Service Impact |
|---|---|---|---|
| JWT Signing Key | `SECRET_KEY` | 90 days | Zero-downtime dual-key overlap |
| PostgreSQL Password | `POSTGRES_PASSWORD` | 90 days | Requires rolling restart of API and Celery |
| Redis Auth Token | `REDIS_PASSWORD` | 90 days | Rolling restart |
| CharmHealth OAuth Secret | `CHARMHEALTH_CLIENT_SECRET` | 180 days | Zero downtime |
| Langfuse Secret Key | `LANGFUSE_SECRET_KEY` | 90 days | Zero downtime |

### 4.1 Zero-Downtime JWT Secret Rotation
1. Update `SECRET_KEY_FALLBACK` in `.env.production` with the current active key.
2. Generate a new cryptographically secure 64-character hex key and assign it to `SECRET_KEY`.
3. Restart `sims_api_prod`:
   ```bash
   docker compose -f docker-compose.prod.yml restart api
   ```
4. The API middleware accepts tokens signed with either `SECRET_KEY` (new) or `SECRET_KEY_FALLBACK` (old) for the duration of the 8-hour token expiration window.
5. After 8 hours, remove `SECRET_KEY_FALLBACK` from `.env.production`.

### 4.2 Database Credential Rotation
1. Connect to PostgreSQL as superuser:
   ```bash
   docker exec -it sims_postgres_prod psql -U sims_user -d sims_radiology
   ```
2. Alter password:
   ```sql
   ALTER USER sims_user WITH PASSWORD 'NewStrongPassword2026!';
   ```
3. Update `POSTGRES_PASSWORD` in `.env.production`.
4. Gracefully restart dependent services:
   ```bash
   docker compose -f docker-compose.prod.yml restart api celery_worker langfuse
   ```

---

## 5. Queue & Pipeline Failure Reprocessing

### 5.1 Transactional Outbox Monitoring & Manual Drain
The transactional outbox ensures atomicity between database transactions and downstream event delivery:
- **Table:** `outbox_events` (columns: `id`, `aggregate_type`, `aggregate_id`, `event_type`, `payload`, `created_at`, `processed_at`).
- **Normal Backlog:** < 10 unprocessed events.
- **Alert Threshold:** Backlog > 100 events triggers `DEGRADED` health state in `/api/v1/integrations/health`.

#### Diagnosing Backlog:
```sql
-- Check count of pending outbox events
SELECT count(*) AS pending_events, min(created_at) AS oldest_pending
FROM outbox_events 
WHERE processed_at IS NULL;

-- Identify failing aggregate types
SELECT aggregate_type, event_type, count(*) 
FROM outbox_events 
WHERE processed_at IS NULL 
GROUP BY aggregate_type, event_type;
```

#### Manual Drain Command:
Run the outbox processor synchronously to flush the backlog:
```bash
docker exec -it sims_api_prod python -c "
import asyncio
from core.infrastructure.persistence.outbox_worker import process_outbox_batch
count = asyncio.run(process_outbox_batch(batch_size=500))
print(f'Manually processed {count} pending outbox events.')
"
```

### 5.2 Celery Worker Dead-Letter Queue (DLQ) Reprocessing
When Celery async tasks exceed `max_retries=3`, tasks are routed to the dead-letter queue `celery_dlq`.

#### Inspecting and Purging Celery Queues:
```bash
# Check Celery active workers and queue depth
docker exec -it sims_celery_worker_prod celery -A core.infrastructure.celery.app.celery_app inspect active

# Check registered tasks
docker exec -it sims_celery_worker_prod celery -A core.infrastructure.celery.app.celery_app inspect registered

# Re-queue failed tasks from DLQ
docker exec -it sims_celery_worker_prod python -c "
from core.infrastructure.celery.app import celery_app
# Trigger reprocessing for study processing tasks
celery_app.send_task('persistence.process_outbox_events_task', args=[100], queue='high_priority')
print('Dispatched high-priority retry task.')
"
```

### 5.3 Kestra Workflow Pipeline Failures
Kestra pipelines run asynchronously to orchestrate data flows (`kestra/flows/`):
- `study_ingestion_pipeline.yml`: Ingestion, deterministic reconciliation, DICOM parsing.
- `report_delivery_retry.yml`: Outbox polling, CharmHealth delivery retries with exponential backoff.
- `sla_monitor_pipeline.yml`: TAT monitoring, SLA breach notifications, SHAP explainability vector computation.

#### Reprocessing Failed Executions via Kestra API:
```bash
# List failed executions in the sims.radiology namespace
curl -s "http://localhost:8080/api/v1/executions?namespace=sims.radiology&state=FAILED" | jq .

# Restart execution from failed task
curl -X POST "http://localhost:8080/api/v1/executions/{executionId}/restart"
```

### 5.4 Exception Quarantine Queue Clearance
When inbound studies fail reconciliation (e.g., patient identity mismatch or duplicate accession with conflicting metadata):
1. Navigate to the Web UI -> **Reconciliation Queue**.
2. Or query quarantined work items via API:
   ```bash
   curl -H "Authorization: Bearer <TOKEN>" \
     "http://localhost:8000/api/v1/work-items?status=QUARANTINED"
   ```
3. A Clinical Coordinator reviews the mismatch against hospital ADT records and submits resolution:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/work-items/{id}/reconciliation-resolution" \
     -H "Authorization: Bearer <COORDINATOR_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"action": "OVERRIDE_AND_LINK", "target_patient_id": "MRN-10023", "justification": "Typo in incoming HL7 surname resolved"}'
   ```

---

## 6. Downtime & Disaster Recovery Procedures

### 6.1 SLA Targets
- **Recovery Point Objective (RPO):** ≤ 15 minutes. Backups are executed via cron every 15 minutes. Maximum potential data loss is limited to events within the 15-minute window.
- **Recovery Time Objective (RTO):** ≤ 4 hours. Automated restore procedures restore full system operation in under 2 minutes for typical datasets.

### 6.2 Automated Backup Schedule (Cron Setup)
Install the following cron entry on the database host to enforce the RPO ≤ 15 min SLA:

```cron
# /etc/cron.d/sims_radiology_backup
# Run database backup every 15 minutes
*/15 * * * * root /bin/bash /opt/sims_radiology/scripts/backup_restore.sh backup >> /var/log/sims_backup.log 2>&1
```

### 6.3 Database Backup & Restore Utility Commands (`scripts/backup_restore.sh`)

| Command | Description | Target SLA |
|---|---|---|
| `scripts/backup_restore.sh backup` | Creates gzip-compressed `pg_dump` with SHA-256 checksum, prunes archives > 7 days | RPO ≤ 15 min |
| `scripts/backup_restore.sh restore <file>` | Restores schema and data, validates SHA-256 checksum, executes row count assertions | RTO ≤ 4 hrs |
| `scripts/backup_restore.sh drill` | Restores latest backup into a temporary drill database, executes assertions, tears down | Non-destructive test |
| `scripts/backup_restore.sh verify-rpo` | Verifies age of latest snapshot; flags SLA breaches if age > 15 minutes | SLA Audit |
| `scripts/backup_restore.sh list` | Formatted inventory of all backup archives, sizes, and integrity verification | Operational status |

### 6.4 Cold-Standby Disaster Recovery Procedure
In the event of complete host failure or hardware loss:
1. Provision replacement VM/server with Docker Engine and Git.
2. Clone repository:
   ```bash
   git clone git@github.com:simshospital/sims-radiology.git /opt/sims_radiology
   cd /opt/sims_radiology
   ```
3. Restore `.env.production` from encrypted offsite key vault.
4. Transfer latest backup archive from offsite S3/NFS backup mirror into `./backups/postgres/`.
5. Start PostgreSQL container:
   ```bash
   docker compose -f docker-compose.prod.yml up -d postgres
   ```
6. Restore database:
   ```bash
   bash scripts/backup_restore.sh restore ./backups/postgres/sims_radiology_backup_<LATEST>.dump.gz
   ```
7. Start all remaining microservices:
   ```bash
   docker compose -f docker-compose.prod.yml up --build -d
   ```
8. Verify health probes across all 7 services.

---

## 7. Incident Response & Troubleshooting Playbooks

### Playbook 1: NeMo Guardrails Intercepting Clinical Drafts
- **Symptom:** AI draft reports fail with error `400 Guardrail Violation: HALLUCINATED_FINDINGS` or `SAFETY_INTERVENTION`.
- **Diagnosis:** NeMo Guardrails detected an ungrounded finding not supported by prior history or imaging modality facts.
- **Action:**
  1. Inspect Langfuse trace for the specific `work_item_id` at `http://localhost:3000`.
  2. If the finding is clinically valid but novel, the radiologist can bypass the AI draft and enter manual structured findings directly in the Web UI `ReportEditorWidget`.
  3. NeMo guardrail rails cannot be bypassed programmatically; human clinician signature is the ultimate safety boundary.

### Playbook 2: High Turnaround Time (TAT) / SLA Breach Escalation
- **Symptom:** Urgent or STAT studies exceed 60-minute turnaround time.
- **Diagnosis:** Check SHAP feature attribution metrics for queue delays:
  ```bash
  curl -H "Authorization: Bearer <TOKEN>" \
    "http://localhost:8000/api/v1/work-items/{id}/explainability"
  ```
  Attributes returned: `modality_complexity`, `radiologist_workload`, `prior_comparison_count`, `unassigned_wait_time`.
- **Action:** If `radiologist_workload` is the dominant feature, use `POST /api/v1/work-items/{id}/assignments` with `reason_code="LOAD_BALANCING"` to reassign the case to an available on-call radiologist.

### Playbook 3: Append-Only Report Version Immutability Violation (TC-033)
- **Symptom:** Application error when attempting to modify a finalized report version.
- **Expected Behavior:** System invariant. Finalized reports are cryptographically signed with SHA-256 and protected by PostgreSQL trigger `enforce_report_version_append_only`. Any `UPDATE` or `DELETE` statement is rejected with SQLSTATE `23514`.
- **Remediation:** If an addendum or correction is required, the radiologist must issue an **Addendum Version** using `POST /api/v1/work-items/{id}/report-drafts`, creating a new incremental version without mutating previous signed records.

---

**Emergency Platform Contacts:**  
- Lead AI Infrastructure Engineer: `ai-eng-oncall@sims-radiology.internal`  
- Chief of Radiology: `radiology-director@sims-radiology.internal`  
- Hospital Information Systems Helpdesk: Ext. 4400 / `it-support@sims-radiology.internal`
