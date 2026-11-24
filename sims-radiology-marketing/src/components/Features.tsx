import React from 'react';
import { featureSpecs } from '../data/features';
import { Check } from 'lucide-react';

export const Features: React.FC = () => {
  return (
    <section className="py-20 bg-slate-50/50 dark:bg-navy-950/50 border-y border-slate-200 dark:border-navy-800 relative transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
          <span className="text-xs font-mono font-semibold uppercase tracking-widest text-teal-600 dark:text-cyan-400 bg-teal-500/10 border border-teal-500/20 px-3 py-1 rounded-full">
            Autonomous Pipeline Intelligence
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-navy-900 dark:text-white tracking-tight">
            Engineered for High-Acuity Diagnostic Triage
          </h2>
          <p className="text-base text-slate-600 dark:text-slate-300">
            Every layer follows Clean Architecture with strict inward dependency boundaries, decoupling domain clinical safety from rapid AI model evolutions.
          </p>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {featureSpecs.map((feature) => (
            <div 
              key={feature.id}
              className="bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-navy-800 shadow-medical-card dark:shadow-medical-card-dark medical-card-hover flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-teal-600 dark:text-cyan-400 bg-teal-500/10 border border-teal-500/20 px-2.5 py-1 rounded-md">
                    {feature.badge}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    {feature.category}
                  </span>
                </div>

                <h3 className="text-xl font-bold text-navy-900 dark:text-white mb-2.5">
                  {feature.title}
                </h3>

                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed mb-6">
                  {feature.description}
                </p>

                <div className="space-y-2 mb-6">
                  {feature.technicalHighlights.map((highlight, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300">
                      <Check className="w-3.5 h-3.5 text-teal-500 shrink-0 mt-0.5" />
                      <span>{highlight}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-navy-800 flex items-center justify-between">
                <span className="text-xs text-slate-500 dark:text-slate-400">Validated Metric:</span>
                <span className="text-xs font-mono font-bold text-teal-700 dark:text-cyan-300 bg-teal-50 dark:bg-navy-850 px-2.5 py-1 rounded border border-teal-200 dark:border-teal-500/30">
                  {feature.metrics}
                </span>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
};
