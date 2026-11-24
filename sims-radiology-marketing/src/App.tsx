import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { Hero } from './components/Hero';
import { FeatureShowcase } from './components/FeatureShowcase';
import { Features } from './components/Features';
import { StakeholderViews } from './components/StakeholderViews';
import { RoiCalculator } from './components/RoiCalculator';
import { SecuritySection } from './components/SecuritySection';
import { ArchitectureDiagram } from './components/ArchitectureDiagram';
import { CaseConciergeDemo } from './components/features/CaseConciergeDemo';
import { WorklistDemo } from './components/features/WorklistDemo';
import { ReportingDemo } from './components/features/ReportingDemo';
import { TaskOrchestratorDemo } from './components/features/TaskOrchestratorDemo';
import { DemoRequest } from './pages/DemoRequest';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [isDark, setIsDark] = useState<boolean>(true);

  // Sync dark class on html root element
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [activeTab]);

  const toggleTheme = () => {
    setIsDark(prev => !prev);
  };

  const handleOpenDemo = () => {
    setActiveTab('request-demo');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'case-concierge':
        return (
          <div className="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
            <div className="text-center max-w-3xl mx-auto space-y-3">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-teal-600 dark:text-cyan-400 bg-teal-500/10 px-3 py-1 rounded-full border border-teal-500/20">
                Autonomous Pre-Read Synthesis
              </span>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-900 dark:text-white">
                Case Concierge AI
              </h1>
              <p className="text-slate-600 dark:text-slate-300 text-sm">
                Aggregates clinical referral indications, EHR problem lists, past imaging, and lab results into an actionable pre-read briefing.
              </p>
            </div>
            <CaseConciergeDemo />
            <TaskOrchestratorDemo />
          </div>
        );

      case 'worklist-reporting':
        return (
          <div className="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
            <div className="text-center max-w-3xl mx-auto space-y-3">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-teal-600 dark:text-cyan-400 bg-teal-500/10 px-3 py-1 rounded-full border border-teal-500/20">
                Unified Dynamic Orchestration
              </span>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-900 dark:text-white">
                Worklist & Structured Reporting
              </h1>
              <p className="text-slate-600 dark:text-slate-300 text-sm">
                Dynamic acuity worklist sorting across CT, MRI, and X-ray with voice-assisted ACR-compliant structured report generation.
              </p>
            </div>
            <WorklistDemo />
            <ReportingDemo />
          </div>
        );

      case 'security-architecture':
        return (
          <div className="py-6 space-y-12">
            <SecuritySection
              onRequestWhitepaper={handleOpenDemo}
              onScheduleDemo={handleOpenDemo}
            />
          </div>
        );

      case 'roi-impact':
        return (
          <div className="py-12 space-y-12">
            <StakeholderViews onScheduleDemo={handleOpenDemo} />
            <RoiCalculator onRequestQuote={handleOpenDemo} />
          </div>
        );

      case 'request-demo':
        return (
          <div className="py-12">
            <DemoRequest />
          </div>
        );

      case 'overview':
      default:
        return (
          <div className="space-y-12">
            <Hero
              onExploreDemo={handleOpenDemo}
              onExploreArchitecture={() => setActiveTab('security-architecture')}
            />

            <FeatureShowcase onScheduleDemo={handleOpenDemo} />

            <StakeholderViews onScheduleDemo={handleOpenDemo} />

            <RoiCalculator onRequestQuote={handleOpenDemo} />

            <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <ArchitectureDiagram />
            </section>

            <Features />

            <SecuritySection
              onRequestWhitepaper={handleOpenDemo}
              onScheduleDemo={handleOpenDemo}
            />

            {/* Bottom Call to Action */}
            <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
              <div className="relative rounded-3xl overflow-hidden bg-gradient-to-r from-navy-900 via-navy-850 to-navy-900 border border-teal-500/30 p-10 lg:p-16 text-center space-y-6 shadow-glow-teal">
                <div className="inline-block px-3 py-1 rounded-full bg-teal-500/10 text-cyan-300 text-xs font-mono font-bold uppercase tracking-wider border border-teal-500/30">
                  Ready for Retrospective or Prospective Evaluation
                </div>
                <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight max-w-3xl mx-auto">
                  Deploy Autonomous Agentic Triage Inside Your Secure Hospital DMZ
                </h2>
                <p className="text-slate-300 text-base max-w-2xl mx-auto">
                  No PHI leaves your premise. Experience sub-second DICOM ingestion, NVIDIA NeMo Guardrail verification, and seamless PACS integration.
                </p>
                <div className="pt-2">
                  <button
                    onClick={handleOpenDemo}
                    className="px-8 py-4 rounded-xl font-bold text-navy-950 bg-gradient-to-r from-teal-400 to-cyan-400 hover:from-teal-300 hover:to-cyan-300 shadow-glow-cyan text-base transition duration-200"
                  >
                    Schedule Hospital Pilot Demo
                  </button>
                </div>
              </div>
            </section>
          </div>
        );
    }
  };

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      isDark ? 'bg-surface-dark text-slate-100' : 'bg-surface-light text-navy-900'
    }`}>
      <Navbar
        activeTab={activeTab}
        onNavigate={setActiveTab}
        isDark={isDark}
        onToggleTheme={toggleTheme}
        onRequestDemo={handleOpenDemo}
      />

      <main>
        {renderContent()}
      </main>

      <Footer
        onNavigate={setActiveTab}
        onRequestDemo={handleOpenDemo}
      />
    </div>
  );
};

export default App;
