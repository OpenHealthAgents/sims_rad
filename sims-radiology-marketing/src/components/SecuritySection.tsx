import React from 'react';
import { DeploymentTopologyWidget } from './DeploymentTopologyWidget';
import { SafetyGuardrails } from './SafetyGuardrails';
import { VendorCapabilityConformance } from './VendorCapabilityConformance';
import { ShieldCheck, Lock, FileCode, CheckCircle2, ArrowRight } from 'lucide-react';

interface SecuritySectionProps {
  onRequestWhitepaper?: () => void;
  onScheduleDemo?: () => void;
}

export const SecuritySection: React.FC<SecuritySectionProps> = ({ 
  onRequestWhitepaper, 
  onScheduleDemo 
}) => {
  return (
    <section className="py-16 space-y-20 relative transition-colors" id="security-architecture">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-20">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-mono font-bold uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4" />
            Enterprise Security, Architecture & EHR Integration
          </div>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-navy-900 dark:text-white tracking-tight">
            Hospital-Controlled Sovereignty & Clinical Safety Rails
          </h2>
          <p className="text-base text-slate-600 dark:text-slate-300 leading-relaxed">
            Engineered from inception for zero PHI egress. Deploy on-premises behind your hospital firewall with native DICOM C-STORE, BackBone HMS interoperability, and CharmHealth Cloud EHR writeback.
          </p>
        </div>

        {/* 1. Hospital-Controlled Deployment Diagram */}
        <div className="space-y-4">
          <DeploymentTopologyWidget />
        </div>

        {/* 2. AI Safety & Guardrails Cards */}
        <div className="space-y-4">
          <SafetyGuardrails />
        </div>

        {/* 3. Vendor Capability Conformance Checklist */}
        <div className="space-y-4">
          <VendorCapabilityConformance />
        </div>

        {/* CISO & IT Action Banner */}
        <div className="rounded-3xl p-8 sm:p-10 bg-gradient-to-r from-navy-900 via-navy-850 to-navy-900 text-white border border-teal-500/30 shadow-glow-teal flex flex-col lg:flex-row items-center justify-between gap-8">
          <div className="space-y-3 text-center lg:text-left">
            <div className="inline-block px-3 py-1 rounded-full bg-teal-500/10 text-cyan-300 text-xs font-mono font-bold uppercase tracking-wider border border-teal-500/30">
              Hospital IT & CISO Fast-Track
            </div>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-white">
              Request the Technical Architecture & BAA Pack
            </h3>
            <p className="text-xs sm:text-sm text-slate-300 max-w-xl">
              Includes Docker Compose on-prem manifests, HIPAA Security Risk Assessment, SOC 2 Type II audit report, and network port allocation guides.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 w-full lg:w-auto shrink-0">
            {onRequestWhitepaper && (
              <button
                onClick={onRequestWhitepaper}
                className="px-6 py-3.5 rounded-xl font-bold text-xs sm:text-sm text-white bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 shadow-glow-teal transition text-center"
              >
                Request Security Whitepaper & BAA
              </button>
            )}
            {onScheduleDemo && (
              <button
                onClick={onScheduleDemo}
                className="px-6 py-3.5 rounded-xl font-semibold text-xs sm:text-sm text-slate-200 bg-navy-800 border border-navy-700 hover:border-teal-400 hover:text-white transition text-center"
              >
                Schedule Technical Architecture Review
              </button>
            )}
          </div>
        </div>

      </div>
    </section>
  );
};

export default SecuritySection;
