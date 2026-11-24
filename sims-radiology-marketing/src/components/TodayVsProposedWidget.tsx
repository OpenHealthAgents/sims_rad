import React, { useState } from 'react';
import { 
  AlertCircle, 
  CheckCircle2, 
  XCircle, 
  Sparkles, 
  ArrowRight, 
  Bot, 
  Layers, 
  PhoneCall, 
  FileSearch, 
  ListOrdered, 
  FileText, 
  BellRing,
  Cpu
} from 'lucide-react';

interface TodayVsProposedWidgetProps {
  onScheduleDemo?: () => void;
}

export const TodayVsProposedWidget: React.FC<TodayVsProposedWidgetProps> = ({ onScheduleDemo }) => {
  // Mobile active tab toggle
  const [mobileTab, setMobileTab] = useState<'today' | 'proposed'>('proposed');
  const [activeStep, setActiveStep] = useState<number | null>(null);

  const workflowSteps = [
    {
      step: '01. Detection & AI Tools',
      today: {
        title: 'Point Solution AI Detectors',
        icon: XCircle,
        desc: 'Siloed, single-finding black boxes in disconnected windows. Radiologist must manually reconcile conflicting alerts.',
        tag: 'Fragmented Silos'
      },
      proposed: {
        title: 'AI Case Concierge Pre-Read',
        icon: CheckCircle2,
        desc: 'Autonomous multi-agent synthesis across CT, MRI, and X-ray. Pre-calculates measurements and lesion heatmaps before study opens.',
        tag: 'Multi-Agent Choreography'
      }
    },
    {
      step: '02. Clinical Context Gathering',
      today: {
        title: 'Manual DICOM / EHR Lookup',
        icon: XCircle,
        desc: 'Clicking back and forth across 4+ disparate screens (PACS, RIS, Epic/Cerner EHR, historical PDFs) to assemble patient history.',
        tag: '3.5 min/study lost'
      },
      proposed: {
        title: 'Unified Multi-Modality Context',
        icon: CheckCircle2,
        desc: 'Instant longitudinal correlation: prior studies, clinical lab values, and surgical notes automatically summarized into concise clinical dossier.',
        tag: 'Instant Ingest Synthesis'
      }
    },
    {
      step: '03. Worklist & Prioritization',
      today: {
        title: 'Fragmented Chronological Queues',
        icon: XCircle,
        desc: 'First-in, first-out worklists. Life-threatening intracranial hemorrhages sit behind non-urgent routine outpatients.',
        tag: 'STAT Delays (75m+)'
      },
      proposed: {
        title: 'Dynamic Acuity Worklist',
        icon: CheckCircle2,
        desc: 'Sub-minute autonomous triage. Emergent pathology is elevated to top-of-list within 42 seconds of PACS C-STORE transmission.',
        tag: '< 45s Triage Latency'
      }
    },
    {
      step: '04. Reporting & Communication',
      today: {
        title: 'Manual Calls & Blank Dictations',
        icon: XCircle,
        desc: 'Typing or dictating routine boilerplate from scratch; interrupted reading room phone tag to alert ED teams of critical findings.',
        tag: 'Clinician Burnout'
      },
      proposed: {
        title: 'Voice-Assisted Structured Drafts & Auto-Escalation',
        icon: CheckCircle2,
        desc: 'Pre-populated structured report with ACR-compliant impressions. 1-click radiologist sign-off triggers closed-loop EHR notification.',
        tag: '100% Sign-off Authority'
      }
    }
  ];

  return (
    <div className="w-full">
      
      {/* Widget Header & Mobile Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse"></span>
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-teal-600 dark:text-cyan-400">
              Interactive Workflow Architecture Comparison
            </span>
          </div>
          <h3 className="text-2xl font-extrabold text-navy-900 dark:text-white mt-1">
            Today vs. SIMS Agentic Operating Model
          </h3>
        </div>

        {/* Mobile Tab Pills (< md breakpoint) */}
        <div className="flex md:hidden p-1 rounded-xl bg-slate-100 dark:bg-navy-900 border border-slate-200 dark:border-navy-800 text-xs font-semibold">
          <button
            onClick={() => setMobileTab('today')}
            className={`flex-1 py-2 px-3 rounded-lg transition ${
              mobileTab === 'today'
                ? 'bg-rose-500 text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            Today: Fragmented
          </button>
          <button
            onClick={() => setMobileTab('proposed')}
            className={`flex-1 py-2 px-3 rounded-lg transition ${
              mobileTab === 'proposed'
                ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white shadow-glow-teal'
                : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            SIMS Agentic Platform
          </button>
        </div>
      </div>

      {/* Main Comparison Container */}
      <div className="bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-navy-800 shadow-medical-card dark:shadow-medical-card-dark overflow-hidden">
        
        {/* Desktop Comparison Table Header */}
        <div className="hidden md:grid md:grid-cols-2 border-b border-slate-200 dark:border-navy-800">
          <div className="p-6 bg-rose-500/5 dark:bg-rose-950/20 border-r border-slate-200 dark:border-navy-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-500 flex items-center justify-center font-bold">
                  ✕
                </div>
                <div>
                  <h4 className="font-bold text-navy-900 dark:text-white text-base">
                    Today: Fragmented Point Solutions
                  </h4>
                  <p className="text-xs text-rose-600 dark:text-rose-400 font-mono">Disjointed Tools & Cognitive Overhead</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded text-[11px] font-mono bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                Legacy Model
              </span>
            </div>
          </div>

          <div className="p-6 bg-teal-500/5 dark:bg-teal-950/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-teal-500/10 text-teal-600 dark:text-cyan-400 flex items-center justify-center font-bold shadow-glow-teal">
                  ✓
                </div>
                <div>
                  <h4 className="font-bold text-navy-900 dark:text-white text-base">
                    SIMS Agentic Operating Platform
                  </h4>
                  <p className="text-xs text-teal-600 dark:text-cyan-400 font-mono">Autonomous Orchestration + Radiologist Authority</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded text-[11px] font-mono bg-teal-500/10 text-teal-600 dark:text-cyan-300 border border-teal-500/30">
                Agentic 2.0
              </span>
            </div>
          </div>
        </div>

        {/* Step-by-Step Rows */}
        <div className="divide-y divide-slate-200 dark:divide-navy-800">
          {workflowSteps.map((item, idx) => {
            const isHovered = activeStep === idx;
            return (
              <div 
                key={idx}
                onMouseEnter={() => setActiveStep(idx)}
                onMouseLeave={() => setActiveStep(null)}
                className={`transition-colors duration-150 ${
                  isHovered ? 'bg-slate-50/80 dark:bg-navy-850/40' : ''
                }`}
              >
                
                {/* Step Marker Badge */}
                <div className="px-6 pt-4 pb-1">
                  <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-slate-400 dark:text-slate-500">
                    {item.step}
                  </span>
                </div>

                {/* Grid Split */}
                <div className="grid grid-cols-1 md:grid-cols-2">
                  
                  {/* Left (Today) - Always on desktop, conditionally on mobile */}
                  <div className={`p-6 md:border-r border-slate-200 dark:border-navy-800 space-y-3 ${
                    mobileTab === 'today' ? 'block' : 'hidden md:block'
                  }`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <XCircle className="w-4 h-4 text-rose-500 shrink-0" />
                        <h5 className="font-bold text-sm text-navy-900 dark:text-white">
                          {item.today.title}
                        </h5>
                      </div>
                      <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 shrink-0">
                        {item.today.tag}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed pl-6">
                      {item.today.desc}
                    </p>
                  </div>

                  {/* Right (SIMS Proposed) - Always on desktop, conditionally on mobile */}
                  <div className={`p-6 space-y-3 bg-teal-500/[0.02] dark:bg-teal-500/[0.03] ${
                    mobileTab === 'proposed' ? 'block' : 'hidden md:block'
                  }`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-teal-500 shrink-0" />
                        <h5 className="font-bold text-sm text-navy-900 dark:text-white">
                          {item.proposed.title}
                        </h5>
                      </div>
                      <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-teal-500/10 text-teal-600 dark:text-cyan-300 border border-teal-500/20 shrink-0">
                        {item.proposed.tag}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed pl-6">
                      {item.proposed.desc}
                    </p>
                  </div>

                </div>

              </div>
            );
          })}
        </div>

        {/* Bottom Banner Summary inside widget */}
        <div className="p-6 bg-slate-50 dark:bg-navy-950 border-t border-slate-200 dark:border-navy-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-teal-500/10 text-teal-600 dark:text-cyan-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-bold text-navy-900 dark:text-white">
                Human-in-the-Loop Safeguard Standard
              </p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Zero clinical reports are submitted to EHR without explicit, credentialed radiologist sign-off.
              </p>
            </div>
          </div>

          {onScheduleDemo && (
            <button
              onClick={onScheduleDemo}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold text-white bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 shadow-glow-teal transition shrink-0"
            >
              <span>See Live Interactive Comparison</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

      </div>

    </div>
  );
};

export default TodayVsProposedWidget;
