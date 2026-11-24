import React from 'react';
import { securityPillars } from '../data/securitySpecs';
import { ShieldCheck, Lock, FileCode, CheckCircle2 } from 'lucide-react';

export const SecurityMatrix: React.FC = () => {
  return (
    <section className="py-20 bg-white dark:bg-navy-950 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <span className="text-xs font-mono font-semibold uppercase tracking-widest text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
            Enterprise Security & Clinical Safety Rails
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-navy-900 dark:text-white">
            Zero Cloud Egress. Zero Black-Box Hallucinations.
          </h2>
          <p className="text-slate-600 dark:text-slate-300 text-sm">
            Architected specifically for Tier-1 healthcare compliance, protecting sensitive Protected Health Information (PHI) under strict institutional control.
          </p>
        </div>

        {/* Pillars Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          {securityPillars.map((pillar, idx) => (
            <div key={idx} className="bg-slate-50 dark:bg-navy-900 rounded-2xl p-7 border border-slate-200 dark:border-navy-800 shadow-medical-card dark:shadow-medical-card-dark flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-mono uppercase tracking-wider text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded-md inline-block mb-4">
                  {pillar.badge}
                </span>
                <h3 className="text-xl font-bold text-navy-900 dark:text-white mb-3">
                  {pillar.title}
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed mb-6">
                  {pillar.description}
                </p>
                <ul className="space-y-2.5 text-xs text-slate-600 dark:text-slate-400">
                  {pillar.items.map((item, itemIdx) => (
                    <li key={itemIdx} className="flex items-start gap-2">
                      <span className="text-teal-500 font-bold">●</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        {/* Architectural Comparison Table */}
        <div className="bg-slate-50 dark:bg-navy-900 rounded-2xl p-6 lg:p-8 border border-slate-200 dark:border-navy-800 shadow-medical-card dark:shadow-medical-card-dark">
          <h3 className="text-lg font-bold text-navy-900 dark:text-white mb-6">
            SIMS Radiology vs. Generic Cloud AI Vendors
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-200 dark:border-navy-800 text-slate-500 dark:text-slate-400">
                  <th className="pb-3 font-semibold">Security / Clinical Vector</th>
                  <th className="pb-3 font-semibold text-teal-600 dark:text-cyan-400">SIMS Radiology AI OS</th>
                  <th className="pb-3 font-semibold text-slate-400">Traditional Cloud SaaS Models</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-navy-800 text-slate-700 dark:text-slate-300">
                <tr>
                  <td className="py-3 font-medium text-navy-900 dark:text-white">PHI Data Sovereignty</td>
                  <td className="py-3 text-emerald-600 dark:text-emerald-400 font-bold">100% Air-Gapped On-Premises (Zero Egress)</td>
                  <td className="py-3 text-rose-500">Public Cloud REST endpoints (Egress risk)</td>
                </tr>
                <tr>
                  <td className="py-3 font-medium text-navy-900 dark:text-white">Hallucination Mitigation</td>
                  <td className="py-3 text-emerald-600 dark:text-emerald-400 font-bold">NVIDIA NeMo Guardrails Deterministic Rails</td>
                  <td className="py-3 text-rose-500">Heuristic prompt engineering (Non-deterministic)</td>
                </tr>
                <tr>
                  <td className="py-3 font-medium text-navy-900 dark:text-white">XAI / Clinical Auditability</td>
                  <td className="py-3 text-emerald-600 dark:text-emerald-400 font-bold">Pixel-level SHAP heatmaps on DICOM slices</td>
                  <td className="py-3 text-rose-500">Black-box text summary without spatial proof</td>
                </tr>
                <tr>
                  <td className="py-3 font-medium text-navy-900 dark:text-white">Integration Standard</td>
                  <td className="py-3 text-emerald-600 dark:text-emerald-400 font-bold">Native DICOM Part 10 & FHIR R4 Core</td>
                  <td className="py-3 text-amber-500">Proprietary REST schema requiring custom ETL</td>
                </tr>
                <tr>
                  <td className="py-3 font-medium text-navy-900 dark:text-white">Architecture Standard</td>
                  <td className="py-3 text-emerald-600 dark:text-emerald-400 font-bold">Uncle Bob Clean Architecture & Kestra DAGs</td>
                  <td className="py-3 text-slate-400">Tightly coupled monolith / vendor lock-in</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </section>
  );
};
