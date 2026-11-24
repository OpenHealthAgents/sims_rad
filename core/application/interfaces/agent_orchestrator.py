"""
Application Interface (Port) for Agentic Orchestration (Deep Agents + LangGraph).
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from core.application.dto.report_dto import DiagnosticTriageResultDTO
from core.domain.entities.study import RadiologyStudy


class AgentOrchestratorInterface(ABC):
    @abstractmethod
    async def run_diagnostic_agent(
        self,
        study: RadiologyStudy,
        metadata: Dict[str, Any],
    ) -> DiagnosticTriageResultDTO:
        """Execute autonomous multi-agent analysis with Deep Agents harnesses."""
        pass
