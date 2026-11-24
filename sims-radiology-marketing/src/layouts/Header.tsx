import React, { useState } from 'react';

interface HeaderProps {
  activePage: string;
  onNavigate: (page: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ activePage, onNavigate }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { id: 'home', label: 'Platform' },
    { id: 'solutions', label: 'Clinical Solutions' },
    { id: 'security', label: 'Security & Air-Gap' },
    { id: 'pricing', label: 'ROI & Tiers' },
  ];

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-clinical-950/85 border-b border-clinical-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Brand */}
          <div 
            className="flex items-center gap-3.5 cursor-pointer group"
            onClick={() => onNavigate('home')}
          >
            <div className="w-10 h-10 rounded-xl bg-clinical-900 border border-cyan-500/40 flex items-center justify-center shadow-glow-cyan/20 group-hover:border-cyan-400 transition-all">
              <svg className="w-6 h-6 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="9" strokeDasharray="3 3"/>
                <path d="M12 3v18M3 12h18"/>
                <circle cx="12" cy="12" r="3" fill="#06B6D4" stroke="none"/>
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight text-white font-sans">
                  SIMS<span className="text-cyan-400">.</span>AI
                </span>
                <span className="text-[10px] uppercase font-mono tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                  Agentic OS
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono tracking-tight hidden sm:block">Radiology Diagnostic Operating Platform</p>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <button
                key={link.id}
                onClick={() => onNavigate(link.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activePage === link.id
                    ? 'text-cyan-300 bg-clinical-900/90 border border-cyan-500/30 shadow-sm'
                    : 'text-slate-300 hover:text-white hover:bg-clinical-900/50'
                }`}
              >
                {link.label}
              </button>
            ))}
          </nav>

          {/* Right Action */}
          <div className="hidden md:flex items-center gap-3">
            <button
              onClick={() => onNavigate('demo')}
              className="relative inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium rounded-lg text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-glow-cyan transition-all duration-200 active:scale-95"
            >
              Request Clinical Demo
            </button>
          </div>

          {/* Mobile hamburger */}
          <div className="md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-clinical-900 focus:outline-none"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-clinical-950 border-b border-clinical-800 px-4 pt-2 pb-5 space-y-2">
          {navLinks.map((link) => (
            <button
              key={link.id}
              onClick={() => {
                onNavigate(link.id);
                setMobileMenuOpen(false);
              }}
              className={`w-full text-left px-3 py-2.5 rounded-md text-base font-medium ${
                activePage === link.id
                  ? 'text-cyan-400 bg-clinical-900'
                  : 'text-slate-300 hover:bg-clinical-900'
              }`}
            >
              {link.label}
            </button>
          ))}
          <button
            onClick={() => {
              onNavigate('demo');
              setMobileMenuOpen(false);
            }}
            className="w-full mt-3 text-center px-4 py-2.5 rounded-lg text-sm font-medium text-white bg-cyan-600 hover:bg-cyan-500"
          >
            Request Clinical Demo
          </button>
        </div>
      )}
    </header>
  );
};
