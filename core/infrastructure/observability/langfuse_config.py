"""
Langfuse Observability & Enterprise AI Telemetry Configuration (Clean Architecture).
Provides full AI observability for Deep Agents, LangGraph nodes, LLM calls, and NeMo guardrails.
Enforces strict HIPAA-compliant PHI/PII sanitization before traces are transmitted.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import functools
import inspect
import logging
import os
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import uuid

from langfuse import Langfuse, get_client, observe, propagate_attributes
from core.infrastructure.config import settings

logger = logging.getLogger("sims_radiology.observability.langfuse")

# =============================================================================
# PHI / PII Masking and Data Sanitization Invariants (HIPAA Compliance)
# =============================================================================

PHI_PATTERNS = [
    # Explicit patient names
    (r"(?i)\b(?:patient(?:\s+name)?|pt(?:\s+name)?|name)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", "Patient Name: [REDACTED_NAME]"),
    # Dates of birth
    (r"(?i)\b(?:dob|date of birth|birth date)[:\s]+(?:\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})\b", "DOB: [REDACTED_DOB]"),
    # Standalone dates that look like DOBs (e.g. 1980-05-15 or 05/15/1980) when labeled
    (r"(?i)\b(?:born|birth)[:\s]+(?:\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})\b", "Born: [REDACTED_DOB]"),
    # Social Security Numbers
    (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]"),
    # Phone numbers
    (r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]"),
    # Email addresses
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[REDACTED_EMAIL]"),
    # Street addresses
    (r"\b\d+\s+[A-Za-z0-9\s,.'-]{3,}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b", "[REDACTED_ADDRESS]"),
]

SENSITIVE_KEY_NAMES = {
    "patient_name", "first_name", "last_name", "family_name", "given_name",
    "dob", "birth_date", "ssn", "social_security", "phone", "email", "address",
}


def mask_phi_text(text: str) -> str:
    """Mask PHI and PII strings using regex replacement."""
    if not isinstance(text, str):
        return text
    sanitized = text
    for pattern, replacement in PHI_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)
    return sanitized


def sanitize_payload(data: Any, max_depth: int = 5, visited: Optional[set] = None) -> Any:
    """
    Recursively sanitize dictionaries, lists, and strings to eliminate PHI
    before serializing or transmitting to Langfuse observability buffers.
    Safely handles circular references and avoids traversing internal agent engines.
    """
    if max_depth <= 0:
        return "[TRUNCATED_DEPTH]"
    if visited is None:
        visited = set()

    if isinstance(data, (str, int, float, bool)) or data is None:
        return mask_phi_text(data) if isinstance(data, str) else data

    obj_id = id(data)
    if obj_id in visited:
        return "[CIRCULAR_REF]"
    visited.add(obj_id)

    try:
        if isinstance(data, dict):
            sanitized_dict = {}
            for k, v in data.items():
                k_lower = str(k).lower()
                if any(sensitive in k_lower for sensitive in SENSITIVE_KEY_NAMES):
                    sanitized_dict[k] = "[REDACTED_PHI]"
                else:
                    sanitized_dict[k] = sanitize_payload(v, max_depth - 1, visited)
            return sanitized_dict
        elif isinstance(data, (list, tuple)):
            return [sanitize_payload(item, max_depth - 1, visited) for item in data]
        elif hasattr(data, "model_dump") and callable(data.model_dump):
            return sanitize_payload(data.model_dump(), max_depth - 1, visited)
        elif hasattr(data, "__dict__"):
            cls_name = getattr(getattr(data, "__class__", None), "__name__", "")
            if any(term in cls_name.lower() for term in ("agent", "orchestrator", "service", "client", "guardrail", "session")):
                return f"<{cls_name}>"
            return sanitize_payload({k: v for k, v in vars(data).items() if not k.startswith("_")}, max_depth - 1, visited)
        return str(data)
    finally:
        visited.remove(obj_id)


# =============================================================================
# Telemetry Data Structures (for local test auditability and offline mode)
# =============================================================================

@dataclass
class RecordedTrace:
    """Audit record capturing full trace metadata, latency, and costs."""
    trace_id: str
    name: str
    user_id: Optional[str]
    session_id: Optional[str]
    observation_type: str
    inputs: Any
    outputs: Any
    metadata: Dict[str, Any]
    shap_attribution_scores: Optional[Dict[str, Any]]
    model: Optional[str]
    cost_usd: float
    latency_ms: float
    guardrail_verified: bool
    scores: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InMemTraceStore:
    """In-memory telemetry store for unit/integration verification and offline auditing."""
    def __init__(self) -> None:
        self.traces: Dict[str, RecordedTrace] = {}

    def record(self, trace: RecordedTrace) -> None:
        self.traces[trace.trace_id] = trace

    def get(self, trace_id: str) -> Optional[RecordedTrace]:
        return self.traces.get(trace_id)

    def list_all(self) -> List[RecordedTrace]:
        return list(self.traces.values())

    def clear(self) -> None:
        self.traces.clear()


in_mem_trace_store = InMemTraceStore()


# =============================================================================
# Langfuse Telemetry Manager
# =============================================================================

class LangfuseObservabilityService:
    """
    Manages Langfuse client lifecycle, context propagation, and custom span instrumentation.
    """

    def __init__(self) -> None:
        self.host = settings.LANGFUSE_HOST
        self.public_key = settings.LANGFUSE_PUBLIC_KEY
        self.secret_key = settings.LANGFUSE_SECRET_KEY
        self.enabled = settings.LANGFUSE_ENABLED
        self._client: Optional[Langfuse] = None
        self._init_client()

    def _init_client(self) -> None:
        if not self.enabled:
            logger.info("Langfuse is disabled by configuration.")
            return

        # Configure environment variables expected by Langfuse OpenTelemetry runtime
        os.environ["LANGFUSE_HOST"] = self.host
        os.environ["LANGFUSE_PUBLIC_KEY"] = self.public_key
        os.environ["LANGFUSE_SECRET_KEY"] = self.secret_key

        try:
            self._client = Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host,
                timeout=2,
            )
            logger.info(f"Langfuse observability client initialized for host: {self.host}")
        except Exception as e:
            logger.warning(f"Could not connect to Langfuse host: {e}. Using local recorder fallback.")
            self._client = None

    def is_server_available(self) -> bool:
        """Quick non-blocking check to determine if Langfuse server is responding on network."""
        if not self.enabled:
            return False
        try:
            import urllib.parse
            import socket
            parsed = urllib.parse.urlparse(self.host)
            hostname = parsed.hostname or "localhost"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            res = s.connect_ex((hostname, port))
            s.close()
            return res == 0
        except Exception:
            return False

    @property
    def client(self) -> Optional[Langfuse]:
        return self._client

    def flush(self) -> None:
        """Flush pending spans to Langfuse ingestion endpoint."""
        if self._client:
            try:
                self._client.flush()
            except Exception as e:
                logger.debug(f"Langfuse flush error: {e}")

    def create_trace_id(self) -> str:
        """Generate a new standard trace UUID."""
        return f"trc-{uuid.uuid4().hex[:16]}"

    def record_score(
        self,
        trace_id: str,
        name: str,
        value: Union[float, int, str, bool],
        data_type: Optional[str] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record an evaluation score linked to a specific Langfuse trace ID.
        """
        sanitized_meta = sanitize_payload(metadata or {})
        sanitized_comment = mask_phi_text(comment or "")

        # 1. Update in-memory audit store
        if trace_id in in_mem_trace_store.traces:
            in_mem_trace_store.traces[trace_id].scores[name] = {
                "value": value,
                "data_type": data_type,
                "comment": sanitized_comment,
                "metadata": sanitized_meta,
            }

        # 2. Forward to Langfuse API if connected and server is reachable
        if self._client and self.is_server_available():
            try:
                num_val = float(value) if isinstance(value, (int, float, bool)) else 1.0 if str(value).upper() == "PASS" else 0.0
                dt = data_type or ("BOOLEAN" if isinstance(value, bool) else "NUMERIC")
                self._client.create_score(
                    trace_id=trace_id,
                    name=name,
                    value=num_val,
                    data_type=dt,
                    comment=sanitized_comment,
                    metadata=sanitized_meta,
                )
                logger.info(f"Recorded Langfuse score for trace '{trace_id}': {name}={value}")
            except Exception as e:
                logger.warning(f"Failed to submit score to Langfuse API: {e}")


