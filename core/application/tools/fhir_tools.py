"""
Sub-Agent Tools: FHIR DiagnosticReport and ImagingStudy generator.
Leverages patterns from reference_repos/fhir-core.
"""
from typing import Any, Dict
from datetime import datetime


class FhirDiagnosticReportTool:
    """Tool for sub-agents to convert AI findings into HL7 FHIR R4 DiagnosticReport resources."""

    def __init__(self) -> None:
        self.name = "fhir_report_generator"
        self.description = "Encapsulates diagnostic observations and findings into FHIR R4 JSON standard."

    def build_diagnostic_report(
        self,
        study_uid: str,
        patient_id: str,
        impression: str,
        findings: list,
    ) -> Dict[str, Any]:
        """Generates standard FHIR R4 DiagnosticReport resource."""
        return {
            "resourceType": "DiagnosticReport",
            "id": f"dr-{study_uid.replace('.', '-')[:32]}",
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                            "code": "RAD",
                            "display": "Radiology",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "24725-4",
                        "display": "CT Head without contrast",
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{patient_id}",
            },
            "effectiveDateTime": datetime.utcnow().isoformat() + "Z",
            "conclusion": impression,
            "conclusionCode": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "1386000",
                            "display": "Intracranial Hemorrhage",
                        }
                    ]
                }
            ],
        }
