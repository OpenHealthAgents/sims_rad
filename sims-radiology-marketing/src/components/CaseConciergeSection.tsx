import React, { useState } from 'react';
import { Bot, Sparkles, CheckCircle, AlertTriangle, ArrowRight, Eye, FileText, Layers } from 'lucide-react';

export const CaseConciergeSection: React.FC<{ onRequestDemo: () => void }> = ({ onRequestDemo }) => {
  const [selectedCase, setSelectedCase] = useState('case-1');

  const cases = [
    {
      id: 'case-1',
      title: 'NCCT Head: Acute Intraparenchymal Hemorrhage',
      modality: 'CT Head',
      urgency: 'STAT Critical',
      confidence: '98.4%',
      agent: 'DeepAgents-Neuro v2.4',
      findings: 'Hyperdense hematoma (34 x 22 mm) in right basal ganglia with surrounding vasogenic edema and 4.2 mm leftward midline shift.',
      guardrailStatus: 'Passed NeMo Rails: 0 Hallucinations',
      shapTarget: 'Right Basal Ganglia Density (+0.84 attribution)',
      timeToTriage: '18 seconds',
    },
    {
      id: 'case-2',
      title: 'CTPA: Acute Segmental Pulmonary Embolism',
      modality: 'CT Angio Chest',
      urgency: 'STAT Critical',
      confidence: '96.2%',
      agent: 'DeepAgents-Pulm v2.1',
      findings: 'Partial filling defect in right lower lobe posterior basal segmental artery. RV/LV ratio: 0.9 (no acute right heart strain).',
      guardrailStatus: 'Passed NeMo Rails: ACR Criteria Validated',
      shapTarget: 'Intraluminal Filling Defect (+0.79 attribution)',
      timeToTriage: '26 seconds',
    },
    {
      id: 'case-3',
      title: 'Portable AP Chest: Tension Pneumothorax',
      modality: 'XR Chest',
      urgency: 'STAT Emergent',
      confidence: '99.1%',
      agent: 'DeepAgents-Thorax v3.0',
      findings: 'Complete collapse of right lung with flattening of right hemidiaphragm and contralateral tracheal deviation.',
      guardrailStatus: 'Passed NeMo Rails: Critical Alert Triggered',
      shapTarget: 'Visceral Pleural Line Separation (+0.92 attribution)',
      timeToTriage: '7 seconds',
    }
  ];

  const current = cases.find(c => c.id === selectedCase) || cases[0];

  return (
    <section className="py-20 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-600 dark:text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider">
            <Bot className="w-3.5 h-3.5" />
            Autonomous Case Concierge
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-navy-900 dark:text-white tracking-tight">
            Intelligent Triage & Multi-Agent Pre-Read Synthesis
          </h2>
          <p className="text-slate-600 dark:text-slate-300 text-base">
            The SIMS Case Concierge orchestrates specialized neural sub-agents to analyze scans, compute quantitative lesion metrics, and prepare verified preliminary findings before the radiologist opens the study.
          </p>
        </div>

        {/* Case Concierge Interactive Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Column: Case Selector Queue */}
          <div className="lg:col-span-5 space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 font-bold mb-2">
              Live Ingested Emergency Stream
            </h3>
            {cases.map((c) => {
              const isSelected = selectedCase === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => setSelectedCase(c.id)}
                  className={`p-4 rounded-xl cursor-pointer border transition-all medical-card-hover ${
                    isSelected
                      ? 'bg-white dark:bg-navy-850 border-teal-500 shadow-glow-teal'
                      : 'bg-white/80 dark:bg-navy-900/60 border-slate-200 dark:border-navy-800 hover:border-teal-400'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                      {c.urgency}
                    </span>
                    <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                      Triage: {c.timeToTriage}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-navy-900 dark:text-white mb-1">{c.title}</h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">Modality: {c.modality}</p>
                </div>
              );
            })}
          </div>

          {/* Right Column: Case Concierge Synthesized Dossier */}
          <div className="lg:col-span-7 bg-white dark:bg-navy-900 rounded-2xl p-6 sm:p-8 border border-slate-200 dark:border-navy-800 shadow-medical-card dark:shadow-medical-card-dark space-y-6">
            
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-200 dark:border-navy-800">
              <div>
                <span className="text-xs font-mono text-teal-600 dark:text-cyan-400 font-bold">
                  {current.agent}
                </span>
                <h3 className="text-lg font-bold text-navy-900 dark:text-white mt-0.5">
                  {current.title}
                </h3>
              </div>
              <div className="text-right">
                <span className="text-xs font-mono text-slate-400 block">Agent Confidence</span>
                <span className="text-lg font-mono font-extrabold text-teal-600 dark:text-teal-400">
                  {current.confidence}
                </span>
              </div>
            </div>

            {/* Findings Box */}
            <div className="space-y-3">
              <h4 className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 font-bold flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-teal-500" />
                Synthesized Preliminary Findings
              </h4>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 text-sm text-navy-900 dark:text-slate-200 leading-relaxed font-sans">
                {current.findings}
              </div>
            </div>

            {/* Guardrail & SHAP Verification Badges */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-3.5 rounded-xl bg-teal-500/5 dark:bg-teal-500/10 border border-teal-500/20 text-xs space-y-1">
                <div className="flex items-center gap-1.5 text-teal-700 dark:text-teal-300 font-bold">
                  <CheckCircle className="w-4 h-4 text-teal-500" />
                  NVIDIA NeMo Clinical Rail
                </div>
                <p className="text-slate-600 dark:text-slate-300 text-[11px] font-mono">
                  {current.guardrailStatus}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-cyan-500/5 dark:bg-cyan-500/10 border border-cyan-500/20 text-xs space-y-1">
                <div className="flex items-center gap-1.5 text-cyan-700 dark:text-cyan-300 font-bold">
                  <Eye className="w-4 h-4 text-cyan-500" />
                  SHAP Explainability Layer
                </div>
                <p className="text-slate-600 dark:text-slate-300 text-[11px] font-mono">
                  {current.shapTarget}
                </p>
              </div>
            </div>

            {/* Clinician in the loop action */}
            <div className="pt-4 border-t border-slate-200 dark:border-navy-800 flex flex-col sm:flex-row items-center justify-between gap-4">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Awaiting Radiologist verification & e-signature.
              </p>
              <button
                onClick={onRequestDemo}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-xs font-bold text-white bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 shadow-glow-teal transition"
              >
                Launch Radiologist Review Studio
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

          </div>

        </div>

      </div>
    </section>
  );
};
