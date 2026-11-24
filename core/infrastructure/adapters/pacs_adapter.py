"""
PACS / DICOMweb Adapter (Clean Architecture).
Leverages pydicom utilities to parse DICOM header metadata and DICOMweb interfaces (QIDO-RS / WADO-RS).
Strict Invariant: NEVER stores or exposes raw pixel data to the primary application database.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import io
import logging
from typing import Any, Dict, List, Optional, Union
import httpx
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.tag import Tag

from core.domain.entities.patient import Patient, ReconciliationStatus
from core.domain.entities.study import ImagingSeries, Modality, RadiologyStudy
from core.domain.exceptions import InvalidDICOMMetadataError
from core.infrastructure.adapters.exceptions import PACSConnectionError

logger = logging.getLogger("sims_radiology.adapters.pacs")

# Pixel data DICOM tags that must NEVER be persisted or exposed to DB
FORBIDDEN_PIXEL_TAGS = {
    Tag(0x7FE0, 0x0010),  # Pixel Data
    Tag(0x7FE0, 0x0008),  # Float Pixel Data
    Tag(0x7FE0, 0x0009),  # Double Float Pixel Data
    Tag(0x0028, 0x0004),  # Photometric Interpretation
}


@dataclass
class DICOMHeaderMetadata:
    """Safe, sanitized representation of DICOM metadata with zero pixel bytes."""
    study_instance_uid: str
    series_instance_uid: str
    sop_instance_uid: str
    modality: str
    patient_id: str
    patient_name: str
    patient_birth_date: Optional[str]
    patient_sex: Optional[str]
    accession_number: str
    study_date: Optional[datetime]
    study_description: str
    series_description: str
    series_number: int
    instance_number: int
    raw_metadata_json: Dict[str, Any] = field(default_factory=dict)


class PACSAdapter:
    """
    PACS / DICOMweb Adapter for communicating with Enterprise Imaging PACS archives.
    Implements QIDO-RS (query) and WADO-RS (retrieve / viewer) protocols.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8042/dicom-web",
        viewer_base_url: str = "http://localhost:3000/viewer",
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.viewer_base_url = viewer_base_url.rstrip("/")
        self.timeout = timeout

    @staticmethod
    def parse_dicom_bytes(
        dicom_bytes: bytes,
        stop_before_pixels: bool = True,
    ) -> DICOMHeaderMetadata:
        """
        Parse raw DICOM file bytes using pydicom.
        Enforces reading without loading pixel data when stop_before_pixels=True.
        """
        try:
            bio = io.BytesIO(dicom_bytes)
            ds: Dataset = pydicom.dcmread(
                bio,
                stop_before_pixels=stop_before_pixels,
                defer_size="1 KB",
            )
            return PACSAdapter.extract_header_metadata(ds)
        except Exception as e:
            logger.error(f"Failed to parse DICOM bytes: {e}", exc_info=True)
            raise InvalidDICOMMetadataError(f"Malformed DICOM stream: {e}") from e

    @staticmethod
    def parse_dicom_file(
        file_path: str,
        stop_before_pixels: bool = True,
    ) -> DICOMHeaderMetadata:
        """
        Parse a DICOM file on disk using pydicom with pixel exclusion.
        """
        try:
            ds: Dataset = pydicom.dcmread(
                file_path,
                stop_before_pixels=stop_before_pixels,
                defer_size="1 KB",
            )
            return PACSAdapter.extract_header_metadata(ds)
        except Exception as e:
            logger.error(f"Failed to parse DICOM file '{file_path}': {e}", exc_info=True)
            raise InvalidDICOMMetadataError(f"Cannot read DICOM file '{file_path}': {e}") from e

    @staticmethod
    def _get_val(ds: Dataset, tag: tuple, attr_name: str, default: Any = "") -> Any:
        elem = ds.get(tag)
        if elem is not None:
            return elem.value if elem.value is not None else default
        if hasattr(ds, attr_name):
            val = getattr(ds, attr_name)
            return val if val is not None else default
        return default

    @classmethod
    def extract_header_metadata(cls, ds: Dataset) -> DICOMHeaderMetadata:
        """
        Extract standardized metadata attributes from a pydicom Dataset.
        Strictly strips out any pixel data tags.
        """
        # Invariant check: Strip pixel data tags if present in dataset
        for tag in FORBIDDEN_PIXEL_TAGS:
            if tag in ds:
                del ds[tag]

        study_uid = str(cls._get_val(ds, (0x0020, 0x000D), "StudyInstanceUID", ""))
        series_uid = str(cls._get_val(ds, (0x0020, 0x000E), "SeriesInstanceUID", ""))
        sop_uid = str(cls._get_val(ds, (0x0008, 0x0018), "SOPInstanceUID", ""))
        modality = str(cls._get_val(ds, (0x0008, 0x0060), "Modality", "OT")).upper()
        patient_id = str(cls._get_val(ds, (0x0010, 0x0020), "PatientID", ""))
        patient_name = str(cls._get_val(ds, (0x0010, 0x0010), "PatientName", ""))
        birth_date = str(cls._get_val(ds, (0x0010, 0x0030), "PatientBirthDate", "")) or None
        sex = str(cls._get_val(ds, (0x0010, 0x0040), "PatientSex", "")) or None
        accession = str(cls._get_val(ds, (0x0008, 0x0050), "AccessionNumber", ""))
        study_desc = str(cls._get_val(ds, (0x0008, 0x1030), "StudyDescription", ""))
        series_desc = str(cls._get_val(ds, (0x0008, 0x103E), "SeriesDescription", ""))

        # Series & Instance numbers
        raw_series_no = cls._get_val(ds, (0x0020, 0x0011), "SeriesNumber", 1)
        raw_instance_no = cls._get_val(ds, (0x0020, 0x0013), "InstanceNumber", 1)
        try:
            series_no = int(raw_series_no)
        except (ValueError, TypeError):
            series_no = 1
        try:
            instance_no = int(raw_instance_no)
        except (ValueError, TypeError):
            instance_no = 1

        # Parse DICOM Study Date (YYYYMMDD)
        study_date_raw = str(cls._get_val(ds, (0x0008, 0x0020), "StudyDate", ""))
        study_date = None
        if study_date_raw and len(study_date_raw) == 8:
            try:
                study_date = datetime.strptime(study_date_raw, "%Y%m%d").replace(tzinfo=timezone.utc)
            except ValueError:
                study_date = datetime.now(timezone.utc)
        else:
            study_date = datetime.now(timezone.utc)

        # Sanitized metadata JSON representation (strictly without pixel data)
        safe_meta = {
            "StudyInstanceUID": study_uid,
            "SeriesInstanceUID": series_uid,
            "SOPInstanceUID": sop_uid,
            "Modality": modality,
            "PatientID": patient_id,
            "PatientName": patient_name,
            "PatientBirthDate": birth_date,
            "PatientSex": sex,
            "AccessionNumber": accession,
            "StudyDate": study_date_raw,
            "StudyDescription": study_desc,
            "SeriesDescription": series_desc,
            "SeriesNumber": series_no,
            "InstanceNumber": instance_no,
        }

        return DICOMHeaderMetadata(
            study_instance_uid=study_uid,
            series_instance_uid=series_uid,
            sop_instance_uid=sop_uid,
            modality=modality,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_birth_date=birth_date,
            patient_sex=sex,
            accession_number=accession,
            study_date=study_date,
            study_description=study_desc,
            series_description=series_desc,
            series_number=series_no,
            instance_number=instance_no,
            raw_metadata_json=safe_meta,
        )

    def to_domain_entities(
        self,
        meta: DICOMHeaderMetadata,
        source_system: str = "PACS-DICOMWEB",
        identifier_namespace: str = "urn:oid:sims:hospital:mrn",
    ) -> tuple[RadiologyStudy, Patient, ImagingSeries]:
        """
        Map sanitized DICOM header metadata to domain entities.
        Ensures strict Clean Architecture invariants (no pixel data leaks).
        """
        # 1. Domain Patient (RULE-01: Name parsed, authoritative MRN required)
        name_parts = meta.patient_name.split("^")
        family_name = name_parts[0] if name_parts else meta.patient_name
        given_name = name_parts[1] if len(name_parts) > 1 else None

        patient = Patient(
            patient_id=meta.patient_id or f"PAT-{meta.accession_number}",
            mrn=meta.patient_id or f"MRN-{meta.accession_number}",
            identifier_namespace=identifier_namespace,
            reconciliation_status=ReconciliationStatus.PENDING,
            family_name=family_name,
            given_name=given_name,
            birth_date=meta.patient_birth_date,
            gender=meta.patient_sex.lower() if meta.patient_sex else None,
        )

        # 2. Domain Series
        series = ImagingSeries(
            series_uid=meta.series_instance_uid,
            series_number=meta.series_number,
            modality=Modality(meta.modality),
            description=meta.series_description or meta.study_description,
            number_of_instances=1,
        )

        # 3. Domain Study
        study = RadiologyStudy(
            study_id=f"STU-{meta.accession_number or meta.study_instance_uid[-8:]}",
            study_instance_uid=meta.study_instance_uid,
            accession_number=meta.accession_number,
            modality=Modality(meta.modality),
            study_date=meta.study_date or datetime.now(timezone.utc),
            source_system=source_system,
            patient_id=patient.patient_id,
            description=meta.study_description,
            series=[series],
        )

        return study, patient, series

    # =========================================================================
    # DICOMweb QIDO-RS Interface (Query based on ID for DICOM Objects)
    # =========================================================================
    async def qido_search_studies(
        self,
        study_instance_uid: Optional[str] = None,
        patient_id: Optional[str] = None,
        accession_number: Optional[str] = None,
        modality: Optional[str] = None,
        study_date: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        QIDO-RS: Query studies from PACS DICOMweb endpoint.
        Returns list of matching DICOM JSON study descriptors.
        """
        url = f"{self.base_url}/studies"
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if study_instance_uid:
            params["StudyInstanceUID"] = study_instance_uid
        if patient_id:
            params["PatientID"] = patient_id
        if accession_number:
            params["AccessionNumber"] = accession_number
        if modality:
            params["Modality"] = modality.upper()
        if study_date:
            params["StudyDate"] = study_date

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, params=params, headers={"Accept": "application/dicom+json"})
                if res.status_code in (502, 503, 504):
                    raise PACSConnectionError(
                        f"PACS server returned gateway/outage status: {res.status_code}",
                        status_code=res.status_code,
                    )
                res.raise_for_status()
                return res.json()
        except httpx.TimeoutException as te:
            raise PACSConnectionError(f"PACS QIDO-RS request timed out: {te}") from te
        except httpx.NetworkError as ne:
            raise PACSConnectionError(f"PACS network error: {ne}") from ne
        except PACSConnectionError:
            raise
        except Exception as e:
            logger.error(f"QIDO-RS query failed: {e}", exc_info=True)
            raise PACSConnectionError(f"PACS QIDO-RS communication error: {e}") from e

    # =========================================================================
    # DICOMweb WADO-RS Interface (Web Access to DICOM Persistent Objects)
    # =========================================================================
    async def wado_retrieve_study_metadata(self, study_instance_uid: str) -> List[Dict[str, Any]]:
        """
        WADO-RS: Retrieve metadata for all series and instances in a study.
        Returns DICOM JSON metadata (no pixel data).
        """
        url = f"{self.base_url}/studies/{study_instance_uid}/metadata"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, headers={"Accept": "application/dicom+json"})
                if res.status_code in (502, 503, 504):
                    raise PACSConnectionError(
                        f"PACS WADO-RS gateway/outage status: {res.status_code}",
                        status_code=res.status_code,
                    )
                res.raise_for_status()
                return res.json()
        except httpx.TimeoutException as te:
            raise PACSConnectionError(f"PACS WADO-RS metadata request timed out: {te}") from te
        except httpx.NetworkError as ne:
            raise PACSConnectionError(f"PACS network error: {ne}") from ne
        except PACSConnectionError:
            raise
        except Exception as e:
            logger.error(f"WADO-RS metadata retrieval failed: {e}", exc_info=True)
            raise PACSConnectionError(f"PACS WADO-RS communication error: {e}") from e

    def wado_get_viewer_url(
        self,
        study_instance_uid: str,
        series_instance_uid: Optional[str] = None,
    ) -> str:
        """
        Construct a zero-footprint web viewer link (e.g. OHIF Viewer) for clinical viewing.
        Enables clinicians to stream images on demand without local database pixel storage.
        """
        url = f"{self.viewer_base_url}?StudyInstanceUIDs={study_instance_uid}"
        if series_instance_uid:
            url += f"&SeriesInstanceUIDs={series_instance_uid}"
        url += f"&wadoURL={self.base_url}"
        return url
