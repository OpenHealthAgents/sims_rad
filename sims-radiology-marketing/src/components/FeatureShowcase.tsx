import React, { useState } from 'react';
import { CaseConciergeDemo } from './features/CaseConciergeDemo';
import { WorklistDemo } from './features/WorklistDemo';
import { ReportingDemo } from './features/ReportingDemo';
import { TaskOrchestratorDemo } from './features/TaskOrchestratorDemo';
import { Bot, Layers, Mic, BellRing, Sparkles, ArrowRight } from 'lucide-react';

interface FeatureShowcaseProps {
  onScheduleDemo?: () => void;
}

export const FeatureShowcase: React.FC<FeatureShowcaseProps> = ({ onScheduleDemo }) => {
  const [activeTab, setActiveTab] = useState<'concierge' | 'worklist' | 'reporting' | 'orchestrator'>('concierge');

  const tabs = [
    {
      id: 'concierge',
      label: 'Case Concierge AI',
      icon: Bot,
      tagline: 'Pre-Read EHR & Lab Synthesis'
    },
    {
      id: 'worklist',
      label: 'Unified Multi-Modality Worklist',
      icon: Layers,
      tagline: 'CT, MRI & XR Acuity Prioritization'
    },
    {
      id: 'reporting',
      label: 'Structured Reporting & Voice',
      icon: Mic,
      tagline: 'Voice Dictation & 100% Sign-off Barrier'
    },
    {
      id: 'orchestrator',
      label: 'Critical Results Orchestrator',
      icon: BellRing,
      tagline: 'Closed-Loop Escalation Timers'
    }
  ] as const;

  return (
    <section className="py-20 relative transition-colors" id="feature-showcase">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        
        {/* Showcase Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-600 dark:text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            Interactive Operational Capabilities
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-navy-900 dark:text-white tracking-tight">
            Explore the SIMS Agentic Operating Suite
          </h2>
          <p className="text-base text-slate-600 dark:text-slate-300">
            Click across the four operational modules below to test live interactive previews of our pre-read synthesis, dynamic multi-modality worklist, voice-assisted reporting, and closed-loop escalation orchestrator.
          </p>
        </div>

        {/* 4 Feature Tabs Switcher */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`p-4 rounded-2xl text-left border transition-all duration-200 flex flex-col justify-between ${
                  isActive
                    ? 'bg-white dark:bg-navy-900 border-teal-500 shadow-glow-teal'
                    : 'bg-white/60 dark:bg-navy-900/40 border-slate-200 dark:border-navy-800 hover:border-teal-400/60 shadow-sm'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className={`p-2 rounded-xl transition ${
                    isActive
                      ? 'bg-gradient-to-br from-teal-500 to-cyan-500 text-white shadow-glow-teal'
                      : 'bg-slate-100 dark:bg-navy-850 text-slate-600 dark:text-slate-400'
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  {isActive && (
                    <span className="w-2 h-2 rounded-full bg-teal-500 animate-ping"></span>
                  )}
                </div>

                <div>
                  <h4 className={`text-sm font-bold ${
                    isActive ? 'text-navy-900 dark:text-white' : 'text-slate-700 dark:text-slate-300'
                  }`}>
                    {tab.label}
                  </h4>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono mt-0.5 line-clamp-1">
                    {tab.tagline}
                  </p>
                </div>
              </button>
            );
          })}
        </div>

        {/* Dynamic Feature Module Viewer */}
        <div className="transition-all duration-300">
          {activeTab === 'concierge' && <CaseConciergeDemo />}
          {activeTab === 'worklist' && <WorklistDemo />}
          {activeTab === 'reporting' && <ReportingDemo />}
          {activeTab === 'orchestrator' && <TaskOrchestratorDemo />}
        </div>

        {/* Bottom CTA Bar */}
        {onScheduleDemo && (
          <div className="pt-6 text-center">
            <button
              onClick={onScheduleDemo}
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-teal-500 via-teal-600 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 shadow-glow-teal transition"
            >
              <span>Schedule Live Interactive System Walkthrough</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}

      </div>
    </section>
  );
};

export default FeatureShowcase;