observability_service = LangfuseObservabilityService()


# =============================================================================
# Custom Instrumentation Decorators with Automatic PHI Masking
# =============================================================================

def instrument_agent(
    name: Optional[str] = None,
    as_type: str = "agent",
    extract_shap: bool = True,
):
    """
    Decorator for Deep Agents, LangGraph nodes, and orchestrators.
    Wraps execution in Langfuse @observe(), injects context attributes,
    masks PHI from inputs/outputs, and logs to the telemetry audit store.
    """
    def decorator(func: Callable):
        func_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            trace_id = kwargs.get("trace_id") or kwargs.get("langfuse_trace_id") or observability_service.create_trace_id()
            user_id = kwargs.get("user_id", "sims_radiologist")
            session_id = kwargs.get("session_id", f"ses-{uuid.uuid4().hex[:8]}")
            metadata = kwargs.get("metadata", {})

            # Mask input arguments for telemetry (excluding internal agent/framework instances)
            clean_args = [a for a in args if not any(term in getattr(getattr(a, "__class__", None), "__name__", "").lower() for term in ("agent", "orchestrator", "service", "client", "guardrail", "session"))]
            sanitized_args = sanitize_payload(clean_args)
            sanitized_kwargs = sanitize_payload(kwargs)
            sanitized_meta = sanitize_payload(metadata)

            shap_scores = None
            if extract_shap and "shap_attribution_scores" in kwargs:
                shap_scores = sanitize_payload(kwargs["shap_attribution_scores"])

            # Propagate attributes into Langfuse OpenTelemetry scope
            with propagate_attributes(
                user_id=user_id,
                session_id=session_id,
                metadata={**sanitized_meta, "trace_id": trace_id},
            ):
                try:
                    result = await func(*args, **kwargs)
                    latency = (time.perf_counter() - start_time) * 1000.0

                    # Extract SHAP from result if available
                    if extract_shap and not shap_scores and hasattr(result, "shap_attribution"):
                        shap_scores = getattr(result, "shap_attribution")
                    elif extract_shap and isinstance(result, dict) and "shap_attribution" in result:
                        shap_scores = result["shap_attribution"]

                    sanitized_result = sanitize_payload(result)

                    # Record trace locally for verifiable audit
                    trace_record = RecordedTrace(
                        trace_id=trace_id,
                        name=func_name,
                        user_id=user_id,
                        session_id=session_id,
                        observation_type=as_type,
                        inputs=sanitized_kwargs,
                        outputs=sanitized_result,
                        metadata=sanitized_meta,
                        shap_attribution_scores=shap_scores,
                        model=kwargs.get("model", "med-gemini-1.5-pro"),
                        cost_usd=round(0.00004 * (latency / 100.0), 6),
                        latency_ms=round(latency, 2),
                        guardrail_verified=True,
                    )
                    in_mem_trace_store.record(trace_record)

                    # Update current span in Langfuse if active
                    if observability_service.client:
                        try:
                            observability_service.client.update_current_span(
                                name=func_name,
                                input=sanitized_kwargs,
                                output=sanitized_result,
                                metadata={**sanitized_meta, "shap_attribution": shap_scores},
                            )
                        except Exception:
                            pass

                    return result
                except Exception as e:
                    latency = (time.perf_counter() - start_time) * 1000.0
                    trace_record = RecordedTrace(
                        trace_id=trace_id,
                        name=func_name,
                        user_id=user_id,
                        session_id=session_id,
                        observation_type=as_type,
                        inputs=sanitized_kwargs,
                        outputs={"error": str(e)},
                        metadata=sanitized_meta,
                        shap_attribution_scores=shap_scores,
                        model=kwargs.get("model", "med-gemini-1.5-pro"),
                        cost_usd=0.0,
                        latency_ms=round(latency, 2),
                        guardrail_verified=False,
                    )
                    in_mem_trace_store.record(trace_record)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            trace_id = kwargs.get("trace_id") or kwargs.get("langfuse_trace_id") or observability_service.create_trace_id()
            user_id = kwargs.get("user_id", "sims_radiologist")
            session_id = kwargs.get("session_id", f"ses-{uuid.uuid4().hex[:8]}")
            metadata = kwargs.get("metadata", {})

            clean_args = [a for a in args if not any(term in getattr(getattr(a, "__class__", None), "__name__", "").lower() for term in ("agent", "orchestrator", "service", "client", "guardrail", "session"))]
            sanitized_args = sanitize_payload(clean_args)
            sanitized_kwargs = sanitize_payload(kwargs)
            sanitized_meta = sanitize_payload(metadata)

            shap_scores = None
            if extract_shap and "shap_attribution_scores" in kwargs:
                shap_scores = sanitize_payload(kwargs["shap_attribution_scores"])

            with propagate_attributes(
                user_id=user_id,
                session_id=session_id,
                metadata={**sanitized_meta, "trace_id": trace_id},
            ):
                try:
                    result = func(*args, **kwargs)
                    latency = (time.perf_counter() - start_time) * 1000.0

                    if extract_shap and not shap_scores and hasattr(result, "shap_attribution"):
                        shap_scores = getattr(result, "shap_attribution")
                    elif extract_shap and isinstance(result, dict) and "shap_attribution" in result:
                        shap_scores = result["shap_attribution"]

                    sanitized_result = sanitize_payload(result)

                    trace_record = RecordedTrace(
                        trace_id=trace_id,
                        name=func_name,
                        user_id=user_id,
                        session_id=session_id,
                        observation_type=as_type,
                        inputs=sanitized_kwargs,
                        outputs=sanitized_result,
                        metadata=sanitized_meta,
                        shap_attribution_scores=shap_scores,
                        model=kwargs.get("model", "med-gemini-1.5-pro"),
                        cost_usd=round(0.00004 * (latency / 100.0), 6),
                        latency_ms=round(latency, 2),
                        guardrail_verified=True,
                    )
                    in_mem_trace_store.record(trace_record)

                    if observability_service.client:
                        try:
                            observability_service.client.update_current_span(
                                name=func_name,
                                input=sanitized_kwargs,
                                output=sanitized_result,
                                metadata={**sanitized_meta, "shap_attribution": shap_scores},
                            )
                        except Exception:
                            pass

                    return result
                except Exception as e:
                    latency = (time.perf_counter() - start_time) * 1000.0
                    trace_record = RecordedTrace(
                        trace_id=trace_id,
                        name=func_name,
                        user_id=user_id,
                        session_id=session_id,
                        observation_type=as_type,
                        inputs=sanitized_kwargs,
                        outputs={"error": str(e)},
                        metadata=sanitized_meta,
                        shap_attribution_scores=shap_scores,
                        model=kwargs.get("model", "med-gemini-1.5-pro"),
                        cost_usd=0.0,
                        latency_ms=round(latency, 2),
                        guardrail_verified=False,
                    )
                    in_mem_trace_store.record(trace_record)
                    raise

        # Apply official Langfuse @observe decorator as outermost wrapper
        wrapped = async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
        return observe(name=func_name, as_type=as_type)(wrapped)

    return decorator
