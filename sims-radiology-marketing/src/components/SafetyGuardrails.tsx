import React from 'react';
import { 
  ShieldCheck, 
  Eye, 
  RefreshCw, 
  Lock, 
  CheckCircle2, 
  AlertOctagon, 
  FileCheck, 
  Sliders, 
  Cpu, 
  Database 
} from 'lucide-react';

export const SafetyGuardrails: React.FC = () => {
  const cards = [
    {
      id: 'nemo-rails',
      title: 'NeMo Guardrail Boundaries',
      badge: 'Deterministic Safety Rail',
      badgeColor: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
      icon: ShieldCheck,
      iconColor: 'text-emerald-500',
      description: 'Hard deterministic boundaries intercept and block any ungrounded assertions or autonomous report writebacks before clinician review.',
      capabilities: [
        'Blocks autonomous report signing: Strictly restricts output status to DRAFT_PENDING_REVIEW until radiologist credentials are authenticated.',
        'Real-time PHI / PII masking: Redacts patient identifiers, MRNs, and clinician names during local inference per HIPAA Safe Harbor standard.',
        'Topical scope enforcement: Intercepts out-of-scope diagnostic suggestions not supported by DICOM modality or body region.'
      ],
      technicalSpec: 'NVIDIA NeMo Guardrails Engine running locally on on-premise container cluster with zero external API calls.'
    },
    {
      id: 'shap-xai',
      title: 'SHAP Explainable AI (XAI)',
      badge: 'Pixel Attribution Layer',
      badgeColor: 'bg-teal-500/10 text-teal-600 dark:text-cyan-400 border-teal-500/30',
      icon: Eye,
      iconColor: 'text-teal-500',
      description: 'Eliminates black-box deep learning. Every triage escalation, priority score, and lesion candidate is verified through transparent feature attribution.',
      capabilities: [
        'Slice-level visual heatmaps: Generates SHAP attribution overlays indicating the exact pixel clusters that triggered the emergency flag.',
        'Quantified confidence percentiles: Surfaces exact statistical attribution scores (e.g. ICH attribution +0.84) alongside anatomical coordinates.',
        'Transparent worklist priority shifts: Radiologists inspect the rationalized explanation for why an acute study was expedited ahead of routine cases.'
      ],
      technicalSpec: 'Direct PyDICOM pixel array integration computed via local CUDA-accelerated Tree/DeepExplainer kernels.'
    },
    {
      id: 'outbox-idempotency',
      title: 'Transactional Outbox & Idempotency',
      badge: 'Zero-Loss Guarantee',
      badgeColor: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/30',
      icon: RefreshCw,
      iconColor: 'text-cyan-500',
      description: 'Ensures zero duplicate reports, zero ghost orders, and zero lost critical alerts during hospital network hiccups or PACS restarts.',
      capabilities: [
        'Idempotent transactional outbox: Orders, triage events, and report writes are committed within atomic PostgreSQL ACID transactions.',
        'Automatic deduplication keys: SHA-256 hash digests on study UIDs and accession numbers prevent redundant downstream broadcasts.',
        'Resilient store-and-forward buffer: If EHR or PACS endpoints drop offline, outbox workers queue and replay events without data loss.'
      ],
      technicalSpec: 'PostgreSQL 16 WAL with SQLAlchemy 2.0 Asyncpg transactional event tables and Celery retry queues.'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <span className="text-xs font-mono font-bold uppercase tracking-wider text-teal-600 dark:text-cyan-400 bg-teal-500/10 px-3 py-1 rounded-full border border-teal-500/20">
          Clinical AI Trust & Reliability Architecture
        </span>
        <h3 className="text-2xl sm:text-3xl font-extrabold text-navy-900 dark:text-white">
          Three Pillars of AI Safety & Operational Resilience
        </h3>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300">
          Engineered for hospital IT directors, CISO teams, and clinical governance boards.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.id}
              className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 p-6 sm:p-7 shadow-medical-card dark:shadow-medical-card-dark medical-card-hover flex flex-col justify-between"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold border ${card.badgeColor}`}>
                    {card.badge}
                  </span>
                  <div className="p-2 rounded-xl bg-slate-100 dark:bg-navy-850">
                    <Icon className={`w-5 h-5 ${card.iconColor}`} />
                  </div>
                </div>

                <h4 className="text-lg font-bold text-navy-900 dark:text-white">
                  {card.title}
                </h4>

                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  {card.description}
                </p>

                <div className="space-y-2.5 pt-2 border-t border-slate-100 dark:border-navy-800">
                  {card.capabilities.map((cap, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                      <span className="text-teal-500 font-bold shrink-0 mt-0.5">✓</span>
                      <span className="leading-relaxed">{cap}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-200 dark:border-navy-800 text-[11px] font-mono text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-navy-950 p-3 rounded-xl border border-slate-100 dark:border-navy-850">
                <strong className="text-teal-600 dark:text-cyan-400 block mb-0.5">SPECIFICATION:</strong>
                {card.technicalSpec}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SafetyGuardrails;
