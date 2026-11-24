import React, { useState } from 'react';
import { Sun, Moon, Menu, X, ShieldCheck, Activity } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  onNavigate: (tab: string) => void;
  isDark: boolean;
  onToggleTheme: () => void;
  onRequestDemo: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onNavigate,
  isDark,
  onToggleTheme,
  onRequestDemo,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { id: 'overview', label: 'Overview' },
    { id: 'case-concierge', label: 'Case Concierge' },
    { id: 'worklist-reporting', label: 'Worklist & Reporting' },
    { id: 'security-architecture', label: 'Security & Architecture' },
    { id: 'roi-impact', label: 'ROI Impact' },
  ];

  const handleLinkClick = (id: string) => {
    onNavigate(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className={`sticky top-0 z-50 transition-colors duration-200 ${
      isDark ? 'glass-header-dark' : 'glass-header-light'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Brand Identity */}
          <div 
            className="flex items-center gap-3.5 cursor-pointer group"
            onClick={() => handleLinkClick('overview')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-500 p-[1.5px] shadow-glow-teal flex items-center justify-center transition-transform group-hover:scale-105">
              <div className="w-full h-full bg-navy-900 rounded-[10px] flex items-center justify-center">
                <Activity className="w-5 h-5 text-cyan-400 group-hover:rotate-12 transition-transform" />
              </div>
            </div>
            
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className={`font-extrabold text-xl tracking-tight ${
                  isDark ? 'text-white' : 'text-navy-900'
                }`}>
                  SIMS<span className="text-teal-500">.</span>Radiology
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider bg-teal-500/10 text-teal-600 dark:text-cyan-400 border border-teal-500/20 dark:border-cyan-500/30">
                  AI OS
                </span>
              </div>
              <span className={`text-[11px] font-mono tracking-tight hidden sm:block ${
                isDark ? 'text-slate-400' : 'text-navy-600'
              }`}>
                Agentic Clinical Triage & Diagnostic Intelligence
              </span>
            </div>
          </div>

          {/* Desktop Nav Items */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navLinks.map((link) => {
              const isActive = activeTab === link.id;
              return (
                <button
                  key={link.id}
                  onClick={() => handleLinkClick(link.id)}
                  className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? isDark
                        ? 'text-cyan-300 bg-navy-850/90 border border-teal-500/40 shadow-sm'
                        : 'text-teal-700 bg-teal-50 border border-teal-300 shadow-sm'
                      : isDark
                        ? 'text-slate-300 hover:text-white hover:bg-navy-850/60'
                        : 'text-navy-800 hover:text-teal-600 hover:bg-slate-100'
                  }`}
                >
                  {link.label}
                </button>
              );
            })}
          </nav>

          {/* Right Action Bar */}
          <div className="hidden md:flex items-center gap-3">
            
            {/* Theme Toggle Button */}
            <button
              onClick={onToggleTheme}
              aria-label="Toggle Dark / Light Theme"
              className={`p-2 rounded-lg border transition-all ${
                isDark
                  ? 'bg-navy-850 border-navy-700 text-yellow-400 hover:bg-navy-800'
                  : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100 shadow-sm'
              }`}
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* Prominent CTA */}
            <button
              onClick={onRequestDemo}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-sm font-bold text-white bg-gradient-to-r from-teal-500 via-teal-600 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 shadow-glow-teal hover:shadow-glow-cyan transition-all active:scale-[0.98]"
            >
              <ShieldCheck className="w-4 h-4" />
              Request Pilot Demo
            </button>
          </div>

          {/* Mobile menu trigger */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={onToggleTheme}
              className={`p-2 rounded-lg border ${
                isDark ? 'bg-navy-850 border-navy-700 text-yellow-400' : 'bg-white border-slate-200 text-slate-700'
              }`}
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className={`p-2 rounded-lg ${
                isDark ? 'text-slate-300 hover:bg-navy-850' : 'text-navy-800 hover:bg-slate-100'
              }`}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className={`md:hidden px-4 pt-3 pb-6 border-b space-y-2 transition-colors ${
          isDark ? 'bg-navy-950 border-navy-800' : 'bg-surface-light border-slate-200'
        }`}>
          {navLinks.map((link) => (
            <button
              key={link.id}
              onClick={() => handleLinkClick(link.id)}
              className={`w-full text-left px-3.5 py-2.5 rounded-lg text-sm font-medium ${
                activeTab === link.id
                  ? isDark ? 'text-cyan-300 bg-navy-850' : 'text-teal-600 bg-teal-50'
                  : isDark ? 'text-slate-300' : 'text-navy-800'
              }`}
            >
              {link.label}
            </button>
          ))}
          <button
            onClick={() => {
              onRequestDemo();
              setMobileMenuOpen(false);
            }}
            className="w-full mt-3 py-3 rounded-lg text-sm font-bold text-white bg-gradient-to-r from-teal-500 to-cyan-500 shadow-glow-teal flex items-center justify-center gap-2"
          >
            <ShieldCheck className="w-4 h-4" />
            Request Pilot Demo
          </button>
        </div>
      )}
    </header>
  );
};

export default Navbar;
