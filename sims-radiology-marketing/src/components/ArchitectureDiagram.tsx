import React from 'react';

export const ArchitectureDiagram: React.FC = () => {
  return (
    <div className="bg-white dark:bg-navy-950 p-6 rounded-2xl border border-slate-200 dark:border-navy-800 font-mono text-xs text-slate-700 dark:text-slate-300 shadow-medical-card dark:shadow-medical-card-dark transition-colors">
      <div className="flex items-center justify-between mb-4 border-b border-slate-200 dark:border-navy-800 pb-3">
        <span className="text-teal-600 dark:text-cyan-400 font-bold uppercase tracking-wider">Clean Architecture & Monorepo Topology</span>
        <span className="text-slate-500 dark:text-slate-400">Dependencies Point Inwards Only</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        
        {/* Layer 1: Ingestion & Interop */}
        <div className="bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-navy-800 rounded-xl p-4 flex flex-col justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-teal-600 dark:text-cyan-400 block mb-2">01. INGESTION & INTEROP</span>
            <h4 className="text-navy-900 dark:text-white font-bold text-sm mb-2">DICOM & FHIR Gateway</h4>
            <ul className="space-y-1.5 text-[11px] text-slate-600 dark:text-slate-400">
              <li>• DIMSE C-STORE / C-FIND</li>
              <li>• PyDICOM Header Parser</li>
              <li>• Kestra Pipeline Flows</li>
              <li>• Celery Async Task Broker</li>
            </ul>
          </div>
          <div className="mt-4 pt-2 border-t border-slate-200 dark:border-navy-800 text-[10px] text-teal-600 dark:text-cyan-400">
            ↓ Asyncpg / PostgreSQL 16
          </div>
        </div>

        {/* Layer 2: Deep Agents Orchestrator */}
        <div className="bg-slate-50 dark:bg-navy-900 border border-teal-500/40 rounded-xl p-4 flex flex-col justify-between shadow-glow-teal/20">
          <div>
            <span className="text-[10px] uppercase font-bold text-teal-600 dark:text-cyan-300 block mb-2">02. AGENTIC CORE</span>
            <h4 className="text-navy-900 dark:text-white font-bold text-sm mb-2">LangGraph & Deep Agents</h4>
            <ul className="space-y-1.5 text-[11px] text-slate-700 dark:text-slate-300">
              <li>• Modality Triage State Machine</li>
              <li>• CT Neuro Hemorrhage Agent</li>
              <li>• Pulmonary Embolism Agent</li>
              <li>• Pneumothorax Detection Agent</li>
            </ul>
          </div>
          <div className="mt-4 pt-2 border-t border-slate-200 dark:border-navy-800 text-[10px] text-teal-600 dark:text-cyan-400">
            ↓ State Checkpointing
          </div>
        </div>

        {/* Layer 3: Safety Guardrails */}
        <div className="bg-slate-50 dark:bg-navy-900 border border-emerald-500/40 rounded-xl p-4 flex flex-col justify-between shadow-glow-emerald/20">
          <div>
            <span className="text-[10px] uppercase font-bold text-emerald-600 dark:text-emerald-400 block mb-2">03. SAFETY & XAI</span>
            <h4 className="text-navy-900 dark:text-white font-bold text-sm mb-2">NeMo Rails & SHAP</h4>
            <ul className="space-y-1.5 text-[11px] text-slate-700 dark:text-slate-300">
              <li>• NVIDIA NeMo Hallucination Rails</li>
              <li>• Clinical Policy Bounds Check</li>
              <li>• Pixel-Level SHAP Heatmaps</li>
              <li>• Confidence Scoring Engine</li>
            </ul>
          </div>
          <div className="mt-4 pt-2 border-t border-slate-200 dark:border-navy-800 text-[10px] text-emerald-600 dark:text-emerald-400">
            ✓ Guardrails Enforced
          </div>
        </div>

        {/* Layer 4: Presentation & Web Components */}
        <div className="bg-slate-50 dark:bg-navy-900 border border-slate-200 dark:border-navy-800 rounded-xl p-4 flex flex-col justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-indigo-600 dark:text-indigo-400 block mb-2">04. PRESENTATION & EHR</span>
            <h4 className="text-navy-900 dark:text-white font-bold text-sm mb-2">EHR & Web Worklist</h4>
            <ul className="space-y-1.5 text-[11px] text-slate-600 dark:text-slate-400">
              <li>• FastAPI Presentation API</li>
              <li>• A2UI Lit Web Components</li>
              <li>• FHIR DiagnosticReport Write</li>
              <li>• Langfuse Observability Traces</li>
            </ul>
          </div>
          <div className="mt-4 pt-2 border-t border-slate-200 dark:border-navy-800 text-[10px] text-indigo-600 dark:text-indigo-400">
            → Radiologist Workstation
          </div>
        </div>

      </div>
    </div>
  );
};
