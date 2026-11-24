import React from 'react';

export const Footer: React.FC<{ onNavigate: (page: string) => void }> = ({ onNavigate }) => {
  return (
    <footer className="bg-clinical-950 border-t border-clinical-800/80 text-slate-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          
          {/* Brand Info */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-clinical-900 border border-cyan-500/30 flex items-center justify-center">
                <span className="text-cyan-400 font-bold text-base">S</span>
              </div>
              <span className="font-bold text-lg text-white">SIMS Radiology AI</span>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              Enterprise clinical imaging agentic OS built on Clean Architecture, LangGraph multi-agent choreography, and NVIDIA NeMo Guardrails safety standards.
            </p>
            <div className="flex items-center gap-3 pt-2">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                ● NeMo Guardrails Verified
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                FHIR R4 Core
              </span>
            </div>
          </div>

          {/* Solutions Column */}
          <div>
            <h4 className="text-white font-semibold mb-4 text-xs tracking-wider uppercase">Platform Capabilities</h4>
            <ul className="space-y-2.5 text-xs">
              <li><button onClick={() => onNavigate('solutions')} className="hover:text-cyan-300">STAT Neuro & Pulmonary Triage</button></li>
              <li><button onClick={() => onNavigate('solutions')} className="hover:text-cyan-300">Multi-Agent LangGraph Choreography</button></li>
              <li><button onClick={() => onNavigate('solutions')} className="hover:text-cyan-300">PyDICOM Header & Metadata Extraction</button></li>
              <li><button onClick={() => onNavigate('solutions')} className="hover:text-cyan-300">SHAP Explainable Attribution Heatmaps</button></li>
              <li><button onClick={() => onNavigate('solutions')} className="hover:text-cyan-300">Kestra Flow Automated Ingestion</button></li>
            </ul>
          </div>

          {/* Architecture & Security */}
          <div>
            <h4 className="text-white font-semibold mb-4 text-xs tracking-wider uppercase">Enterprise Trust</h4>
            <ul className="space-y-2.5 text-xs">
              <li><button onClick={() => onNavigate('security')} className="hover:text-cyan-300">Air-Gapped On-Premises DMZ</button></li>
              <li><button onClick={() => onNavigate('security')} className="hover:text-cyan-300">NVIDIA NeMo Hallucination Rails</button></li>
              <li><button onClick={() => onNavigate('security')} className="hover:text-cyan-300">HIPAA & SOC 2 Type II Security</button></li>
              <li><button onClick={() => onNavigate('security')} className="hover:text-cyan-300">DICOM Part 10 & DIMSE C-STORE</button></li>
              <li><button onClick={() => onNavigate('security')} className="hover:text-cyan-300">FHIR R4 DiagnosticReport Bridge</button></li>
            </ul>
          </div>

          {/* Organization & CTA */}
          <div>
            <h4 className="text-white font-semibold mb-4 text-xs tracking-wider uppercase">Clinical Evaluation</h4>
            <p className="text-xs text-slate-400 mb-3">
              Pilot SIMS on-prem or simulate with your retrospective de-identified DICOM cohorts.
            </p>
            <button
              onClick={() => onNavigate('demo')}
              className="w-full py-2 px-3 text-xs font-medium text-white bg-clinical-900 border border-cyan-500/40 rounded-lg hover:border-cyan-400 hover:bg-clinical-850 transition"
            >
              Book Technical Architecture Walkthrough
            </button>
            <p className="text-[11px] text-slate-500 mt-3 font-mono">
              Docker compose & Helm deployments supported.
            </p>
          </div>

        </div>

        <div className="mt-12 pt-6 border-t border-clinical-900 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500">
          <p>© {new Date().getFullYear()} SIMS Radiology AI Platform. All rights reserved. Clean Architecture Medical Intelligence.</p>
          <div className="flex gap-4 mt-3 sm:mt-0 font-mono text-[11px]">
            <span>PACS Compliant</span>
            <span>•</span>
            <span>Zero Egress</span>
            <span>•</span>
            <span>ISO 27001 Ready</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
