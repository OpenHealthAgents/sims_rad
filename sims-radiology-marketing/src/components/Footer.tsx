import React from 'react';
import { ShieldAlert, Lock, CheckCircle2, Phone, Mail, Building2, ExternalLink } from 'lucide-react';

interface FooterProps {
  onNavigate: (tab: string) => void;
  onRequestDemo: () => void;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate, onRequestDemo }) => {
  return (
    <footer className="bg-navy-950 text-slate-300 border-t border-navy-800 transition-colors">
      
      {/* Prominent Clinical Disclaimer Banner */}
      <div className="bg-navy-900 border-b border-navy-800/80 py-4 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex items-start sm:items-center gap-3">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0 mt-0.5 sm:mt-0">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div className="text-xs sm:text-sm leading-relaxed">
            <strong className="text-white font-semibold block sm:inline mr-2">
              Mandatory Clinical Disclaimer & AI Architecture Notice:
            </strong>
            <span className="text-slate-300">
              Clinician-in-the-Loop Architecture: AI assists workflow; final interpretation remains strictly under authorized radiologist sign-off.
            </span>
          </div>
        </div>
      </div>

      {/* Main Footer Directory */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10">
          
          {/* Column 1: Brand & Architecture Description */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center p-[1px]">
                <div className="w-full h-full bg-navy-900 rounded-[11px] flex items-center justify-center font-bold text-cyan-400 text-sm">
                  S
                </div>
              </div>
              <span className="font-extrabold text-xl text-white tracking-tight">
                SIMS<span className="text-teal-400">.</span>Radiology
              </span>
            </div>
            
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed max-w-sm">
              The Agentic Clinical Operating Platform for High-Acuity Radiology. Coordinating specialized LangGraph sub-agents, NVIDIA NeMo Guardrails, and native DICOM / FHIR R4 interfaces.
            </p>

            <div className="flex flex-wrap gap-2 pt-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono bg-teal-500/10 text-cyan-300 border border-teal-500/20">
                <CheckCircle2 className="w-3 h-3 text-teal-400" />
                Air-Gapped On-Premises
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono bg-navy-850 text-slate-300 border border-navy-700">
                <Lock className="w-3 h-3 text-cyan-400" />
                Zero PHI Egress
              </span>
            </div>
          </div>

          {/* Column 2: Navigation Links */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-teal-400 font-bold">
              Platform Modules
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <button onClick={() => onNavigate('overview')} className="hover:text-cyan-300 transition">
                  Platform Overview
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('case-concierge')} className="hover:text-cyan-300 transition">
                  Case Concierge (Agent Triage)
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('worklist-reporting')} className="hover:text-cyan-300 transition">
                  Worklist & Reporting Assist
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('security-architecture')} className="hover:text-cyan-300 transition">
                  Security & Architecture
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('roi-impact')} className="hover:text-cyan-300 transition">
                  ROI & Capacity Impact
                </button>
              </li>
            </ul>
          </div>

          {/* Column 3: Compliance & Standards Links */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-teal-400 font-bold">
              Compliance & Specs
            </h4>
            <ul className="space-y-2 text-xs">
              <li className="flex items-center gap-1.5">
                <span className="text-teal-400 font-mono">›</span>
                <span className="hover:text-white cursor-pointer">HIPAA & HITECH BAA</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="text-teal-400 font-mono">›</span>
                <span className="hover:text-white cursor-pointer">SOC 2 Type II Certified</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="text-teal-400 font-mono">›</span>
                <span className="hover:text-white cursor-pointer">DICOM PS 3.10 / C-STORE</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="text-teal-400 font-mono">›</span>
                <span className="hover:text-white cursor-pointer">HL7 FHIR R4 DiagnosticReport</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="text-teal-400 font-mono">›</span>
                <span className="hover:text-white cursor-pointer">FDA 510(k) Pre-Market Dossier</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="text-teal-400 font-mono">›</span>
                <span className="hover:text-white cursor-pointer">ISO 27001 & ISO 13485 Alignment</span>
              </li>
            </ul>
          </div>

          {/* Column 4: Hospital Contact Channels */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-teal-400 font-bold">
              Hospital Contact Channels
            </h4>
            <div className="space-y-2.5 text-xs text-slate-400">
              <div className="flex items-start gap-2">
                <Building2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-white font-medium">Enterprise Health Pilots</p>
                  <p className="text-[11px]">health-systems@simsradiology.org</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Mail className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-white font-medium">IT & CISO Architecture</p>
                  <p className="text-[11px]">security-review@simsradiology.org</p>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Phone className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-white font-medium">Clinical Informatics SLA Desk</p>
                  <p className="text-[11px] font-mono">+1 (800) 555-SIMS-RAD (24/7/365)</p>
                </div>
              </div>

              <button
                onClick={onRequestDemo}
                className="w-full mt-2 py-2 px-3 rounded-lg text-xs font-bold text-navy-950 bg-gradient-to-r from-teal-400 to-cyan-400 hover:from-teal-300 hover:to-cyan-300 transition"
              >
                Inquire for Institutional Evaluation
              </button>
            </div>
          </div>

        </div>

        {/* Bottom Legal / Disclaimers Bar */}
        <div className="mt-12 pt-6 border-t border-navy-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>
            © {new Date().getFullYear()} SIMS Radiology AI Platform Inc. All clinical rights reserved. Built with Clean Architecture.
          </p>
          <div className="flex items-center gap-4 text-[11px] font-mono">
            <span className="hover:text-slate-300 cursor-pointer">Privacy & BAA Terms</span>
            <span>•</span>
            <span className="hover:text-slate-300 cursor-pointer">Security Protocol</span>
            <span>•</span>
            <span className="hover:text-slate-300 cursor-pointer">PACS Matrix</span>
          </div>
        </div>

      </div>

    </footer>
  );
};

export default Footer;
