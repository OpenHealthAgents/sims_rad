"""
Mock Test Harness for SIMS Radiology Platform External Adapters.
Generates synthetic DICOM files with pydicom and simulates vendor endpoints/outages using httpx.
"""
from datetime import datetime, timezone
import io
import os
import tempfile
from typing import Any, Dict, List, Optional
import uuid
import httpx
import pydicom
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid


class SyntheticDICOMBuilder:
    """
    Builds realistic, synthetic DICOM datasets with pydicom.
    Can generate metadata-only or dummy pixel data files.
    """

    @staticmethod
    def build_dataset(
        study_instance_uid: Optional[str] = None,
        series_instance_uid: Optional[str] = None,
        sop_instance_uid: Optional[str] = None,
        modality: str = "CT",
        patient_id: str = "PAT-MOCK-001",
        patient_name: str = "Skywalker^Luke",
        patient_birth_date: str = "19770525",
        patient_sex: str = "M",
        accession_number: str = "ACC-MOCK-9901",
        study_description: str = "CT Head Non-Contrast",
        series_description: str = "Brain 5mm Axial",
        study_date: str = "20261124",
        include_pixel_data: bool = True,
    ) -> FileDataset:
        """Construct a complete pydicom FileDataset with synthetic metadata."""
        sop_uid = sop_instance_uid or generate_uid()
        study_uid = study_instance_uid or generate_uid()
        series_uid = series_instance_uid or generate_uid()

        # 1. File Meta Information
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
        file_meta.MediaStorageSOPInstanceUID = sop_uid
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

        # 2. Main Dataset
        filename_dummy = "synthetic.dcm"
        ds = FileDataset(filename_dummy, {}, file_meta=file_meta, preamble=b"\0" * 128)

        # Standard DICOM Tags
        ds.SOPClassUID = SecondaryCaptureImageStorage
        ds.SOPInstanceUID = sop_uid
        ds.StudyInstanceUID = study_uid
        ds.SeriesInstanceUID = series_uid

        ds.Modality = modality
        ds.PatientID = patient_id
        ds.PatientName = patient_name
        ds.PatientBirthDate = patient_birth_date
        ds.PatientSex = patient_sex
        ds.AccessionNumber = accession_number
        ds.StudyDescription = study_description
        ds.SeriesDescription = series_description
        ds.StudyDate = study_date
        ds.SeriesNumber = 1
        ds.InstanceNumber = 1

        # Pixel data representation if requested
        if include_pixel_data:
            ds.Rows = 64
            ds.Columns = 64
            ds.BitsAllocated = 8
            ds.BitsStored = 8
            ds.HighBit = 7
            ds.PixelRepresentation = 0
            ds.SamplesPerPixel = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
            # 64 x 64 dummy pixel buffer
            ds.PixelData = b"\x80" * (64 * 64)

        return ds

    @classmethod
    def create_dicom_bytes(cls, **kwargs) -> bytes:
        """Return synthetic DICOM as raw byte array."""
        ds = cls.build_dataset(**kwargs)
        bio = io.BytesIO()
        pydicom.dcmwrite(bio, ds)
        return bio.getvalue()

    @classmethod
    def create_dicom_file(cls, directory: Optional[str] = None, **kwargs) -> str:
        """Write synthetic DICOM to a temporary file on disk and return path."""
        ds = cls.build_dataset(**kwargs)
        target_dir = directory or tempfile.gettempdir()
        file_path = os.path.join(target_dir, f"mock_{uuid.uuid4().hex[:8]}.dcm")
        pydicom.dcmwrite(file_path, ds)
        return file_path


class MockVendorTransport(httpx.AsyncBaseTransport):
    """
    Flexible mock HTTP transport for simulating PACS, HMS, and EHR vendor interfaces,
    including network drops, HTTP 500/502/503/504 errors, and timeouts.
    """

    def __init__(self) -> None:
        self.simulate_outage: bool = False
        self.outage_status_code: int = 503
        self.simulate_timeout: bool = False
        self.simulate_network_error: bool = False
        self.intercepted_requests: List[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.intercepted_requests.append(request)

        if self.simulate_timeout:
            raise httpx.ReadTimeout(f"Read timed out connecting to {request.url}", request=request)

        if self.simulate_network_error:
            raise httpx.ConnectError(f"Connection refused to {request.url}", request=request)

        if self.simulate_outage:
            return httpx.Response(
                status_code=self.outage_status_code,
                text="Vendor Service Temporarily Unavailable",
                request=request,
            )

        path = request.url.path
        # PACS Mock Endpoints
        if "/studies" in path:
            if path.endswith("/metadata"):
                # WADO-RS metadata
                mock_meta = [
                    {
                        "0020000D": {"vr": "UI", "Value": ["1.2.840.113619.2.55.3.mock"]},
                        "00080060": {"vr": "CS", "Value": ["CT"]},
                    }
                ]
                return httpx.Response(200, json=mock_meta, request=request)
            else:
                # QIDO-RS search
                results = [
                    {
                        "0020000D": {"vr": "UI", "Value": ["1.2.840.113619.2.55.3.mock"]},
                        "00100020": {"vr": "LO", "Value": ["PAT-MOCK-001"]},
                        "00080050": {"vr": "SH", "Value": ["ACC-MOCK-9901"]},
                        "00080060": {"vr": "CS", "Value": ["CT"]},
                    }
                ]
                return httpx.Response(200, json=results, request=request)

        # BackBone HMS Mock Endpoints
        if "/orders" in path:
            return httpx.Response(
                200,
                json={
                    "order_id": "ORD-12345",
                    "accession_number": "ACC-MOCK-9901",
                    "status": "SCHEDULED",
                    "modality": "CT",
                    "patient_id": "PAT-MOCK-001",
                },
                request=request,
            )

        # CharmHealth EHR Mock Endpoints
        if "/DiagnosticReport" in path:
            if request.method == "POST":
                return httpx.Response(
                    201,
                    json={
                        "resourceType": "DiagnosticReport",
                        "id": f"ehr-report-{uuid.uuid4().hex[:8]}",
                        "status": "final",
                    },
                    request=request,
                )
            else:
                return httpx.Response(
                    200,
                    json={"resourceType": "Bundle", "entry": []},
                    request=request,
                )

        if "/Patient" in path:
            return httpx.Response(
                200,
                json={
                    "resourceType": "Bundle",
                    "entry": [{"resource": {"resourceType": "Patient", "id": "PAT-MOCK-001"}}],
                },
                request=request,
            )

        if "/Encounter" in path:
            return httpx.Response(
                200,
                json={"resourceType": "Encounter", "id": "ENC-MOCK-99", "status": "finished"},
                request=request,
            )

        return httpx.Response(404, text="Not Found", request=request)
