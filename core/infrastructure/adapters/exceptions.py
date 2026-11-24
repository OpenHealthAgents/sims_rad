"""
External Adapter Exceptions (Clean Architecture).
Differentiates between retriable vendor outages and non-retriable domain/validation failures.
"""


class AdapterException(Exception):
    """Base exception for all external system adapter errors."""
    pass


class RetriableAdapterException(AdapterException):
    """
    Base exception for transient vendor outages (network drop, timeout, 502/503/504).
    Indicates that the operation should be retried via background outbox/celery task.
    """
    def __init__(self, message: str, vendor: str, status_code: int | None = None):
        super().__init__(f"[{vendor}] Transient Vendor Outage: {message}")
        self.vendor = vendor
        self.status_code = status_code


class VendorOutageError(RetriableAdapterException):
    """General vendor outage exception."""
    pass


class PACSConnectionError(RetriableAdapterException):
    """Raised when PACS / DICOMweb server is unreachable or times out."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message=message, vendor="PACS", status_code=status_code)


class BackBoneHMSConnectionError(RetriableAdapterException):
    """Raised when BackBone HMS endpoint is unreachable or times out."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message=message, vendor="BackBone_HMS", status_code=status_code)


class CharmHealthConnectionError(RetriableAdapterException):
    """Raised when CharmHealth EHR endpoint is unreachable or times out."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message=message, vendor="CharmHealth_EHR", status_code=status_code)


class NonRetriableAdapterException(AdapterException):
    """Base exception for deterministic or contract violation errors that should NOT be retried."""
    pass


class MissingAccessionNumberError(NonRetriableAdapterException):
    """Raised when an order or study ingestion payload lacks an Accession Number."""
    def __init__(self, details: str = "Accession Number is missing from payload."):
        super().__init__(f"Validation Error: {details}")


class OutOfOrderEventError(AdapterException):
    """Raised when an out-of-order event sequence is detected."""
    def __init__(self, event_id: str, current_state: str, incoming_event: str):
        super().__init__(
            f"Out-of-order event '{incoming_event}' received for '{event_id}' in state '{current_state}'."
        )
        self.event_id = event_id
        self.current_state = current_state
        self.incoming_event = incoming_event


class VendorCapabilityDisabledError(NonRetriableAdapterException):
    """Raised when an attempted operation is disabled in the vendor capability matrix."""
    def __init__(self, capability: str, vendor: str):
        super().__init__(f"Vendor capability '{capability}' is disabled for '{vendor}'.")
        self.capability = capability
        self.vendor = vendor
