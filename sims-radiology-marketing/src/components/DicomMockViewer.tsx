import React, { useState } from 'react';

export const DicomMockViewer: React.FC = () => {
  const [showShap, setShowShap] = useState(true);
  const [activeSlice, setActiveSlice] = useState(24);

  return (
    <div className="rounded-xl overflow-hidden bg-clinical-900 border border-clinical-800 shadow-2xl flex flex-col font-mono text-xs">
      
      {/* Viewport Header Bar */}
      <div className="bg-clinical-950/90 px-4 py-2.5 border-b border-clinical-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
          <span className="font-semibold text-white tracking-wider">STAT RAD-TRIAGE</span>
          <span className="text-slate-500">|</span>
          <span className="text-cyan-400">ANON-77491-NCCT</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[10px] font-bold">
            ACUTE ICH (98.4%)
          </span>
          <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px]">
            NeMo Rails: PASS
          </span>
        </div>
      </div>

      {/* Main Viewport Workspace */}
      <div className="relative aspect-[4/3] bg-black flex items-center justify-center overflow-hidden select-none">
        
        {/* DICOM Grid & Crosshair Lines */}
        <div className="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none"></div>
        <div className="absolute top-1/2 left-0 right-0 h-px bg-cyan-500/10 pointer-events-none"></div>
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-cyan-500/10 pointer-events-none"></div>

        {/* Simulated Brain CT Axial Scan SVG */}
        <svg viewBox="0 0 400 300" className="w-full h-full p-4">
          <defs>
            {/* Brain tissue gradient */}
            <radialGradient id="cranium" cx="50%" cy="50%" r="50%">
              <stop offset="60%" stopColor="#1e293b" stopOpacity="0.8"/>
              <stop offset="90%" stopColor="#334155" stopOpacity="0.95"/>
              <stop offset="98%" stopColor="#94a3b8" stopOpacity="1"/>
              <stop offset="100%" stopColor="#cbd5e1" stopOpacity="1"/>
            </radialGradient>
            {/* SHAP Heatmap Gradient */}
            <radialGradient id="shapHeat" cx="62%" cy="42%" r="20%">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.85"/>
              <stop offset="50%" stopColor="#f59e0b" stopOpacity="0.5"/>
              <stop offset="90%" stopColor="#06b6d4" stopOpacity="0.15"/>
              <stop offset="100%" stopColor="transparent" stopOpacity="0"/>
            </radialGradient>
          </defs>

          {/* Cranium Skull Boundary */}
          <ellipse cx="200" cy="150" rx="140" ry="115" fill="url(#cranium)" stroke="#cbd5e1" strokeWidth="3"/>
          
          {/* Brain Parenchyma / Ventricles */}
          <path d="M175 130 Q185 110 200 130 Q215 110 225 130 Q200 170 175 130" fill="#0f172a" stroke="#475569" strokeWidth="1"/>
          <path d="M185 160 Q200 180 215 160" stroke="#475569" strokeWidth="1.5" fill="none"/>
          <path d="M200 65 L200 235" stroke="#334155" strokeWidth="1" strokeDasharray="2 3"/>

          {/* Pathological Density (Hyperdensity in Right Parietal/Temporal) */}
          <path d="M235 115 Q255 120 250 145 Q235 155 228 135 Z" fill="#e2e8f0" opacity="0.9"/>

          {/* SHAP Attribution Heatmap Overlay */}
          {showShap && (
            <g className="transition-opacity duration-300">
              <circle cx="240" cy="135" r="45" fill="url(#shapHeat)" />
              {/* Bounding Box */}
              <rect x="220" y="105" width="46" height="52" fill="none" stroke="#f43f5e" strokeWidth="1.5" strokeDasharray="3 2"/>
              <text x="222" y="100" fill="#f43f5e" fontSize="9" fontWeight="bold">ICH Risk: 0.984</text>
            </g>
          )}

          {/* DICOM On-Screen Annotations (Corner tags) */}
          <text x="25" y="45" fill="#38bdf8" fontSize="10">HOSP: SIMS MEMORIAL</text>
          <text x="25" y="60" fill="#94a3b8" fontSize="9">MOD: CT | HEAD NON-CON</text>
          <text x="25" y="75" fill="#94a3b8" fontSize="9">KV: 120 | mA: 280</text>
          
          <text x="375" y="45" textAnchor="end" fill="#38bdf8" fontSize="10">SER: 002 | SL: {activeSlice}/48</text>
          <text x="375" y="60" textAnchor="end" fill="#94a3b8" fontSize="9">THICK: 2.5 mm</text>
          <text x="375" y="75" textAnchor="end" fill="#94a3b8" fontSize="9">W: 80 L: 40</text>

          <text x="25" y="270" fill="#94a3b8" fontSize="9">AGENT: LangGraph DeepAgent-Neuro</text>
          <text x="375" y="270" textAnchor="end" fill="#10b981" fontSize="9">FHIR CORE R4 SYNCHRONIZED</text>
        </svg>

        {/* Scan line simulation */}
        <div className="absolute inset-x-0 h-1 bg-cyan-400/40 blur-[1px] animate-scanline pointer-events-none"></div>

      </div>

      {/* Control Footer */}
      <div className="bg-clinical-950 p-3 border-t border-clinical-800 space-y-2">
        <div className="flex items-center justify-between text-[11px]">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowShap(!showShap)}
              className={`px-2.5 py-1 rounded font-medium transition ${
                showShap 
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' 
                  : 'bg-clinical-900 text-slate-400 border border-clinical-800'
              }`}
            >
              {showShap ? '✓ SHAP XAI Layer: ON' : '○ SHAP XAI Layer: OFF'}
            </button>
            <span className="text-slate-400">Attribution: Right Parenchymal Hyperdensity</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-500">Slice:</span>
            <input 
              type="range" 
              min="1" 
              max="48" 
              value={activeSlice} 
              onChange={(e) => setActiveSlice(Number(e.target.value))}
              className="w-24 accent-cyan-400"
            />
            <span className="text-cyan-300 w-8 text-right">{activeSlice}</span>
          </div>
        </div>

        {/* Agent pipeline breadcrumb */}
        <div className="pt-2 border-t border-clinical-900 flex items-center justify-between text-[10px] text-slate-400">
          <div className="flex items-center gap-1.5 overflow-x-auto py-0.5">
            <span className="text-emerald-400 font-semibold">PACS Ingest (0.3s)</span>
            <span>→</span>
            <span className="text-emerald-400 font-semibold">PyDICOM Extract (0.2s)</span>
            <span>→</span>
            <span className="text-cyan-400 font-semibold">Sub-Agent Triage (0.6s)</span>
            <span>→</span>
            <span className="text-emerald-400 font-semibold">NeMo Guardrails (0.1s)</span>
            <span>→</span>
            <span className="text-amber-400 font-semibold">STAT Worklist Pushed</span>
          </div>
          <span className="text-slate-500 hidden sm:inline">Total Latency: 1.2s</span>
        </div>
      </div>

    </div>
  );
};
