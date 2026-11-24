"""
External System Adapters for SIMS Radiology Platform.
Includes PACS / DICOMweb, BackBone HMS, and CharmHealth EHR adapters.
"""
from core.infrastructure.adapters.backbone_adapter import (
    BackBoneHMSAdapter,
    OrderReconciliationResult,
)
from core.infrastructure.adapters.charmhealth_adapter import (
    CapabilityMatrix,
    CharmHealthEHRAdapter,
    ReportDeliveryResult,
)
from core.infrastructure.adapters.exceptions import (
    AdapterException,
    BackBoneHMSConnectionError,
    CharmHealthConnectionError,
    MissingAccessionNumberError,
    OutOfOrderEventError,
    PACSConnectionError,
    RetriableAdapterException,
    VendorCapabilityDisabledError,
    VendorOutageError,
)
from core.infrastructure.adapters.pacs_adapter import (
    DICOMHeaderMetadata,
    PACSAdapter,
)

__all__ = [
    "PACSAdapter",
    "DICOMHeaderMetadata",
    "BackBoneHMSAdapter",
    "OrderReconciliationResult",
    "CharmHealthEHRAdapter",
    "CapabilityMatrix",
    "ReportDeliveryResult",
    "AdapterException",
    "RetriableAdapterException",
    "VendorOutageError",
    "PACSConnectionError",
    "BackBoneHMSConnectionError",
    "CharmHealthConnectionError",
    "MissingAccessionNumberError",
    "OutOfOrderEventError",
    "VendorCapabilityDisabledError",
]
