"""
Langfuse Observability & Evals Connector.
Leverages patterns from reference_repos/langfuse and reference_repos/langfuse-examples.
Directly interfaces with core.infrastructure.observability.langfuse_config.
"""
from typing import Any, Dict, Optional
import logging
from core.infrastructure.config import settings
from core.infrastructure.observability.langfuse_config import (
    observability_service,
    sanitize_payload,
    mask_phi_text,
)

logger = logging.getLogger(__name__)


class LangfuseTelemetryService:
    """Wrapper around Langfuse SDK for tracing agent runs, latency, and guardrail decisions."""

    def __init__(self) -> None:
        self.host = settings.LANGFUSE_HOST
        self.public_key = settings.LANGFUSE_PUBLIC_KEY
        self.secret_key = settings.LANGFUSE_SECRET_KEY
        self.enabled = settings.LANGFUSE_ENABLED
        self._service = observability_service

    @property
    def _client(self) -> Optional[Any]:
        return self._service.client

    def trace_agent_execution(
        self,
        name: str,
        user_id: str,
        metadata: Dict[str, Any],
    ) -> Any:
        """Create a new trace for an agent run with sanitized metadata."""
        sanitized_meta = sanitize_payload(metadata)
        if self._client:
            try:
                return self._client.trace(name=name, user_id=user_id, metadata=sanitized_meta)
            except Exception as e:
                logger.debug(f"Langfuse trace creation error: {e}")
        return None

    def flush(self) -> None:
        self._service.flush()


langfuse_service = LangfuseTelemetryService()
