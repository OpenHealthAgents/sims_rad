"""
Use Case: Run AI Diagnostic Triage with Deep Agents and NeMo Guardrail Verification.
"""
from typing import Any
from core.application.dto.report_dto import DiagnosticTriageResultDTO, FindingDTO
from core.application.interfaces.agent_orchestrator import AgentOrchestratorInterface
from core.application.interfaces.guardrail_service import GuardrailServiceInterface
from core.application.interfaces.study_repository import StudyRepositoryInterface
from core.domain.entities.study import StudyLifecycleState
from core.domain.exceptions import StudyNotFoundError
from core.domain.values.triage_priority import TriagePriority
from core.infrastructure.observability.langfuse_config import instrument_agent


class RunAiDiagnosticTriageUseCase:
    def __init__(
        self,
        repository: StudyRepositoryInterface,
        agent_orchestrator: AgentOrchestratorInterface,
        guardrail_service: GuardrailServiceInterface,
    ) -> None:
        self.repository = repository
        self.agent_orchestrator = agent_orchestrator
        self.guardrail_service = guardrail_service

    @instrument_agent(name="RunAiDiagnosticTriageUseCase.execute", as_type="chain")
    async def execute(self, study_uid: str, **kwargs: Any) -> DiagnosticTriageResultDTO:
        study = await self.repository.get_by_uid(study_uid)
        if not study:
            raise StudyNotFoundError(f"Study with UID {study_uid} was not found.")

        # Transition study lifecycle to analysis
        study.transition_to(StudyLifecycleState.ANALYSIS_IN_PROGRESS)
        await self.repository.save(study)

        # Run Deep Agents analysis
        result = await self.agent_orchestrator.run_diagnostic_agent(
            study=study,
            metadata={"priority": study.priority.value, "modality": study.modality.value},
        )

        # Transition to Guardrail evaluation
        study.transition_to(StudyLifecycleState.GUARDRAIL_EVALUATION)
        is_safe, reasons = await self.guardrail_service.verify_radiology_output(
            study_uid=study_uid,
            clinical_text=result.impression,
            findings=[f.model_dump() for f in result.findings],
        )

        # Update triage priority if critical finding identified
        has_critical = any(f.is_critical for f in result.findings)
        if has_critical:
            study.escalate_priority(TriagePriority.STAT)

        study.transition_to(
            StudyLifecycleState.COMPLETED if is_safe else StudyLifecycleState.FAILED
        )
        await self.repository.save(study)

        return DiagnosticTriageResultDTO(
            study_uid=study_uid,
            triage_priority=study.priority,
            findings=result.findings,
            impression=result.impression,
            guardrail_passed=is_safe,
            guardrail_reasons=reasons,
            shap_summary=result.shap_summary,
        )
