"""
Application Interface (Port) for NeMo Guardrails safety and policy verification.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple


class GuardrailServiceInterface(ABC):
    @abstractmethod
    async def verify_radiology_output(
        self,
        study_uid: str,
        clinical_text: str,
        findings: List[dict],
    ) -> Tuple[bool, List[str]]:
        """
        Verify that diagnostic output conforms to clinical safety,
        hallucination prevention, and institutional policy rails.
        Returns: (is_safe, list_of_violations_or_reasons)
        """
        pass
