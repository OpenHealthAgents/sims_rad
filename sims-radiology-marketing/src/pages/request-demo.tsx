import React from 'react';
import { DemoRequestForm } from '../components/DemoRequestForm';
import { RadiologistWorkbenchTour } from '../components/RadiologistWorkbenchTour';
import { ShieldCheck, Lock, CheckCircle2, Clock, Calendar, ArrowRight } from 'lucide-react';

export const RequestDemoPage: React.FC = () => {
  return (
    <div className="py-12 space-y-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-14">
        
        {/* Page Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-600 dark:text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4" />
            Institutional Trial & Technical Demonstration
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-navy-900 dark:text-white tracking-tight">
            Schedule Your Hospital Pilot & Architecture Review
          </h1>
          <p className="text-sm sm:text-base text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Evaluate the SIMS Agentic Operating Platform within your clinical imaging department. Experience sub-second DICOM ingestion, zero cloud PHI egress, and automated structured reporting.
          </p>
        </div>

        {/* 2-Column or Stacked Layout: Form + Sandbox Tour */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
          
          {/* Left Column (7 cols): Multi-Step Demo Booking Form */}
          <div className="lg:col-span-7">
            <DemoRequestForm />
          </div>

          {/* Right Column (5 cols): Sandbox Interactive Tour & Institutional Guarantees */}
          <div className="lg:col-span-5 space-y-6">
            
            {/* Live Sandbox Interactive Tour Card */}
            <RadiologistWorkbenchTour />

            {/* Pilot Evaluation SLA & Trust Card */}
            <div className="bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-navy-800 p-6 sm:p-7 shadow-medical-card dark:shadow-medical-card-dark space-y-4">
              <h4 className="font-bold text-sm text-navy-900 dark:text-white flex items-center gap-2">
                <Lock className="w-4 h-4 text-teal-500" />
                <span>Hospital Evaluation Standard Guarantees</span>
              </h4>

              <ul className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-teal-500 shrink-0 mt-0.5" />
                  <span>
                    <strong>Zero Vendor Lock-In:</strong> Works alongside existing Sectra, GE, Philips, and Siemens PACS over standard DICOM C-STORE.
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-teal-500 shrink-0 mt-0.5" />
                  <span>
                    <strong>Air-Gapped Deployment:</strong> 100% on-premises DMZ isolation with local model weights; zero external API egress.
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-teal-500 shrink-0 mt-0.5" />
                  <span>
                    <strong>Standard Healthcare BAA:</strong> Comprehensive HIPAA Business Associate Agreement executed prior to testing.
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-teal-500 shrink-0 mt-0.5" />
                  <span>
                    <strong>Fast Evaluation Ramp:</strong> Connect synthetic test de-identified cohorts in under 48 hours without infrastructure changes.
                  </span>
                </li>
              </ul>

              <div className="pt-3 border-t border-slate-200 dark:border-navy-800 text-[11px] font-mono text-slate-500 dark:text-slate-400">
                Questions? Direct email: <strong>health-systems@simsradiology.org</strong>
              </div>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
};

export default RequestDemoPage;
