import React, { useState } from 'react';
import { personas } from '../data/personas';
import { Check, X } from 'lucide-react';

export const PersonaTabs: React.FC = () => {
  const [selectedId, setSelectedId] = useState(personas[0].id);
  const activePersona = personas.find(p => p.id === selectedId) || personas[0];

  return (
    <section className="py-20 relative transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="text-center max-w-2xl mx-auto mb-12">
          <span className="text-xs font-mono font-semibold uppercase tracking-widest text-teal-600 dark:text-cyan-400 bg-teal-500/10 border border-teal-500/20 px-3 py-1 rounded-full">
            Clinical Stakeholder Alignment
          </span>
          <h2 className="text-3xl font-extrabold text-navy-900 dark:text-white mt-4">
            Built for Clinical Confidence, Enterprise Trust & Seamless Operations
          </h2>
        </div>

        {/* Tab Headers */}
        <div className="flex flex-wrap justify-center gap-3 mb-10">
          {personas.map((persona) => (
            <button
              key={persona.id}
              onClick={() => setSelectedId(persona.id)}
              className={`px-5 py-3 rounded-xl text-sm font-semibold transition-all ${
                selectedId === persona.id
                  ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white shadow-glow-teal'
                  : 'bg-white dark:bg-navy-900 text-slate-600 dark:text-slate-300 hover:text-navy-900 dark:hover:text-white border border-slate-200 dark:border-navy-800 shadow-sm'
              }`}
            >
              {persona.role}: {persona.title.split('&')[0]}
            </button>
          ))}
        </div>

        {/* Tab Content Box */}
        <div className="bg-white dark:bg-navy-900 rounded-2xl p-8 lg:p-10 border border-slate-200 dark:border-navy-800 shadow-medical-card dark:shadow-medical-card-dark">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            
            {/* Left: Persona Details & Quote */}
            <div className="lg:col-span-6 space-y-5">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-teal-500/10 text-teal-600 dark:text-cyan-300 font-mono font-bold flex items-center justify-center text-lg border border-teal-500/30">
                  {activePersona.avatarText}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-navy-900 dark:text-white">{activePersona.title}</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{activePersona.organization}</p>
                </div>
              </div>

              <blockquote className="text-base text-slate-700 dark:text-slate-200 italic border-l-2 border-teal-500 pl-4 py-1 leading-relaxed">
                "{activePersona.quote}"
              </blockquote>

              <div className="inline-block px-3 py-1 rounded-md bg-slate-50 dark:bg-navy-950 border border-teal-500/30 text-xs font-mono text-teal-700 dark:text-cyan-300">
                Core Value: {activePersona.primaryFeatureHook}
              </div>
            </div>

            {/* Right: Pain vs Gain Matrix */}
            <div className="lg:col-span-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Pain points */}
              <div className="bg-slate-50 dark:bg-navy-950 rounded-xl p-5 border border-rose-200 dark:border-rose-950/60">
                <h4 className="text-xs font-mono uppercase tracking-wider text-rose-600 dark:text-rose-400 font-bold mb-3 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                  Key Pains Eliminated
                </h4>
                <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
                  {activePersona.keyPains.map((pain, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <X className="w-3.5 h-3.5 text-rose-500 shrink-0 mt-0.5" />
                      <span>{pain}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Outcomes */}
              <div className="bg-slate-50 dark:bg-navy-950 rounded-xl p-5 border border-emerald-200 dark:border-emerald-950/60">
                <h4 className="text-xs font-mono uppercase tracking-wider text-emerald-600 dark:text-emerald-400 font-bold mb-3 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  Measured Clinical Outcomes
                </h4>
                <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
                  {activePersona.keyOutcomes.map((outcome, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                      <span>{outcome}</span>
                    </li>
                  ))}
                </ul>
              </div>

            </div>

          </div>
        </div>

      </div>
    </section>
  );
};
