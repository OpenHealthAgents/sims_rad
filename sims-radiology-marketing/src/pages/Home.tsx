import React from 'react';
import { Hero } from '../components/Hero';
import { FeatureShowcase } from '../components/FeatureShowcase';
import { StakeholderViews } from '../components/StakeholderViews';
import { RoiCalculator } from '../components/RoiCalculator';
import { SecuritySection } from '../components/SecuritySection';
import { ArchitectureDiagram } from '../components/ArchitectureDiagram';
import { Features } from '../components/Features';

interface HomeProps {
  onNavigate: (page: string) => void;
}

export const Home: React.FC<HomeProps> = ({ onNavigate }) => {
  return (
    <div className="space-y-12">
      {/* Hero Section with Embedded TodayVsProposedWidget & Metrics Strip */}
      <Hero
        onExploreDemo={() => onNavigate('request-demo')}
        onExploreArchitecture={() => onNavigate('security-architecture')}
      />

      {/* Interactive Core Operational Capabilities Showcase */}
      <FeatureShowcase onScheduleDemo={() => onNavigate('request-demo')} />

      {/* Stakeholder-Specific Solution Views (Directors, Radiologists, IT/Security) */}
      <StakeholderViews onScheduleDemo={() => onNavigate('request-demo')} />

      {/* Interactive ROI & Turnaround Time (TAT) Impact Calculator */}
      <RoiCalculator onRequestQuote={() => onNavigate('request-demo')} />

      {/* Clean Architecture Monorepo Topology */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ArchitectureDiagram />
      </section>

      {/* Agentic Capabilities Grid */}
      <Features />

      {/* Enterprise Security, Hospital Deployment Topology & EHR Conformance */}
      <SecuritySection
        onRequestWhitepaper={() => onNavigate('request-demo')}
        onScheduleDemo={() => onNavigate('request-demo')}
      />

      {/* Pre-Footer Action Banner */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="relative rounded-3xl overflow-hidden bg-gradient-to-r from-navy-900 via-navy-850 to-navy-900 border border-teal-500/30 p-10 lg:p-16 text-center space-y-6 shadow-glow-teal">
          <div className="inline-block px-3 py-1 rounded-full bg-teal-500/10 text-cyan-300 text-xs font-mono font-bold uppercase tracking-wider border border-teal-500/30">
            Validated Clinical Deployment
          </div>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight max-w-3xl mx-auto">
            Ready to Accelerate Critical Radiology Triage Without Cloud Egress?
          </h2>
          <p className="text-slate-300 text-base max-w-2xl mx-auto">
            Schedule an on-premise technical pilot or test SIMS against your historical de-identified DICOM cohorts.
          </p>
          <div className="pt-2">
            <button
              onClick={() => onNavigate('request-demo')}
              className="px-8 py-4 rounded-xl font-bold text-navy-950 bg-gradient-to-r from-teal-400 to-cyan-400 hover:from-teal-300 hover:to-cyan-300 shadow-glow-cyan text-base transition duration-200"
            >
              Schedule Hospital Pilot Demo
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
