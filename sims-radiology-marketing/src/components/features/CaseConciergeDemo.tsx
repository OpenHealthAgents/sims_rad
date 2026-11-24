import React, { useState } from 'react';
import { 
  Bot, 
  FileText, 
  Sparkles, 
  Layers, 
  Calendar, 
  Activity, 
  CheckCircle2, 
  ArrowRight,
  Database,
  FlaskConical,
  ClipboardList
} from 'lucide-react';

export const CaseConciergeDemo: React.FC = () => {
  const [viewMode, setViewMode] = useState<'ai' | 'raw'>('ai');

  return (
    <div className="space-y-6">
      
      {/* Module Overview Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-teal-500/5 dark:bg-navy-850/60 border border-teal-500/20">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-teal-500/10 text-teal-600 dark:text-cyan-400">
              <Bot className="w-4 h-4" />
            </span>
            <span className="font-bold text-sm text-navy-900 dark:text-white">
              AI Case Concierge: Pre-Read Intelligence
            </span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Automatically parses EHR clinical notes, past surgery histories, relevant lab trends, and prior imaging series before the study slice viewer opens.
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-1 bg-slate-200/80 dark:bg-navy-950 p-1 rounded-xl text-xs font-semibold self-start sm:self-auto shrink-0">
          <button
            onClick={() => setViewMode('raw')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              viewMode === 'raw'
                ? 'bg-white dark:bg-navy-800 text-navy-900 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white'
            }`}
          >
            Raw EHR Text
          </button>
          <button
            onClick={() => setViewMode('ai')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
              viewMode === 'ai'
                ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white font-bold shadow-glow-teal'
                : 'text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            AI Pre-Read Briefing
          </button>
        </div>
      </div>

      {/* Main Comparative Card */}
      <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 p-6 shadow-medical-card dark:shadow-medical-card-dark transition-all">
        
        {viewMode === 'ai' ? (
          /* AI-Generated Pre-Read Briefing */
          <div className="space-y-6">
            
            {/* Header info strip */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-200 dark:border-navy-800">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-teal-500/10 text-teal-600 dark:text-cyan-400 flex items-center justify-center font-mono font-bold text-sm">
                  CT
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-navy-900 dark:text-white text-sm">
                      ANON-90421 • Head CT Non-Contrast (STAT)
                    </h4>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                      Emergency Acuity 1
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                    Accession: ACC-77291 • Order Ref: ED-TRAUMA-04
                  </p>
                </div>
              </div>

              <div className="text-right">
                <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded border border-emerald-500/30 font-semibold">
                  ✓ 4 Data Sources Synthesized in 1.4s
                </span>
              </div>
            </div>

            {/* 4 Multi-Source Aggregated Blocks */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* 1. Referral Question & Clinical Indication */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 space-y-2">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-teal-600 dark:text-cyan-400">
                  <ClipboardList className="w-3.5 h-3.5" />
                  <span>Referral Question & Indication</span>
                </div>
                <p className="text-xs text-navy-900 dark:text-slate-200 leading-relaxed">
                  <strong>Indication:</strong> 72M with sudden onset right-sided hemiplegia, expressive aphasia, and sudden loss of consciousness (GCS 10). Last known well: 55 mins prior.
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">
                  <strong>Core Question:</strong> Rule out acute intracranial hemorrhage (ICH) vs. large vessel occlusion (LVO) prior to IV thrombolytic administration.
                </p>
              </div>

              {/* 2. Critical Lab Results */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 space-y-2">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-amber-600 dark:text-amber-400">
                  <FlaskConical className="w-3.5 h-3.5" />
                  <span>Point-of-Care Lab Results</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                  <div className="p-2 rounded bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800">
                    <span className="text-[10px] text-slate-400 block">INR / PT</span>
                    <span className="font-bold text-rose-500">2.8 (High)</span>
                  </div>
                  <div className="p-2 rounded bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800">
                    <span className="text-[10px] text-slate-400 block">Platelets</span>
                    <span className="font-bold text-emerald-500">210k (Normal)</span>
                  </div>
                  <div className="p-2 rounded bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800">
                    <span className="text-[10px] text-slate-400 block">eGFR / Cr</span>
                    <span className="font-bold text-slate-700 dark:text-slate-300">68 mL/min</span>
                  </div>
                </div>
                <p className="text-[11px] text-rose-600 dark:text-rose-400 font-mono">
                  ⚠ Patient on Warfarin therapy. High bleeding risk alert attached to worklist.
                </p>
              </div>

              {/* 3. Prior Comparison Studies */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 space-y-2">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-teal-600 dark:text-cyan-400">
                  <Layers className="w-3.5 h-3.5" />
                  <span>Prior Longitudinal Comparison</span>
                </div>
                <ul className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300 font-mono">
                  <li className="flex items-center justify-between">
                    <span>• MRI Brain (14 months ago):</span>
                    <span className="text-slate-400">Mild chronic microvascular disease</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>• CT Head (3 years ago):</span>
                    <span className="text-slate-400">Normal, no prior hemorrhage</span>
                  </li>
                </ul>
                <div className="text-[11px] text-emerald-600 dark:text-emerald-400">
                  ✓ Prior series automatically pre-loaded on viewport #2 for 1-click comparison.
                </div>
              </div>

              {/* 4. Agent Synthesized Pre-Read Impression */}
              <div className="p-4 rounded-xl bg-teal-500/5 dark:bg-teal-950/30 border border-teal-500/30 space-y-2">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-teal-600 dark:text-cyan-400">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Case Concierge Pre-Read Finding</span>
                </div>
                <p className="text-xs font-semibold text-rose-600 dark:text-rose-400">
                  Suspected Acute Left Basal Ganglia Hemorrhage (Est. 28cc) with 3.8mm midline shift.
                </p>
                <p className="text-[11px] text-slate-600 dark:text-slate-300">
                  NeMo Guardrail check: High confidence detection (98.2%). Key slices #22-26 tagged with SHAP attribution heatmaps.
                </p>
              </div>

            </div>

          </div>
        ) : (
          /* Raw Unstructured EHR Record (The Old Frustrating Way) */
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-navy-800">
              <span className="text-xs font-mono text-rose-500 font-bold">
                Legacy Hospital EHR Raw Dump (Epic / Cerner HL7 Feed)
              </span>
              <span className="text-xs text-slate-400 font-mono">4,120 words of unstructured text</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-100 dark:bg-navy-950 font-mono text-xs text-slate-600 dark:text-slate-400 space-y-2 max-h-72 overflow-y-auto leading-relaxed border border-slate-200 dark:border-navy-800">
              <p>*** HOSPITAL INPATIENT CLINICAL ADMISSION NOTE ***</p>
              <p>PATIENT: [REDACTED] DOB: 04/12/1954 MRN: 9021893 ATTENDING: DR. HENDERSON, MD</p>
              <p>HISTORY OF PRESENT ILLNESS: Patient is a 72-year-old male presenting with altered mental state and right side weakness noted around 16:30 today by spouse. History of hypertension, AFib, hyperlipidemia. Taking Metoprolol, Atorvastatin, Coumadin (Warfarin 5mg daily). Last clinic visit INR recorded 2.8 on 11/12/26. Non-compliant with BP medications periodically...</p>
              <p>PAST SURGICAL HISTORY: Appendectomy (1982), Right Knee Arthroscopy (2014), Cholecystectomy (2018)...</p>
              <p>PHYSICAL EXAM: Vitals: BP 184/102, HR 88 irregular, RR 18, SpO2 96% on RA. Neuro: Right hemiparesis 2/5, expressive dysphasia, pupil equal and reactive, GCS 10 (E3V2M5)...</p>
              <p>LABS ORDERED: CBC, CMP, PT/INR, PTT, Troponin, UA, Type and Screen. STAT CT Head w/o contrast and CTA head/neck requested to rule out bleed before tPA...</p>
              <p>[... 32 additional pages of nursing flowcharts, billing codes, and pharmacy refill logs ...]</p>
            </div>
            
            <p className="text-xs text-slate-500 dark:text-slate-400 italic">
              Without SIMS, radiologists spend an average of 3 to 5 minutes scrolling through disparate tabs to piece together medication alerts like Warfarin INR 2.8.
            </p>
          </div>
        )}

      </div>

    </div>
  );
};

export default CaseConciergeDemo;
