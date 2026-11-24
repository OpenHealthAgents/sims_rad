import React, { useState } from 'react';
import { 
  BellRing, 
  Clock, 
  CheckCheck, 
  AlertOctagon, 
  ArrowRight, 
  UserCheck, 
  PhoneCall, 
  ShieldCheck, 
  SendHorizontal,
  Flame,
  CheckCircle2
} from 'lucide-react';

export const TaskOrchestratorDemo: React.FC = () => {
  const [activeStep, setActiveStep] = useState<number>(2); // Default to live escalation stage
  const [acknowledged, setAcknowledged] = useState<boolean>(false);

  const steps = [
    {
      id: 1,
      title: 'Finding Detection & Flag',
      subtitle: 'NeMo Guardrail Verified',
      desc: 'Radiologist confirms STAT acute finding (ICH 3.4cm). Platform tags priority level: Category 1 Red Alert.',
      actor: 'Radiologist Sign-Off',
      time: 'T + 00s',
      status: 'complete'
    },
    {
      id: 2,
      title: 'Automated Recipient Routing',
      subtitle: 'Dynamic On-Call Registry',
      desc: 'System queries hospital roster for active ED Attending (Dr. Henderson) & On-Call Neurosurgeon (Dr. Alvarez).',
      actor: 'SIMS Orchestrator',
      time: 'T + 04s',
      status: 'complete'
    },
    {
      id: 3,
      title: 'Closed-Loop Escalation Timer',
      subtitle: '15-Minute Countdown Active',
      desc: 'Direct push alert delivered via hospital secure VoIP/paging. Escalates to backup attending if unread in 5 mins.',
      actor: 'Clinical Alert Gate',
      time: 'T + 12s',
      status: acknowledged ? 'complete' : 'active'
    },
    {
      id: 4,
      title: 'Receipt & Legal EHR Log',
      subtitle: 'Audit Compliance Stamp',
      desc: 'Recipient digital acknowledgement or voice read-back recorded into EHR legal audit log with biometric timestamp.',
      actor: 'EHR Writeback',
      time: 'T + 48s',
      status: acknowledged ? 'complete' : 'pending'
    }
  ];

  return (
    <div className="space-y-6">
      
      {/* Module Overview Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-teal-500/5 dark:bg-navy-850/60 border border-teal-500/20">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-teal-500/10 text-teal-600 dark:text-cyan-400">
              <BellRing className="w-4 h-4" />
            </span>
            <span className="font-bold text-sm text-navy-900 dark:text-white">
              Critical Results & Follow-Up Orchestrator
            </span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Automates the closed-loop communication of critical findings to treating physicians, eliminating telephone tag and ensuring 100% regulatory audit compliance.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/30">
            Category 1: Red Alert SLA
          </span>
        </div>
      </div>

      {/* Main Orchestration Flow Box */}
      <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 p-6 shadow-medical-card dark:shadow-medical-card-dark space-y-8">
        
        {/* Interactive Step Timeline (Flow Diagram) */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
          {steps.map((st, i) => {
            const isCurrent = activeStep === st.id;
            const isDone = st.status === 'complete';

            return (
              <div 
                key={st.id}
                onClick={() => setActiveStep(st.id)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  isCurrent
                    ? 'bg-teal-500/10 dark:bg-navy-850 border-teal-500 shadow-glow-teal'
                    : isDone
                      ? 'bg-slate-50 dark:bg-navy-950 border-emerald-500/30'
                      : 'bg-slate-50 dark:bg-navy-950/40 border-slate-200 dark:border-navy-800 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold text-slate-400">
                    STAGE 0{st.id}
                  </span>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                    isDone 
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' 
                      : 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
                  }`}>
                    {st.time}
                  </span>
                </div>

                <h4 className="font-bold text-sm text-navy-900 dark:text-white mb-1">
                  {st.title}
                </h4>
                <p className="text-[11px] text-teal-600 dark:text-cyan-400 font-mono mb-2">
                  {st.subtitle}
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  {st.desc}
                </p>
              </div>
            );
          })}
        </div>

        {/* Live Closed-Loop Communication Simulator Card */}
        <div className="p-6 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            
            {/* Alert Notification Payload */}
            <div className="lg:col-span-8 space-y-4">
              <div className="flex items-center gap-2 text-rose-500 font-bold text-sm">
                <AlertOctagon className="w-5 h-5 animate-bounce" />
                <span>ACTIVE CRITICAL ALERT: Intracranial Hemorrhage (ACC-77291)</span>
              </div>

              <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 text-xs font-mono space-y-2">
                <div className="flex justify-between text-slate-400 text-[11px] border-b border-slate-100 dark:border-navy-800 pb-2">
                  <span>DISPATCHED TO: Dr. Henderson, MD (ED Resus Attending)</span>
                  <span>ESCALATION TARGET: Dr. Alvarez (Neurosurgery)</span>
                </div>
                <p className="text-navy-900 dark:text-slate-200">
                  "Critical finding on Head CT: Acute right basal ganglia ICH with 4.2mm midline shift. Immediate clinical intervention required."
                </p>
                <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-[11px]">
                  <CheckCheck className="w-4 h-4" />
                  <span>Push delivered to Voicera / Epic Rover Handset at 17:14:12</span>
                </div>
              </div>

              {/* Status Notice */}
              <div className="flex items-center gap-2 text-xs">
                <span className="font-semibold text-slate-600 dark:text-slate-300">Closed-Loop Status:</span>
                <span className={`font-mono font-bold px-2 py-0.5 rounded text-[11px] ${
                  acknowledged 
                    ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30' 
                    : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30'
                }`}>
                  {acknowledged ? '✓ POSITIVE RECEIPT ACKNOWLEDGED' : '⏱ ESCALATION TIMER: 03:48 REMAINING'}
                </span>
              </div>
            </div>

            {/* Action Simulator Button */}
            <div className="lg:col-span-4 text-center lg:text-right space-y-3">
              <button
                onClick={() => setAcknowledged(!acknowledged)}
                className={`w-full py-4 rounded-xl text-xs font-bold transition flex items-center justify-center gap-2 shadow-sm ${
                  acknowledged
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                    : 'bg-gradient-to-r from-rose-500 to-amber-500 hover:from-rose-400 hover:to-amber-400 text-white'
                }`}
              >
                <CheckCircle2 className="w-4 h-4" />
                {acknowledged ? 'Acknowledged & Logged to EHR' : 'Simulate Recipient Read-Back Receipt'}
              </button>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                Complies with Joint Commission National Patient Safety Goals (NPSG.02.03.01)
              </p>
            </div>

          </div>
        </div>

      </div>

    </div>
  );
};

export default TaskOrchestratorDemo;
