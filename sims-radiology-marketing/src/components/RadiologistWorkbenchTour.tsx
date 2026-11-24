import React, { useState } from 'react';
import { DicomMockViewer } from './DicomMockViewer';
import { 
  Eye, 
  Sparkles, 
  Play, 
  Layers, 
  ExternalLink, 
  Sliders, 
  ShieldCheck, 
  Mic, 
  CheckCircle2, 
  ArrowRight,
  Maximize2
} from 'lucide-react';

export const RadiologistWorkbenchTour: React.FC = () => {
  const [activeFeature, setActiveFeature] = useState<'dicom' | 'shap' | 'voice'>('dicom');
  const [showFullDemo, setShowFullDemo] = useState(false);

  return (
    <div className="bg-gradient-to-br from-navy-900 via-navy-850 to-navy-900 rounded-3xl border border-teal-500/30 p-6 sm:p-8 text-white shadow-glow-teal relative overflow-hidden space-y-6">
      
      {/* Background glow node */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-teal-500/10 rounded-full blur-[100px] pointer-events-none"></div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-navy-700/80">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-teal-500/20 text-cyan-300">
              <Sparkles className="w-4 h-4" />
            </span>
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-300">
              Self-Guided Interactive Sandbox Tour
            </span>
          </div>
          <h4 className="text-xl font-extrabold text-white">
            The Radiologist Workbench Experience
          </h4>
        </div>

        <button
          onClick={() => setShowFullDemo(!showFullDemo)}
          className="px-4 py-2 rounded-xl text-xs font-bold text-navy-950 bg-gradient-to-r from-teal-400 to-cyan-400 hover:from-teal-300 hover:to-cyan-300 transition flex items-center gap-1.5 shrink-0"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>{showFullDemo ? 'Close Live Viewport' : 'Launch Interactive Sandbox'}</span>
        </button>
      </div>

      <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-2xl">
        Explore how reporting radiologists interact with our zero-footprint web viewer, review automated SHAP explainability attributions, and dictate structured findings with natural voice commands.
      </p>

      {/* Feature Navigation Switcher */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[
          {
            id: 'dicom',
            title: '01. A2UI Reactive Viewport',
            desc: 'Multi-slice axial scroller with CT/MRI windowing (Brain, Subdural, Bone).'
          },
          {
            id: 'shap',
            title: '02. SHAP Attribution Layer',
            desc: 'Transparent lesion heatmaps with quantified statistical attribution.'
          },
          {
            id: 'voice',
            title: '03. Voice Structured Reporting',
            desc: 'Natural voice commands and one-click radiologist attestation barrier.'
          }
        ].map(feat => {
          const isSelected = activeFeature === feat.id;
          return (
            <div
              key={feat.id}
              onClick={() => {
                setActiveFeature(feat.id as any);
                setShowFullDemo(true);
              }}
              className={`p-3.5 rounded-xl border cursor-pointer transition text-xs space-y-1 ${
                isSelected
                  ? 'bg-teal-500/10 border-teal-400 shadow-glow-teal ring-1 ring-teal-400'
                  : 'bg-navy-950/60 border-navy-700/80 hover:border-teal-400/50'
              }`}
            >
              <h5 className={`font-bold ${isSelected ? 'text-cyan-300' : 'text-slate-200'}`}>
                {feat.title}
              </h5>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                {feat.desc}
              </p>
            </div>
          );
        })}
      </div>

      {/* Embedded Live Viewport when toggled */}
      {showFullDemo && (
        <div className="pt-4 animate-fadeIn">
          <div className="rounded-2xl border border-teal-500/40 p-4 bg-navy-950/90 shadow-2xl">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-navy-800 text-xs font-mono">
              <span className="text-cyan-300 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                SIMS Diagnostic Workbench Sandbox • Active Session
              </span>
              <span className="text-slate-400">Sample Dataset: ANON-77491-NCCT</span>
            </div>
            <DicomMockViewer />
          </div>
        </div>
      )}

      {/* Safety Reassurance Footer */}
      <div className="pt-2 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 font-mono gap-2">
        <span className="flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
          Zero installation required — runs in modern Chrome, Edge, or Firefox.
        </span>
        <span className="text-cyan-300">
          Powered by Lit & A2UI Web Components
        </span>
      </div>

    </div>
  );
};

export default RadiologistWorkbenchTour;
