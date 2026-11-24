# External System Integrations Guide

## 1. Integration Landscape

The SIMS Radiology platform functions as a clinical bridge connecting hospital picture archiving systems, hospital management systems, and electronic health record software:

```
[ PACS Archive ] ──(DICOMweb QIDO/WADO)──> [ SIMS Radiology ] ──(FHIR R4 DiagnosticReport)──> [ CharmHealth EHR ]
                                                  ▲
[ BackBone HMS ] ──────(ADT / ORM Webhooks)───────┘
```

---

## 2. PACS Adapter (`core/infrastructure/adapters/pacs_adapter.py`)

### 2.1 DICOMweb Protocol Specifications
- **`QIDO-RS` (Query based on ID for DICOM Objects via RESTful Services):**
  - Endpoint: `GET /dicomweb/studies?StudyDate={date}&Modality={modality}`
  - Parses DICOM multipart/json headers using `pydicom`.
  - Extracts DICOM tags:
    - `(0020,000D)` Study Instance UID
    - `(0020,000E)` Series Instance UID
    - `(0008,0060)` Modality
    - `(0010,0020)` Patient ID / MRN
    - `(0008,1030)` Study Description
- **`WADO-RS` (Web Access to DICOM Objects via RESTful Services):**
  - Endpoint: `GET /dicomweb/studies/{studyUID}/series/{seriesUID}/instances/{instanceUID}`
  - Returns rendered frames or viewer stream links.
- **Architectural Guardrail:** Bulk pixel data (e.g. multi-gigabyte CT/MRI volumes) is **never stored** in the primary application database. Only metadata, Series UIDs, and viewer endpoints are indexed.

---

## 3. BackBone HMS Adapter (`core/infrastructure/adapters/backbone_adapter.py`)

### 3.1 Order Ingestion & Deterministic Reconciliation
- Receives HL7 ADT (Admit/Discharge/Transfer) and ORM (Order Management) event notifications.
- **Reconciliation Algorithm:**
  1. Compares incoming accession number against existing database studies.
  2. If the accession exists with matching MRN and modality, the inbound event is treated as an idempotent update (TC-011).
  3. If accession matches an existing study but patient demographic attributes conflict, the study is placed in the **Exception Quarantine Queue** with reason `AMBIGUOUS_PATIENT_MATCH` (TC-012).
  4. If clean, transitions study state to `READY` and triggers worklist ranking.

---

## 4. CharmHealth EHR Adapter (`core/infrastructure/adapters/charmhealth_adapter.py`)

### 4.1 HL7 FHIR R4 Mapping Specification
When a report is finalized, the outbox worker transforms the internal report aggregate into a standard HL7 FHIR R4 `DiagnosticReport` resource:

```json
{
  "resourceType": "DiagnosticReport",
  "id": "DR-SIMS-2026-9941",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
          "code": "RAD",
          "display": "Radiology"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "18748-4",
        "display": "Diagnostic imaging report"
      }
    ]
  },
  "subject": {
    "reference": "Patient/MRN-10023"
  },
  "conclusion": "No acute cardiopulmonary disease. Stable cardiomegaly.",
  "conclusionCode": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "81803006",
          "display": "Cardiomegaly"
        }
      ]
    }
  ],
  "presentedForm": [
    {
      "contentType": "text/plain",
      "data": "Q0xJTklDQUwgSU5ESUNBVElPTjogLi4u"
    }
  ]
}
```

### 4.2 Error Handling & Delivery Retries
- Dispatched via Kestra pipeline `kestra/flows/report_delivery_retry.yml`.
- Retries on network timeout or HTTP 5xx with exponential backoff: 1 min, 5 min, 15 min, 60 min.
- Updates `report_deliveries` record with delivery confirmation timestamp and HTTP response headers.
