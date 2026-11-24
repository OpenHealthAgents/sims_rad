import React from 'react';
import { TodayVsProposedWidget } from './TodayVsProposedWidget';
import { DicomMockViewer } from './DicomMockViewer';
import { 
  ShieldCheck, 
  ArrowRight, 
  Activity, 
  Lock, 
  Zap, 
  Clock, 
  Award, 
  Layers, 
  FileCheck2,
  ChevronRight
} from 'lucide-react';

interface HeroProps {
  onExploreDemo: () => void;
  onExploreArchitecture: () => void;
}

export const Hero: React.FC<HeroProps> = ({ onExploreDemo, onExploreArchitecture }) => {
  return (
    <div className="relative overflow-hidden pt-8 pb-16 lg:pt-14 lg:pb-24">
      
      {/* Subtle Animated Network / Imaging Background Node Graphic */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden select-none opacity-40 dark:opacity-60">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="heroGlow" cx="50%" cy="30%" r="60%">
              <stop offset="0%" stopColor="#2DC4DC" stopOpacity="0.12"/>
              <stop offset="50%" stopColor="#00A6A6" stopOpacity="0.04"/>
              <stop offset="100%" stopColor="transparent" stopOpacity="0"/>
            </radialGradient>
            <pattern id="imagingGrid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-slate-300 dark:text-navy-800" opacity="0.6"/>
              <circle cx="60" cy="0" r="1.5" fill="#00A6A6" opacity="0.4"/>
            </pattern>
          </defs>

          {/* Grid pattern */}
          <rect width="100%" height="100%" fill="url(#imagingGrid)" />
          <rect width="100%" height="100%" fill="url(#heroGlow)" />

          {/* Agentic Neural Node Connections */}
          <g className="transition-all duration-1000">
            {/* Connecting lines */}
            <path d="M 150 120 Q 350 200 500 140 T 850 220" fill="none" stroke="#00A6A6" strokeWidth="1.2" strokeDasharray="4 6" opacity="0.4"/>
            <path d="M 400 320 Q 650 240 900 360" fill="none" stroke="#2DC4DC" strokeWidth="1" strokeDasharray="3 5" opacity="0.3"/>
            <path d="M 250 480 Q 550 400 800 520" fill="none" stroke="#00A6A6" strokeWidth="1" strokeDasharray="5 7" opacity="0.25"/>

            {/* Neural nodes with pulse animation */}
            <circle cx="150" cy="120" r="4" fill="#00A6A6" className="animate-pulse"/>
            <circle cx="500" cy="140" r="5" fill="#2DC4DC"/>
            <circle cx="500" cy="140" r="14" stroke="#2DC4DC" strokeWidth="0.8" strokeDasharray="2 3" opacity="0.6" className="animate-spin" style={{ animationDuration: '12s' }}/>

            <circle cx="850" cy="220" r="4.5" fill="#00A6A6"/>
            <circle cx="400" cy="320" r="3.5" fill="#2DC4DC"/>
            <circle cx="900" cy="360" r="4" fill="#00A6A6"/>
            <circle cx="250" cy="480" r="5" fill="#2DC4DC"/>
          </g>
        </svg>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 space-y-16">
        
        {/* Main Hero Header Presentation */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          
          {/* Left Column: Core Positioning Copy & CTAs */}
          <div className="lg:col-span-7 space-y-6">
            
            {/* Clinical standard badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-500/10 dark:bg-navy-900 border border-teal-500/30 shadow-inner">
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-ping"></span>
              <span className="text-xs font-semibold text-teal-700 dark:text-cyan-300">
                Next-Generation Radiology Operating Model
              </span>
              <span className="text-slate-400">|</span>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Agentic AI OS</span>
            </div>

            {/* Primary Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-navy-900 dark:text-white tracking-tight leading-[1.12]">
              Transforming Radiology from Isolated AI Tools to an{' '}
              <span className="bg-gradient-to-r from-teal-500 via-teal-600 to-cyan-500 bg-clip-text text-transparent">
                Agentic Operating Model
              </span>
            </h1>

            {/* Sub-headline */}
            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl font-sans">
              Unify CT, MRI, and X-ray workflows. AI prepares cases, drafts reports, and orchestrates follow-ups—while radiologists retain 100% interpretation authority and sign-off accountability.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <button
                onClick={onExploreDemo}
                className="inline-flex items-center justify-center gap-2 px-7 py-4 rounded-xl text-base font-bold text-white bg-gradient-to-r from-teal-500 via-teal-600 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 shadow-glow-teal hover:shadow-glow-cyan transition-all duration-200 active:scale-[0.98]"
              >
                <ShieldCheck className="w-5 h-5" />
                Schedule Hospital Pilot Demo
                <ArrowRight className="w-4 h-4 ml-1" />
              </button>

              <button
                onClick={onExploreArchitecture}
                className="inline-flex items-center justify-center gap-2 px-6 py-4 rounded-xl text-base font-semibold text-navy-800 dark:text-slate-200 bg-white dark:bg-navy-900 border border-slate-300 dark:border-navy-700 hover:border-teal-500 transition duration-200 shadow-sm"
              >
                Explore Architecture & Security Blueprint
                <ChevronRight className="w-4 h-4 text-teal-500" />
              </button>
            </div>

            {/* Micro-assurances */}
            <div className="flex flex-wrap items-center gap-6 pt-2 text-xs font-mono text-slate-500 dark:text-slate-400">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                Air-Gapped On-Premises Ready
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span>
                Zero Cloud PHI Egress
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-500"></span>
                DICOM Part 10 & FHIR R4
              </span>
            </div>

          </div>

          {/* Right Column: Live Ingest & Triage Visualizer */}
          <div className="lg:col-span-5">
            <div className="relative">
              <div className="absolute -inset-1.5 bg-gradient-to-r from-teal-500 to-cyan-500 rounded-3xl blur-xl opacity-20"></div>
              <div className="relative">
                <DicomMockViewer />
              </div>
            </div>
          </div>

        </div>

        {/* Key Value Metrics Strip */}
        <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 p-6 sm:p-8 shadow-medical-card dark:shadow-medical-card-dark">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8 divide-y sm:divide-y-0 sm:divide-x divide-slate-200 dark:divide-navy-800">
            
            {/* Metric 1 */}
            <div className="pt-4 sm:pt-0 sm:px-4 first:pt-0 first:px-0 space-y-1.5">
              <div className="flex items-center gap-2 text-teal-600 dark:text-cyan-400">
                <Award className="w-4 h-4" />
                <span className="text-xs font-mono font-semibold uppercase tracking-wider">Clinical Standard</span>
              </div>
              <p className="text-2xl sm:text-3xl font-extrabold text-navy-900 dark:text-white font-mono">
                29+ Years
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Clinical Leadership Design Standard
              </p>
            </div>

            {/* Metric 2 */}
            <div className="pt-4 sm:pt-0 sm:px-4 space-y-1.5">
              <div className="flex items-center gap-2 text-teal-600 dark:text-cyan-400">
                <Layers className="w-4 h-4" />
                <span className="text-xs font-mono font-semibold uppercase tracking-wider">Modality Scope</span>
              </div>
              <p className="text-2xl sm:text-3xl font-extrabold text-navy-900 dark:text-white font-mono">
                3 Modalities
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Unified (CT, MRI, X-ray)
              </p>
            </div>

            {/* Metric 3 */}
            <div className="pt-4 sm:pt-0 sm:px-4 space-y-1.5">
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                <FileCheck2 className="w-4 h-4" />
                <span className="text-xs font-mono font-semibold uppercase tracking-wider">Safety Policy</span>
              </div>
              <p className="text-2xl sm:text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
                0% Unvalidated
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Writeback (Strict Radiologist Gate)
              </p>
            </div>

            {/* Metric 4 */}
            <div className="pt-4 sm:pt-0 sm:px-4 space-y-1.5">
              <div className="flex items-center gap-2 text-teal-600 dark:text-cyan-400">
                <Clock className="w-4 h-4" />
                <span className="text-xs font-mono font-semibold uppercase tracking-wider">Speed to Worklist</span>
              </div>
              <p className="text-2xl sm:text-3xl font-extrabold text-teal-600 dark:text-cyan-400 font-mono">
                &lt; 60s
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Event-to-Worklist Integration Latency Target
              </p>
            </div>

          </div>
        </div>

        {/* Embedded Interactive Comparison Widget */}
        <section className="pt-6">
          <TodayVsProposedWidget onScheduleDemo={onExploreDemo} />
        </section>

      </div>

    </div>
  );
};

export default Hero;
