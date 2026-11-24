"""
Integration Tests: FastAPI presentation layer and health checks.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.src.main import app


@pytest.mark.asyncio
async def test_health_endpoint_returns_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["config_loaded"] is True
        assert "subsystems" in data
        assert data["subsystems"]["postgres"]["status"] == "configured"
        assert data["subsystems"]["redis_celery"]["status"] == "configured"
        assert data["subsystems"]["langfuse"]["status"] == "configured"
        assert data["subsystems"]["kestra"]["status"] == "configured"


@pytest.mark.asyncio
async def test_api_v1_health_returns_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["config_loaded"] is True


@pytest.mark.asyncio
async def test_root_endpoint_returns_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


@pytest.mark.asyncio
async def test_study_ingestion_and_triage_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Ingest study
        study_payload = {
            "study_uid": "1.2.840.10008.5.1.4.1.1.2.20261124.777",
            "accession_number": "ACC-TEST-777",
            "patient_id": "PATIENT-777",
            "modality": "CT",
            "description": "Stat CT Head for Acute Trauma",
            "priority": "ROUTINE",
            "series": [
                {
                    "series_uid": "1.2.840.10008.5.1.4.1.1.2.20261124.777.1",
                    "series_number": 1,
                    "modality": "CT",
                    "description": "Thin Axial Head",
                    "number_of_instances": 48,
                }
            ],
        }
        res_ingest = await client.post("/api/v1/studies", json=study_payload)
        assert res_ingest.status_code == 201
        ingested = res_ingest.json()
        assert ingested["study_uid"] == study_payload["study_uid"]

        # 2. Run diagnostic triage
        res_triage = await client.post(f"/api/v1/triage/{study_payload['study_uid']}/run")
        assert res_triage.status_code == 200
        triage_data = res_triage.json()
        assert triage_data["study_uid"] == study_payload["study_uid"]
        assert triage_data["triage_priority"] == "STAT"
        assert triage_data["guardrail_passed"] is True
        assert len(triage_data["findings"]) > 0
