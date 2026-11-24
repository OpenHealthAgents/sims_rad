import React, { useState } from 'react';
import { 
  Mic, 
  FileCheck, 
  History, 
  Lock, 
  Sparkles, 
  CheckCircle2, 
  RotateCcw, 
  Send, 
  ShieldAlert, 
  Edit3, 
  Volume2 
} from 'lucide-react';

export const ReportingDemo: React.FC = () => {
  const [activeVoicePrompt, setActiveVoicePrompt] = useState<string | null>(null);
  const [impressionText, setImpressionText] = useState(
    '1. Acute 3.4 x 2.2 cm intracerebral hemorrhage in the right basal ganglia and internal capsule with 4.2 mm right-to-left subfalcine midline shift.\n2. Surrounding vasogenic edema exerting regional mass effect on the right lateral ventricle.\n3. STAT communication logged with ED Attending Dr. Henderson at 17:14.'
  );
  const [isSigned, setIsSigned] = useState(false);
  const [activeHistoryTab, setActiveHistoryTab] = useState<'current' | 'history'>('current');

  const voiceCommands = [
    {
      label: '"Add comparison with prior CT"',
      action: () => {
        setActiveVoicePrompt('"Add comparison with prior CT"');
        setImpressionText(prev => prev + '\n4. Compared to prior CT (14 months ago), this represents a new acute hemorrhagic event without prior parenchymal insult.');
      }
    },
    {
      label: '"Change impression to stable ICH without active expansion"',
      action: () => {
        setActiveVoicePrompt('"Change impression to stable ICH without active expansion"');
        setImpressionText('1. Right basal ganglia intracerebral hemorrhage appears stable in volume without evidence of active contrast extravasation (spot sign negative).\n2. Mass effect and 4.2 mm midline shift unchanged from initial scan.');
      }
    },
    {
      label: '"Insert ACR critical result escalation template"',
      action: () => {
        setActiveVoicePrompt('"Insert ACR critical result escalation template"');
        setImpressionText(prev => prev + '\n\n[CRITICAL FINDING COMMUNICATION]:\nCommunicated verbally to Dr. Henderson (ED Attending) via secure hospital closed-loop interface. Read-back verified.');
      }
    }
  ];

  const resetReport = () => {
    setActiveVoicePrompt(null);
    setIsSigned(false);
    setImpressionText(
      '1. Acute 3.4 x 2.2 cm intracerebral hemorrhage in the right basal ganglia and internal capsule with 4.2 mm right-to-left subfalcine midline shift.\n2. Surrounding vasogenic edema exerting regional mass effect on the right lateral ventricle.\n3. STAT communication logged with ED Attending Dr. Henderson at 17:14.'
    );
  };

  return (
    <div className="space-y-6">
      
      {/* Module Overview Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-teal-500/5 dark:bg-navy-850/60 border border-teal-500/20">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-teal-500/10 text-teal-600 dark:text-cyan-400">
              <Mic className="w-4 h-4" />
            </span>
            <span className="font-bold text-sm text-navy-900 dark:text-white">
              Structured Reporting & Intelligent Voice Layer
            </span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            AI prepares structured findings pre-aligned with ACR templates. Radiologists edit via natural voice or keyboard with immutable audit versioning and final sign-off authority.
          </p>
        </div>

        {/* Mode Switcher */}
        <div className="flex items-center gap-1 bg-slate-200/80 dark:bg-navy-950 p-1 rounded-xl text-xs font-semibold self-start sm:self-auto">
          <button
            onClick={() => setActiveHistoryTab('current')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeHistoryTab === 'current'
                ? 'bg-white dark:bg-navy-800 text-navy-900 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            Live Editor & Voice
          </button>
          <button
            onClick={() => setActiveHistoryTab('history')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeHistoryTab === 'history'
                ? 'bg-white dark:bg-navy-800 text-navy-900 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            Immutable Version Trail
          </button>
        </div>
      </div>

      {/* Main Interactive Editor Workspace */}
      <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 p-6 shadow-medical-card dark:shadow-medical-card-dark space-y-6">
        
        {activeHistoryTab === 'current' ? (
          <>
            {/* Voice Command Simulation Ribbon */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-teal-600 dark:text-cyan-400 flex items-center gap-1.5">
                  <Volume2 className="w-4 h-4 text-teal-500 animate-pulse" />
                  Try Voice Command Interactivity:
                </span>
                {activeVoicePrompt && (
                  <button 
                    onClick={resetReport}
                    className="text-[11px] font-mono text-slate-400 hover:text-navy-900 dark:hover:text-white flex items-center gap-1"
                  >
                    <RotateCcw className="w-3 h-3" /> Reset
                  </button>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                {voiceCommands.map((cmd, idx) => (
                  <button
                    key={idx}
                    onClick={cmd.action}
                    className="px-3 py-1.5 rounded-lg text-xs font-mono bg-white dark:bg-navy-900 border border-slate-300 dark:border-navy-700 hover:border-teal-500 text-navy-800 dark:text-slate-200 hover:text-teal-600 dark:hover:text-cyan-300 transition shadow-sm active:scale-95"
                  >
                    🎤 {cmd.label}
                  </button>
                ))}
              </div>

              {activeVoicePrompt && (
                <div className="p-2.5 rounded-lg bg-teal-500/10 border border-teal-500/30 text-xs font-mono text-teal-700 dark:text-cyan-300 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-teal-500 shrink-0" />
                  <span>Voice Prompt Executed: <strong>{activeVoicePrompt}</strong></span>
                </div>
              )}
            </div>

            {/* Structured Report Preview */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
              
              {/* Findings Section (8 cols) */}
              <div className="md:col-span-8 space-y-4">
                
                {/* Findings block */}
                <div className="space-y-1.5">
                  <span className="text-[11px] font-mono font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                    Structured Findings (AI-Assisted Pre-Draft):
                  </span>
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 text-xs text-navy-900 dark:text-slate-200 font-mono leading-relaxed space-y-2">
                    <p><strong>BRAIN PARENCHYMA:</strong> Acute hyperdense hematoma measuring 3.4 x 2.2 cm within the right basal ganglia and posterior limb of the internal capsule. Surrounding hypoattenuation is consistent with early vasogenic edema.</p>
                    <p><strong>VENTRICLES & CISTERNS:</strong> Partial effacement of the frontal horn and body of the right lateral ventricle. 4.2 mm of right-to-left subfalcine herniation is identified. Basal cisterns remain patent without uncal herniation.</p>
                    <p><strong>EXTRA-AXIAL SPACES:</strong> No subdural, epidural, or subarachnoid hemorrhage.</p>
                    <p><strong>CALVARIUM & ORBITS:</strong> No acute fractures or osseous lesions.</p>
                  </div>
                </div>

                {/* Impression editable textarea */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                      Diagnostic Impression (Radiologist Dictation / Voice Editable):
                    </span>
                    <span className="text-[10px] text-teal-600 dark:text-cyan-400 font-mono">
                      ACR Appropriateness Guided
                    </span>
                  </div>
                  <textarea
                    rows={4}
                    value={impressionText}
                    onChange={(e) => setImpressionText(e.target.value)}
                    disabled={isSigned}
                    className={`w-full p-4 rounded-xl font-mono text-xs border leading-relaxed focus:outline-none transition ${
                      isSigned
                        ? 'bg-slate-100 dark:bg-navy-950 text-slate-500 border-slate-200 dark:border-navy-800'
                        : 'bg-white dark:bg-navy-950 text-navy-900 dark:text-slate-200 border-teal-500/40 focus:border-teal-500'
                    }`}
                  />
                </div>

              </div>

              {/* Attestation & Approval Barrier (4 cols) */}
              <div className="md:col-span-4 space-y-4">
                
                {/* Authorization Barrier Callout */}
                <div className="p-4 rounded-xl bg-teal-500/5 dark:bg-teal-500/10 border border-teal-500/30 space-y-3">
                  <div className="flex items-center gap-2">
                    <Lock className="w-4 h-4 text-teal-600 dark:text-cyan-400" />
                    <h5 className="font-bold text-xs text-navy-900 dark:text-white">
                      Strict Sign-Off Barrier
                    </h5>
                  </div>
                  <p className="text-[11px] text-slate-600 dark:text-slate-300 leading-relaxed">
                    0% unvalidated writeback policy. Even after AI drafting, the report remains in <code>DRAFT_PENDING_REVIEW</code> status until credentialed radiologist biometric or password sign-off.
                  </p>
                  <div className="pt-2 border-t border-teal-500/20 text-[10px] font-mono text-slate-500 dark:text-slate-400">
                    FHIR DiagnosticReport.status = <strong className="text-teal-600 dark:text-cyan-400">{isSigned ? '"final"' : '"preliminary"'}</strong>
                  </div>
                </div>

                {/* Sign-off Action */}
                <div className="space-y-2">
                  <button
                    onClick={() => setIsSigned(!isSigned)}
                    className={`w-full py-3.5 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 ${
                      isSigned
                        ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                        : 'bg-gradient-to-r from-teal-500 via-teal-600 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-white shadow-glow-teal'
                    }`}
                  >
                    <FileCheck className="w-4 h-4" />
                    {isSigned ? '✓ Final Report Committed & Pushed to EHR' : 'Authorize & Sign-Off Report'}
                  </button>

                  <p className="text-center text-[10px] text-slate-400 font-mono">
                    Signed by: Dr. Marcus Vance, MD (ID #RAD-88120)
                  </p>
                </div>

              </div>

            </div>
          </>
        ) : (
          /* Immutable Versioning Trail */
          <div className="space-y-4">
            <h4 className="font-bold text-sm text-navy-900 dark:text-white">
              Immutable Report Audit Trail & Version Tree
            </h4>
            <div className="space-y-3 font-mono text-xs">
              
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-navy-900 dark:text-white">Version 1.0 (Initial AI Pre-Draft)</span>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-slate-200 dark:bg-navy-800 text-slate-600 dark:text-slate-400">Automated</span>
                  </div>
                  <p className="text-slate-500 dark:text-slate-400 text-[11px] mt-1">Generated by LangGraph DeepAgent-Neuro at 17:12:08. SHA-256: 9f82...3e11</p>
                </div>
                <span className="text-slate-400 text-[11px]">17:12</span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-navy-900 dark:text-white">Version 1.1 (Voice Addendum: Prior Comparison)</span>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-teal-500/10 text-teal-600 dark:text-cyan-400">Radiologist Voice</span>
                  </div>
                  <p className="text-slate-500 dark:text-slate-400 text-[11px] mt-1">Dictated by Dr. Marcus Vance, MD at 17:13:42. SHA-256: 7a12...b944</p>
                </div>
                <span className="text-slate-400 text-[11px]">17:13</span>
              </div>

              <div className="p-3.5 rounded-xl bg-emerald-500/5 dark:bg-emerald-950/20 border border-emerald-500/30 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-emerald-700 dark:text-emerald-300">Version 2.0 (FINAL SIGNED & BROADCAST)</span>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-bold">Committed</span>
                  </div>
                  <p className="text-slate-500 dark:text-slate-400 text-[11px] mt-1">Biometric radiologist e-signature verified. Synchronized with Epic EHR via FHIR R4. SHA-256: e441...09ac</p>
                </div>
                <span className="text-emerald-500 text-[11px]">17:14</span>
              </div>

            </div>
          </div>
        )}

      </div>

    </div>
  );
};

export default ReportingDemo;
