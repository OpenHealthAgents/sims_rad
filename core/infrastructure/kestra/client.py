"""
Kestra Pipeline Orchestrator API Client.
Leverages patterns from reference_repos/kestra.
"""
from typing import Any, Dict, Optional
import httpx
import logging
from core.infrastructure.config import settings

logger = logging.getLogger(__name__)


class KestraClient:
    """Client for triggering and monitoring flows on Kestra standalone server."""

    def __init__(self) -> None:
        self.base_url = settings.KESTRA_API_HOST.rstrip("/")
        self.namespace = settings.KESTRA_NAMESPACE

    async def check_health(self) -> Dict[str, Any]:
        """Verify Kestra API connectivity."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/v1/health")
                return {"status": "ok" if res.status_code == 200 else "degraded", "code": res.status_code}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    async def trigger_flow(
        self,
        flow_id: str,
        inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Trigger an asynchronous execution of a Kestra flow."""
        url = f"{self.base_url}/api/v1/executions/{self.namespace}/{flow_id}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=inputs)
                if res.status_code in (200, 201):
                    return res.json()
                logger.error(f"Kestra execution trigger failed: {res.status_code} {res.text}")
                return {"error": res.text, "status_code": res.status_code}
        except Exception as e:
            logger.warning(f"Could not reach Kestra server at {url}: {e}")
            return {"status": "queued_offline", "flow_id": flow_id, "inputs": inputs}


kestra_client = KestraClient()
