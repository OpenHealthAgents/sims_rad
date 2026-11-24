import React, { useState } from 'react';
import { ListFilter, FileCheck, Clock, Check, Send, Sparkles, AlertCircle } from 'lucide-react';

export const WorklistReportingSection: React.FC<{ onRequestDemo: () => void }> = ({ onRequestDemo }) => {
  const [filter, setFilter] = useState<'ALL' | 'STAT' | 'URGENT'>('ALL');
  const [signedOff, setSignedOff] = useState(false);

  const worklistItems = [
    {
      acc: 'ACC-88319',
      patient: 'ANON-77491',
      modality: 'CT',
      exam: 'CT HEAD W/O CONTRAST',
      urgency: 'STAT',
      waitTime: '4 min',
      aiTriage: 'Acute ICH Detected (98.4%)',
      badgeClass: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30'
    },
    {
      acc: 'ACC-88320',
      patient: 'ANON-41209',
      modality: 'XR',
      exam: 'CHEST 1 VIEW PORTABLE',
      urgency: 'STAT',
      waitTime: '11 min',
      aiTriage: 'Large Right Pneumothorax',
      badgeClass: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30'
    },
    {
      acc: 'ACC-88321',
      patient: 'ANON-99023',
      modality: 'CT',
      exam: 'CT ANGIO CHEST (PE PROTOCOL)',
      urgency: 'URGENT',
      waitTime: '22 min',
      aiTriage: 'RLL Segmental PE Present',
      badgeClass: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30'
    },
    {
      acc: 'ACC-88322',
      patient: 'ANON-63110',
      modality: 'MR',
      exam: 'MRI BRAIN W/ & W/O CONTRAST',
      urgency: 'ROUTINE',
      waitTime: '45 min',
      aiTriage: 'No acute intracranial pathology',
      badgeClass: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30'
    }
  ];

  const filteredItems = filter === 'ALL' ? worklistItems : worklistItems.filter(i => i.urgency === filter);

  return (
    <section className="py-20 bg-slate-50/70 dark:bg-navy-950/70 border-y border-slate-200 dark:border-navy-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-600 dark:text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider">
            <ListFilter className="w-3.5 h-3.5" />
            Smart Worklist & Structured Reporting
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-navy-900 dark:text-white tracking-tight">
            Dynamic Priority Queues & Automated EHR Drafts
          </h2>
          <p className="text-slate-600 dark:text-slate-300 text-base">
            Replace static chronological worklists with real-time acuity prioritization. Generate pre-drafted structured reports formatted to HL7 FHIR R4 standards ready for instantaneous one-click clinician approval.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Column: Prioritized Worklist Feed */}
          <div className="lg:col-span-6 bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-navy-800 shadow-medical-card dark:shadow-medical-card-dark">
            
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-200 dark:border-navy-800">
              <div>
                <h3 className="font-bold text-navy-900 dark:text-white text-base">Dynamic Clinical Queue</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">Sorted by Clinical Acuity & Waiting Time</p>
              </div>

              {/* Filter pills */}
              <div className="flex gap-1 bg-slate-100 dark:bg-navy-950 p-1 rounded-lg text-xs font-mono">
                {(['ALL', 'STAT', 'URGENT'] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setFilter(tab)}
                    className={`px-2.5 py-1 rounded-md transition ${
                      filter === tab
                        ? 'bg-teal-500 text-white font-bold'
                        : 'text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              {filteredItems.map(item => (
                <div
                  key={item.acc}
                  className="p-3.5 rounded-xl border border-slate-200 dark:border-navy-800 bg-slate-50/50 dark:bg-navy-850/60 hover:border-teal-500 transition-all flex items-center justify-between text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] border ${item.badgeClass}`}>
                        {item.urgency}
                      </span>
                      <span className="font-mono text-slate-500 dark:text-slate-400">{item.acc}</span>
                      <span className="font-bold text-navy-900 dark:text-white">{item.modality}</span>
                    </div>
                    <p className="font-semibold text-navy-800 dark:text-slate-200">{item.exam}</p>
                    <p className="text-[11px] text-teal-600 dark:text-cyan-400 font-mono">AI: {item.aiTriage}</p>
                  </div>
                  <div className="text-right font-mono">
                    <div className="flex items-center gap-1 text-slate-500 dark:text-slate-400 text-[11px]">
                      <Clock className="w-3 h-3" />
                      <span>{item.waitTime}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

          </div>

          {/* Right Column: Automated Structured Reporting & Attestation */}
          <div className="lg:col-span-6 bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-navy-800 shadow-medical-card dark:shadow-medical-card-dark space-y-5">
            
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-navy-800">
              <div>
                <span className="text-[10px] uppercase font-mono font-bold text-teal-600 dark:text-cyan-400">
                  HL7 FHIR R4 Synchronizer
                </span>
                <h3 className="font-bold text-navy-900 dark:text-white text-base">
                  Pre-Drafted Structured Diagnostic Report
                </h3>
              </div>
              <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                NeMo Checked
              </span>
            </div>

            {/* Structured Report Preview */}
            <div className="bg-slate-50 dark:bg-navy-950 p-4 rounded-xl border border-slate-200 dark:border-navy-800 font-mono text-xs space-y-3">
              <div>
                <span className="text-slate-500 dark:text-slate-400 block text-[11px]">CLINICAL INDICATION:</span>
                <p className="text-navy-900 dark:text-slate-200">Acute trauma, altered mental status, GCS 11.</p>
              </div>

              <div>
                <span className="text-slate-500 dark:text-slate-400 block text-[11px]">FINDINGS (AGENT SYNTHESIS):</span>
                <p className="text-navy-900 dark:text-slate-200 leading-relaxed">
                  There is a 3.4 x 2.2 cm acute hyperdense hematoma centered in the right basal ganglia and internal capsule. Local mass effect effaces the right lateral ventricle with 4.2 mm right-to-left midline shift. No herniation.
                </p>
              </div>

              <div>
                <span className="text-slate-500 dark:text-slate-400 block text-[11px]">IMPRESSION (ACR CRITERIA ALIGNED):</span>
                <p className="text-rose-600 dark:text-rose-400 font-semibold">
                  1. Acute right basal ganglia intracerebral hemorrhage with subfalcine mass effect.
                  <br />
                  2. STAT clinical notification recommended for emergent neurosurgical consultation.
                </p>
              </div>
            </div>

            {/* Attestation & Action Bar */}
            <div className="p-4 rounded-xl bg-teal-500/5 dark:bg-teal-500/10 border border-teal-500/20 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600 dark:text-slate-300 font-sans">
                  Clinician-in-the-Loop Sign-Off Status:
                </span>
                <span className={`font-mono font-bold ${
                  signedOff ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'
                }`}>
                  {signedOff ? '✓ E-SIGNED & COMMITTED TO PACS' : '● PENDING RADIOLOGIST ATTESTATION'}
                </span>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setSignedOff(!signedOff)}
                  className={`flex-1 py-2.5 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                    signedOff
                      ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                      : 'bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-white shadow-glow-teal'
                  }`}
                >
                  <FileCheck className="w-4 h-4" />
                  {signedOff ? 'Attested & Broadcast to EHR' : 'Approve Draft & Sign to PACS'}
                </button>
                <button
                  onClick={onRequestDemo}
                  className="px-4 py-2.5 rounded-lg text-xs font-semibold border border-slate-300 dark:border-navy-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-navy-800 transition"
                >
                  Edit in Studio
                </button>
              </div>
            </div>

          </div>

        </div>

      </div>
    </section>
  );
};
