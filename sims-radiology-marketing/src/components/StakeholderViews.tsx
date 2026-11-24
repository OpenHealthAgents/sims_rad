import React, { useState } from 'react';
import { 
  Building2, 
  Stethoscope, 
  ShieldCheck, 
  Clock, 
  BarChart3, 
  Users, 
  Lock, 
  CheckCircle2, 
  Sparkles, 
  Activity, 
  FileCheck, 
  Layers,
  ArrowRight
} from 'lucide-react';

interface StakeholderViewsProps {
  onScheduleDemo?: () => void;
}

export const StakeholderViews: React.FC<StakeholderViewsProps> = ({ onScheduleDemo }) => {
  const [activeTab, setActiveTab] = useState<'directors' | 'radiologists' | 'security'>('directors');

  const perspectives = [
    {
      id: 'directors',
      title: 'Radiology Directors & Department Chairs',
      shortTitle: 'Directors & Chairs',
      icon: Building2,
      tagline: 'Operational Throughput & SLA Breach Prevention',
      heroQuote: 'Our departmental volume increased 28% without staffing additions. SIMS eliminated worklist bottlenecks and cut our STAT emergency turnaround from 75 minutes to 21 minutes.',
      metrics: [
        { label: 'STAT Turnaround Reduction', value: '-72%' },
        { label: 'SLA Breach Rate', value: '< 0.5%' },
        { label: 'Capacity Multiplier', value: '+1.4x' }
      ],
      keyCapabilities: [
        {
          title: 'Dynamic Workload Balancing',
          desc: 'Intelligently distributes studies across on-shift subspecialists (neuro, body, MSK) based on study complexity and current queue velocity.'
        },
        {
          title: 'SLA Breach Prevention',
          desc: 'Real-time countdown monitors flag studies approaching turnaround limits, auto-escalating priority before hospital SLA breaches occur.'
        },
        {
          title: 'Departmental Operational Visibility',
          desc: 'Executive analytics dashboard tracking modality velocity (CT, MRI, X-ray), radiologist productivity, and emergency response times.'
        },
        {
          title: 'Staff Retention & Burnout Mitigation',
          desc: 'Reclaims ~2 hours daily per radiologist from administrative context-hunting, dramatically reducing shift fatigue and turnover.'
        }
      ]
    },
    {
      id: 'radiologists',
      title: 'Reporting Radiologists & Residents',
      shortTitle: 'Radiologists & Residents',
      icon: Stethoscope,
      tagline: 'Reduced Cognitive Fatigue & Clinical Autonomy',
      heroQuote: 'The AI Case Concierge pre-assembles prior comparison CTs and Warfarin lab values before I even click the study. I dictate via voice and retain 100% sign-off control.',
      metrics: [
        { label: 'Context Assembly Time', value: '-80%' },
        { label: 'Unvalidated Writeback', value: '0.0%' },
        { label: 'Diagnostic Alignment', value: '99.4%' }
      ],
      keyCapabilities: [
        {
          title: 'Reduced Cognitive Fatigue',
          desc: 'No more toggling through 30+ pages of unstructured EHR progress notes. Pertinent surgical histories and contraindications are pre-synthesized.'
        },
        {
          title: 'Automated Pre-Read Briefings',
          desc: 'Lesion measurements, prior study comparisons, and key DICOM slice heatmaps are staged on secondary viewports before review begins.'
        },
        {
          title: 'Voice-Driven Structured Drafting',
          desc: 'Natural voice commands ("Change impression to stable ICH", "Insert ACR template") accelerate dictation without rigid keyboard macro locks.'
        },
        {
          title: 'Complete Clinical Autonomy',
          desc: 'Zero reports are finalized or dispatched without explicit clinician sign-off. AI assists workflow; final diagnosis remains strictly under radiologist authority.'
        }
      ]
    },
    {
      id: 'security',
      title: 'Hospital IT & Security Officers (CISO / CIO)',
      shortTitle: 'IT & Security Officers',
      icon: ShieldCheck,
      tagline: 'On-Premises DMZ Isolation & Zero Egress',
      heroQuote: 'SIMS is one of the rare medical AI platforms we approved in under two weeks. It runs 100% air-gapped on-premises with zero direct cloud DB exposure and full Langfuse audit logs.',
      metrics: [
        { label: 'Cloud Data Egress', value: '0 bytes' },
        { label: 'HIPAA & SOC 2 Conformance', value: '100%' },
        { label: 'Integration Deployment', value: '< 48 hrs' }
      ],
      keyCapabilities: [
        {
          title: 'On-Premises DMZ Isolation',
          desc: 'Deploys directly inside the hospital firewall on local GPU container nodes. Raw DICOM pixels remain in existing PACS storage tiers.'
        },
        {
          title: 'Role-Based Access Controls (RBAC)',
          desc: 'Native integration with hospital Active Directory / LDAP and OAuth 2.0. Enforces granular credentialed authorization per subspecialty.'
        },
        {
          title: 'Zero Direct Cloud DB Exposure',
          desc: 'PostgreSQL 16 and Redis run on encrypted on-premise persistent volumes (AES-256) with zero open outbound database ports.'
        },
        {
          title: 'Langfuse Cryptographic Audit Trails',
          desc: 'Every model inference, prompt check, and radiologist edit is hashed with immutable SHA-256 digests for regulatory compliance.'
        }
      ]
    }
  ] as const;

  const current = perspectives.find(p => p.id === activeTab) || perspectives[0];
  const CurrentIcon = current.icon;

  return (
    <section className="py-20 bg-slate-50/60 dark:bg-navy-950/60 border-y border-slate-200 dark:border-navy-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-teal-600 dark:text-cyan-400 bg-teal-500/10 px-3 py-1 rounded-full border border-teal-500/20">
            Tailored Stakeholder Solutions
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-navy-900 dark:text-white tracking-tight">
            Designed for Departmental Impact, Clinician Autonomy & IT Trust
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Select your role to explore how SIMS transforms clinical operations, reading room velocity, and infrastructure governance.
          </p>
        </div>

        {/* 3 Perspective Tabs */}
        <div className="flex flex-col sm:flex-row justify-center gap-3">
          {perspectives.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-5 py-3.5 rounded-2xl text-left border transition-all duration-200 flex items-center gap-3 ${
                  isActive
                    ? 'bg-white dark:bg-navy-900 border-teal-500 shadow-glow-teal ring-2 ring-teal-500/20'
                    : 'bg-white/60 dark:bg-navy-900/40 border-slate-200 dark:border-navy-800 hover:border-teal-400 text-slate-600 dark:text-slate-400'
                }`}
              >
                <div className={`p-2 rounded-xl transition ${
                  isActive
                    ? 'bg-gradient-to-br from-teal-500 to-cyan-500 text-white shadow-glow-teal'
                    : 'bg-slate-100 dark:bg-navy-850 text-slate-500 dark:text-slate-400'
                }`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <h4 className={`text-sm font-bold ${
                    isActive ? 'text-navy-900 dark:text-white' : 'text-slate-700 dark:text-slate-300'
                  }`}>
                    {tab.shortTitle}
                  </h4>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                    {tab.tagline.split('&')[0]}
                  </p>
                </div>
              </button>
            );
          })}
        </div>

        {/* Dynamic Stakeholder Content Container */}
        <div className="bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-navy-800 p-8 lg:p-10 shadow-medical-card dark:shadow-medical-card-dark space-y-8">
          
          {/* Top Banner: Role & Quote */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center pb-8 border-b border-slate-200 dark:border-navy-800">
            <div className="lg:col-span-8 space-y-4">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-lg bg-teal-500/10 text-teal-600 dark:text-cyan-400">
                  <CurrentIcon className="w-4 h-4" />
                </span>
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-teal-600 dark:text-cyan-400">
                  Strategic Perspective: {current.title}
                </span>
              </div>
              <h3 className="text-2xl font-extrabold text-navy-900 dark:text-white">
                {current.tagline}
              </h3>
              <blockquote className="text-sm sm:text-base text-slate-700 dark:text-slate-200 italic border-l-2 border-teal-500 pl-4 py-1 leading-relaxed">
                "{current.heroQuote}"
              </blockquote>
            </div>

            {/* Quick Metrics Strip */}
            <div className="lg:col-span-4 grid grid-cols-3 lg:grid-cols-1 gap-3">
              {current.metrics.map((m, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 text-center lg:text-left">
                  <span className="text-xl sm:text-2xl font-extrabold text-teal-600 dark:text-cyan-400 font-mono block">
                    {m.value}
                  </span>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                    {m.label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Key Capabilities Grid (4 Pillars) */}
          <div>
            <h4 className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 font-bold mb-6">
              Core Technical & Operational Capabilities
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {current.keyCapabilities.map((cap, idx) => (
                <div 
                  key={idx}
                  className="p-5 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 space-y-2 hover:border-teal-500/50 transition"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-teal-500 shrink-0" />
                    <h5 className="font-bold text-sm text-navy-900 dark:text-white">
                      {cap.title}
                    </h5>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed pl-6">
                    {cap.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* CTA Bar */}
          {onScheduleDemo && (
            <div className="pt-4 border-t border-slate-200 dark:border-navy-800 flex flex-col sm:flex-row items-center justify-between gap-4">
              <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                Request an on-premise technical demonstration tailored for {current.title}.
              </span>
              <button
                onClick={onScheduleDemo}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 shadow-glow-teal transition shrink-0"
              >
                <span>Request Stakeholder Consultation</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

        </div>

      </div>
    </section>
  );
};

export default StakeholderViews;
