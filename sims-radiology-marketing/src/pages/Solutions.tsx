import React from 'react';

export const Solutions: React.FC<{ onNavigate: (page: string) => void }> = ({ onNavigate }) => {
  const clinicalUseCases = [
    {
      modality: 'CT',
      condition: 'Acute Intracranial Hemorrhage (ICH)',
      urgency: 'STAT Critical (< 15 mins)',
      description: 'DeepAgents-Neuro sub-agent inspects non-contrast head CT series. Pinpoints subdural, epidural, subarachnoid, and intraparenchymal bleeds with midline shift calculation.',
      latency: '24s ingestion-to-alert',
      confidence: '98.4%',
      badgeColor: 'border-rose-500/40 bg-rose-500/10 text-rose-400'
    },
    {
      modality: 'CTPA',
      condition: 'Pulmonary Embolism (PE)',
      urgency: 'STAT Critical (< 30 mins)',
      description: 'DeepAgents-Pulm tracks pulmonary arterial branches in contrast-enhanced chest CTs, detecting occlusive and saddle embolisms with right ventricular strain indicators.',
      latency: '38s ingestion-to-alert',
      confidence: '96.8%',
      badgeColor: 'border-rose-500/40 bg-rose-500/10 text-rose-400'
    },
    {
      modality: 'XR',
      condition: 'Tension Pneumothorax & Acute Rib Fractures',
      urgency: 'Urgent Priority (< 45 mins)',
      description: 'Instant triage of portable ICU and ED chest radiographs. Detects pleural line displacement, mediastinal shift, and acute osseous discontinuity.',
      latency: '8s ingestion-to-alert',
      confidence: '99.1%',
      badgeColor: 'border-amber-500/40 bg-amber-500/10 text-amber-400'
    },
    {
      modality: 'MRI',
      condition: 'Acute Ischemic Stroke & Diffusion Restriction',
      urgency: 'STAT Emergent (< 20 mins)',
      description: 'DWI/ADC mismatch quantification sub-agent for automated ischemic core and penumbra volumetric approximation.',
      latency: '52s ingestion-to-alert',
      confidence: '95.9%',
      badgeColor: 'border-indigo-500/40 bg-indigo-500/10 text-indigo-400'
    }
  ];

  return (
    <div className="py-16 space-y-20">
      
      {/* Solutions Header */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
        <span className="text-xs font-mono font-semibold uppercase tracking-widest text-cyan-400 bg-cyan-950/60 border border-cyan-500/20 px-3 py-1 rounded-full">
          Clinical Modalities & Agent Specialization
        </span>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white">
          Dedicated Sub-Agents for High-Acuity Diagnostic Triage
        </h1>
        <p className="text-slate-300 max-w-2xl mx-auto text-base">
          SIMS doesn't rely on generic LLMs for medical images. Specialized sub-agents orchestrate across modalities with tailored computer vision models, audited by NeMo rails.
        </p>
      </section>

      {/* Clinical Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {clinicalUseCases.map((useCase, idx) => (
            <div key={idx} className="glass-panel rounded-2xl p-7 border border-clinical-800 space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 rounded-md bg-clinical-900 border border-cyan-500/40 text-cyan-300 font-mono font-bold text-sm">
                    {useCase.modality}
                  </span>
                  <span className={`px-2.5 py-0.5 rounded text-[11px] font-mono border ${useCase.badgeColor}`}>
                    {useCase.urgency}
                  </span>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  {useCase.latency}
                </span>
              </div>

              <div>
                <h3 className="text-xl font-bold text-white mb-2">{useCase.condition}</h3>
                <p className="text-sm text-slate-300 leading-relaxed">{useCase.description}</p>
              </div>

              <div className="pt-4 border-t border-clinical-850 flex items-center justify-between text-xs">
                <span className="text-slate-400">Validation Benchmark:</span>
                <span className="font-mono text-emerald-400 font-bold bg-emerald-950/40 px-2 py-1 rounded border border-emerald-500/30">
                  AUC Confidence: {useCase.confidence}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Integration Ecosystem */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 bg-clinical-900/50 rounded-3xl p-10 border border-clinical-800">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-2xl font-bold text-white">Universal Healthcare Interoperability</h2>
          <p className="text-xs text-slate-400 mt-2">
            Engineered to bridge standard medical imaging networks (PACS, VNA, RIS, and EHR)
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center font-mono text-xs">
          <div className="bg-clinical-950 p-4 rounded-xl border border-clinical-800">
            <p className="text-cyan-400 font-bold text-sm mb-1">DICOMweb & DIMSE</p>
            <p className="text-slate-400 text-[11px]">C-STORE, C-FIND, WADO-RS</p>
          </div>
          <div className="bg-clinical-950 p-4 rounded-xl border border-clinical-800">
            <p className="text-cyan-400 font-bold text-sm mb-1">HL7 FHIR R4</p>
            <p className="text-slate-400 text-[11px]">DiagnosticReport & Observation</p>
          </div>
          <div className="bg-clinical-950 p-4 rounded-xl border border-clinical-800">
            <p className="text-cyan-400 font-bold text-sm mb-1">EHR Connectors</p>
            <p className="text-slate-400 text-[11px]">Epic, Cerner, Sectra, GE</p>
          </div>
          <div className="bg-clinical-950 p-4 rounded-xl border border-clinical-800">
            <p className="text-cyan-400 font-bold text-sm mb-1">Web Components</p>
            <p className="text-slate-400 text-[11px]">A2UI Reactive Lit Framework</p>
          </div>
        </div>

        <div className="text-center mt-8">
          <button
            onClick={() => onNavigate('demo')}
            className="px-6 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold"
          >
            Request Modality Benchmark Suite
          </button>
        </div>
      </section>

    </div>
  );
};
