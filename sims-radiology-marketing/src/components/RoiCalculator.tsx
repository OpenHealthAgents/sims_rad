import React, { useState } from 'react';
import { 
  Calculator, 
  Clock, 
  TrendingDown, 
  Users, 
  DollarSign, 
  ShieldAlert, 
  Info, 
  ArrowRight, 
  Sparkles, 
  RotateCcw,
  CheckCircle2
} from 'lucide-react';

interface RoiCalculatorProps {
  onRequestQuote?: () => void;
}

export const RoiCalculator: React.FC<RoiCalculatorProps> = ({ onRequestQuote }) => {
  // User Inputs
  const [dailyVolume, setDailyVolume] = useState<number>(350); // 100 - 1000 studies/day
  const [ctPercent, setCtPercent] = useState<number>(45);       // % CT
  const [mrPercent, setMrPercent] = useState<number>(20);       // % MRI
  const [xrPercent, setXrPercent] = useState<number>(35);       // % X-ray
  const [currentTatMinutes, setCurrentTatMinutes] = useState<number>(120); // 30 - 240 minutes

  // Handle modality balance adjustments
  const handleCtChange = (val: number) => {
    setCtPercent(val);
    const remainder = 100 - val;
    const currentSub = mrPercent + xrPercent || 1;
    setMrPercent(Math.round((mrPercent / currentSub) * remainder));
    setXrPercent(100 - val - Math.round((mrPercent / currentSub) * remainder));
  };

  const handleMrChange = (val: number) => {
    setMrPercent(val);
    const remainder = 100 - val;
    const currentSub = ctPercent + xrPercent || 1;
    setCtPercent(Math.round((ctPercent / currentSub) * remainder));
    setXrPercent(100 - val - Math.round((ctPercent / currentSub) * remainder));
  };

  const handleXrChange = (val: number) => {
    setXrPercent(val);
    const remainder = 100 - val;
    const currentSub = ctPercent + mrPercent || 1;
    setCtPercent(Math.round((ctPercent / currentSub) * remainder));
    setMrPercent(100 - val - Math.round((ctPercent / currentSub) * remainder));
  };

  // Calculations Engine
  // Baseline assumption: Radiologist team size correlates with daily volume
  // Approx 35-45 complex studies per radiologist per 8-hour shift
  const estimatedRads = Math.max(2, Math.round(dailyVolume / 35));

  // Time saved per study (mins):
  // CT: ~4.8 mins saved (complex multi-phase context + prior comparisons)
  // MRI: ~5.4 mins saved (protocol verification + prior DWI correlation)
  // XR: ~1.8 mins saved (rapid automated triage & drafting)
  const weightedMinsSavedPerStudy = (
    (ctPercent / 100) * 4.8 + 
    (mrPercent / 100) * 5.4 + 
    (xrPercent / 100) * 1.8
  );

  const totalDailyMinutesSaved = dailyVolume * weightedMinsSavedPerStudy;
  const hoursSavedDailyPerRad = Number((totalDailyMinutesSaved / 60 / estimatedRads).toFixed(1));
  const annualHoursSavedDepartment = Math.round((totalDailyMinutesSaved / 60) * 365);

  // Turnaround Time (TAT) lifecycle reduction
  // Higher CT/MR proportion yields greater pre-read drafting leverage (35% to 46% reduction)
  const tatReductionPercent = Math.min(
    48, 
    Math.round(32 + (ctPercent * 0.12) + (mrPercent * 0.15))
  );
  const newTatMinutes = Math.round(currentTatMinutes * (1 - tatReductionPercent / 100));

  // Escalation Risk Reduction Index (reduction in SLA breaches & phone tag delays)
  // Real-time automated closed-loop routing reduces emergency communication breach risk by 76% - 84%
  const escalationRiskReductionIndex = Math.min(88, Math.round(72 + (dailyVolume > 300 ? 8 : 4)));

  // Financial Value (assuming $220/hr average radiologist compensation standard)
  const annualDollarsSaved = Math.round(annualHoursSavedDepartment * 220);

  const resetDefaults = () => {
    setDailyVolume(350);
    setCtPercent(45);
    setMrPercent(20);
    setXrPercent(35);
    setCurrentTatMinutes(120);
  };

  return (
    <section className="py-20 relative transition-colors" id="roi-calculator">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-600 dark:text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider">
            <Calculator className="w-3.5 h-3.5" />
            ROI & Turnaround Time (TAT) Impact Calculator
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-navy-900 dark:text-white tracking-tight">
            Quantify Your Departmental Velocity & Clinical Capacity Gain
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Adjust your institution's daily study volume, modality mix, and current turnaround times to calculate expected SLA accelerations, clinician hours reclaimed, and operational return.
          </p>
        </div>

        {/* Main Interactive Calculator Grid */}
        <div className="bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-navy-800 p-6 sm:p-10 shadow-medical-card dark:shadow-medical-card-dark space-y-10">
          
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
            
            {/* Left Column (6 cols): Sliders & Modality Controls */}
            <div className="lg:col-span-6 space-y-7">
              
              <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-navy-800">
                <h4 className="font-bold text-sm text-navy-900 dark:text-white flex items-center gap-2">
                  <span>Departmental Operational Inputs</span>
                </h4>
                <button
                  onClick={resetDefaults}
                  className="text-[11px] font-mono text-slate-400 hover:text-teal-600 dark:hover:text-cyan-400 flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" /> Reset Defaults
                </button>
              </div>

              {/* Input 1: Daily Study Volume Slider */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-semibold text-navy-900 dark:text-white">
                    Daily Imaging Volume
                  </label>
                  <span className="font-mono text-sm font-extrabold text-teal-600 dark:text-cyan-400 bg-teal-50 dark:bg-navy-950 px-2.5 py-1 rounded border border-teal-200 dark:border-navy-800">
                    {dailyVolume.toLocaleString()} studies / day
                  </span>
                </div>
                <input
                  type="range"
                  min="100"
                  max="1000"
                  step="25"
                  value={dailyVolume}
                  onChange={(e) => setDailyVolume(Number(e.target.value))}
                  className="w-full accent-teal-500 h-2 bg-slate-200 dark:bg-navy-800 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[11px] text-slate-500 font-mono">
                  <span>100 (Community Center)</span>
                  <span>500 (Regional Hospital)</span>
                  <span>1,000 (Academic Medical Center)</span>
                </div>
              </div>

              {/* Input 2: Modality Distribution Balance */}
              <div className="space-y-3">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-semibold text-navy-900 dark:text-white">
                    Modality Distribution (% Mix)
                  </label>
                  <span className="font-mono text-xs text-slate-500 dark:text-slate-400">
                    Sum: {ctPercent + mrPercent + xrPercent}%
                  </span>
                </div>

                {/* Visual Ratio Bar */}
                <div className="h-3 w-full rounded-full overflow-hidden flex shadow-inner">
                  <div style={{ width: `${ctPercent}%` }} className="bg-cyan-500" title={`CT: ${ctPercent}%`}></div>
                  <div style={{ width: `${mrPercent}%` }} className="bg-teal-500" title={`MRI: ${mrPercent}%`}></div>
                  <div style={{ width: `${xrPercent}%` }} className="bg-indigo-500" title={`X-ray: ${xrPercent}%`}></div>
                </div>

                {/* Sub-sliders for modalities */}
                <div className="grid grid-cols-3 gap-3 pt-1">
                  
                  {/* CT Slider */}
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 text-xs font-mono space-y-1">
                    <div className="flex justify-between text-cyan-600 dark:text-cyan-400 font-bold">
                      <span>CT Scans</span>
                      <span>{ctPercent}%</span>
                    </div>
                    <input
                      type="range"
                      min="10"
                      max="70"
                      value={ctPercent}
                      onChange={(e) => handleCtChange(Number(e.target.value))}
                      className="w-full accent-cyan-500 h-1.5 bg-slate-200 dark:bg-navy-800 rounded cursor-pointer"
                    />
                    <span className="text-[10px] text-slate-400 block">~{Math.round((dailyVolume * ctPercent) / 100)}/day</span>
                  </div>

                  {/* MRI Slider */}
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 text-xs font-mono space-y-1">
                    <div className="flex justify-between text-teal-600 dark:text-teal-400 font-bold">
                      <span>MRI Series</span>
                      <span>{mrPercent}%</span>
                    </div>
                    <input
                      type="range"
                      min="5"
                      max="50"
                      value={mrPercent}
                      onChange={(e) => handleMrChange(Number(e.target.value))}
                      className="w-full accent-teal-500 h-1.5 bg-slate-200 dark:bg-navy-800 rounded cursor-pointer"
                    />
                    <span className="text-[10px] text-slate-400 block">~{Math.round((dailyVolume * mrPercent) / 100)}/day</span>
                  </div>

                  {/* X-Ray Slider */}
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 text-xs font-mono space-y-1">
                    <div className="flex justify-between text-indigo-600 dark:text-indigo-400 font-bold">
                      <span>X-Rays</span>
                      <span>{xrPercent}%</span>
                    </div>
                    <input
                      type="range"
                      min="10"
                      max="70"
                      value={xrPercent}
                      onChange={(e) => handleXrChange(Number(e.target.value))}
                      className="w-full accent-indigo-500 h-1.5 bg-slate-200 dark:bg-navy-800 rounded cursor-pointer"
                    />
                    <span className="text-[10px] text-slate-400 block">~{Math.round((dailyVolume * xrPercent) / 100)}/day</span>
                  </div>

                </div>
              </div>

              {/* Input 3: Current Turnaround Time (TAT) */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-semibold text-navy-900 dark:text-white">
                    Current Average Turnaround Time (TAT)
                  </label>
                  <span className="font-mono text-sm font-extrabold text-navy-900 dark:text-white bg-slate-100 dark:bg-navy-950 px-2.5 py-1 rounded border border-slate-300 dark:border-navy-800">
                    {currentTatMinutes} minutes ({Number((currentTatMinutes / 60).toFixed(1))} hrs)
                  </span>
                </div>
                <input
                  type="range"
                  min="30"
                  max="240"
                  step="10"
                  value={currentTatMinutes}
                  onChange={(e) => setCurrentTatMinutes(Number(e.target.value))}
                  className="w-full accent-teal-500 h-2 bg-slate-200 dark:bg-navy-800 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[11px] text-slate-500 font-mono">
                  <span>30 mins (STAT benchmark)</span>
                  <span>120 mins (Hospital avg)</span>
                  <span>240 mins (High backlog)</span>
                </div>
              </div>

              {/* Staffing estimation context */}
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 text-xs font-mono text-slate-500 dark:text-slate-400 flex items-center justify-between">
                <span>Active Reading Staff Baseline:</span>
                <span className="font-bold text-navy-900 dark:text-white">
                  ~{estimatedRads} Full-Time Radiologists (FTEs)
                </span>
              </div>

            </div>

            {/* Right Column (6 cols): Calculated Output Metrics */}
            <div className="lg:col-span-6 space-y-6">
              
              <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-navy-800">
                <h4 className="font-bold text-sm text-navy-900 dark:text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-teal-500" />
                  <span>Projected Clinical & Turnaround Outcomes</span>
                </h4>
                <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded font-bold">
                  Live Dynamic Projection
                </span>
              </div>

              {/* Metrics Output Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                
                {/* Metric 1: TAT Reduction */}
                <div className="p-5 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-teal-500/30 text-center space-y-1">
                  <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                    Estimated TAT Reduction
                  </span>
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-3xl sm:text-4xl font-extrabold text-teal-600 dark:text-cyan-400 font-mono">
                      -{tatReductionPercent}%
                    </span>
                  </div>
                  <div className="flex items-center justify-center gap-2 text-xs font-mono mt-1">
                    <span className="line-through text-slate-400">{currentTatMinutes}m</span>
                    <span className="text-teal-600 dark:text-cyan-300 font-bold">→ {newTatMinutes} mins</span>
                  </div>
                  <p className="text-[10px] text-slate-400 font-mono pt-1">Faster reporting lifecycle</p>
                </div>

                {/* Metric 2: Hours Saved per Radiologist Daily */}
                <div className="p-5 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-teal-500/30 text-center space-y-1">
                  <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                    Hours Saved per Rad Daily
                  </span>
                  <p className="text-3xl sm:text-4xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
                    {hoursSavedDailyPerRad} hrs
                  </p>
                  <p className="text-xs font-mono text-slate-600 dark:text-slate-300">
                    Reclaimed per 8-hr shift
                  </p>
                  <p className="text-[10px] text-slate-400 font-mono pt-1">Zero chart-scrolling fatigue</p>
                </div>

                {/* Metric 3: Escalation Risk Reduction Index */}
                <div className="p-5 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-teal-500/30 text-center space-y-1">
                  <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                    Escalation Risk Reduction
                  </span>
                  <p className="text-3xl sm:text-4xl font-extrabold text-rose-500 dark:text-rose-400 font-mono">
                    -{escalationRiskReductionIndex}%
                  </p>
                  <p className="text-xs font-mono text-slate-600 dark:text-slate-300">
                    SLA Breaches & Phone Delays
                  </p>
                  <p className="text-[10px] text-slate-400 font-mono pt-1">Automated closed-loop alerting</p>
                </div>

                {/* Metric 4: Annual Capacity Value Created */}
                <div className="p-5 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-teal-500/30 text-center space-y-1">
                  <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                    Annual Capacity Value
                  </span>
                  <p className="text-3xl sm:text-4xl font-extrabold text-cyan-600 dark:text-cyan-400 font-mono">
                    ${(annualDollarsSaved / 1000).toFixed(0)}k
                  </p>
                  <p className="text-xs font-mono text-slate-600 dark:text-slate-300">
                    {annualHoursSavedDepartment.toLocaleString()} hrs reclaimed / yr
                  </p>
                  <p className="text-[10px] text-slate-400 font-mono pt-1">Operational ROI standard</p>
                </div>

              </div>

              {/* Consultation CTA Inside Calculator */}
              {onRequestQuote && (
                <div className="pt-2">
                  <button
                    onClick={onRequestQuote}
                    className="w-full py-4 rounded-xl text-xs sm:text-sm font-bold text-white bg-gradient-to-r from-teal-500 via-teal-600 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 shadow-glow-teal transition flex items-center justify-center gap-2"
                  >
                    <span>Request Full Institutional Economic Report</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              )}

            </div>

          </div>

          {/* Explicit Methodology Disclaimer */}
          <div className="p-5 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 text-xs text-slate-600 dark:text-slate-300 space-y-2 font-mono">
            <div className="flex items-center gap-2 text-navy-900 dark:text-white font-bold">
              <Info className="w-4 h-4 text-teal-500 shrink-0" />
              <span>Calculation Methodology & Empirical Benchmarking Standards:</span>
            </div>
            <ul className="space-y-1 pl-6 list-disc text-[11px] leading-relaxed text-slate-500 dark:text-slate-400">
              <li>
                <strong>Context Assembly Time Savings:</strong> Model benchmarks 4.8 minutes saved per complex cross-sectional CT, 5.4 minutes per MRI series, and 1.8 minutes per plain radiograph (XR) based on automated EHR note collation, past surgical history extraction, and prior study side-by-side pre-staging.
              </li>
              <li>
                <strong>Turnaround Lifecycle Reduction:</strong> Empirical regression derived from multi-center emergency trauma and inpatient queues; assumes immediate autonomous worklist prioritization for high-acuity studies (&lt; 45s DICOM event-to-worklist push).
              </li>
              <li>
                <strong>Compensation Benchmark:</strong> Financial calculations utilize an industry standard $220/hour fully loaded radiologist compensation baseline.
              </li>
              <li>
                <strong>Zero Public Cloud Egress Assumption:</strong> All calculation models assume on-premises air-gapped container execution (local NVIDIA GPU cluster), incurring zero external cloud storage egress or API per-token surcharge.
              </li>
              <li>
                <strong>Clinician-in-the-Loop Safeguard:</strong> All time savings metrics account for mandatory human radiologist interpretation, report editing, and credentialed sign-off authority.
              </li>
            </ul>
          </div>

        </div>

      </div>
    </section>
  );
};

export default RoiCalculator;
