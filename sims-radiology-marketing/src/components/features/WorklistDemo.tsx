import React, { useState } from 'react';
import { 
  ListFilter, 
  Clock, 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  UserCheck, 
  Layers, 
  Flame, 
  Eye, 
  ArrowUpDown 
} from 'lucide-react';

export const WorklistDemo: React.FC = () => {
  const [modalityFilter, setModalityFilter] = useState<'ALL' | 'CT' | 'MR' | 'XR'>('ALL');
  const [selectedCaseId, setSelectedCaseId] = useState<string>('ACC-9921');

  const worklistData = [
    {
      id: 'ACC-9921',
      patientId: 'ANON-77491',
      patientReconciled: true,
      modality: 'CT',
      exam: 'CT HEAD W/O CONTRAST',
      priority: 'STAT',
      waitTime: '04:12',
      targetTurnaround: '15:00',
      status: 'Agent Ingested (42s ago)',
      findingsTag: 'Suspected Acute ICH (98.4%)',
      acuityScore: 98,
      location: 'Emergency Dept (ED-Resus-1)',
      reconciliationDetails: 'Matched: MRN-88219 • Sectra PACS & Epic EHR Aligned'
    },
    {
      id: 'ACC-9922',
      patientId: 'ANON-41209',
      patientReconciled: true,
      modality: 'XR',
      exam: 'XR CHEST 1 VIEW PORTABLE',
      priority: 'STAT',
      waitTime: '09:45',
      targetTurnaround: '20:00',
      status: 'Agent Ingested (1m ago)',
      findingsTag: 'Tension Pneumothorax (R)',
      acuityScore: 94,
      location: 'Cardiothoracic ICU (Bed 12)',
      reconciliationDetails: 'Matched: MRN-55104 • Philips PACS & Cerner Aligned'
    },
    {
      id: 'ACC-9923',
      patientId: 'ANON-33019',
      patientReconciled: true,
      modality: 'CT',
      exam: 'CTA CHEST W/ CONTRAST (PE)',
      priority: 'URGENT',
      waitTime: '21:30',
      targetTurnaround: '45:00',
      status: 'Agent Ingested (6m ago)',
      findingsTag: 'RLL Segmental PE Present',
      acuityScore: 78,
      location: 'Inpatient Stepdown (4 West)',
      reconciliationDetails: 'Matched: MRN-10944 • GE Centricity Aligned'
    },
    {
      id: 'ACC-9924',
      patientId: 'ANON-60193',
      patientReconciled: true,
      modality: 'MR',
      exam: 'MRI BRAIN DIFFUSION / STROKE',
      priority: 'URGENT',
      waitTime: '28:15',
      targetTurnaround: '60:00',
      status: 'Agent Ingested (12m ago)',
      findingsTag: 'DWI Acute Restriction (+)',
      acuityScore: 72,
      location: 'Comprehensive Stroke Unit',
      reconciliationDetails: 'Matched: MRN-88902 • Sectra PACS & Epic EHR Aligned'
    },
    {
      id: 'ACC-9925',
      patientId: 'ANON-11029',
      patientReconciled: true,
      modality: 'XR',
      exam: 'XR RIGHT KNEE 3 VIEWS',
      priority: 'ROUTINE',
      waitTime: '48:10',
      targetTurnaround: '120:00',
      status: 'Standard Queue',
      findingsTag: 'No acute fracture detected',
      acuityScore: 18,
      location: 'Outpatient Ortho Clinic',
      reconciliationDetails: 'Matched: MRN-44910 • Synapse Aligned'
    }
  ];

  const filteredCases = modalityFilter === 'ALL' 
    ? worklistData 
    : worklistData.filter(c => c.modality === modalityFilter);

  const selectedCase = worklistData.find(c => c.id === selectedCaseId) || worklistData[0];

  return (
    <div className="space-y-6">
      
      {/* Module Overview Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-teal-500/5 dark:bg-navy-850/60 border border-teal-500/20">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-teal-500/10 text-teal-600 dark:text-cyan-400">
              <Layers className="w-4 h-4" />
            </span>
            <span className="font-bold text-sm text-navy-900 dark:text-white">
              Unified Multi-Modality Worklist (CT, MRI, X-Ray)
            </span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            A real-time dynamic queue where autonomous sub-agents promote high-acuity life threats to top-of-list within seconds, regardless of arrival order.
          </p>
        </div>

        {/* Modality Filter Pills */}
        <div className="flex items-center gap-1 bg-slate-200/80 dark:bg-navy-950 p-1 rounded-xl text-xs font-mono font-semibold self-start sm:self-auto">
          {(['ALL', 'CT', 'MR', 'XR'] as const).map(mod => (
            <button
              key={mod}
              onClick={() => setModalityFilter(mod)}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                modalityFilter === mod
                  ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white font-bold shadow-glow-teal'
                  : 'text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white'
              }`}
            >
              {mod}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Worklist Table & Case Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left (8 Cols): Worklist Table */}
        <div className="lg:col-span-8 bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-medical-card dark:shadow-medical-card-dark overflow-hidden">
          
          <div className="p-4 border-b border-slate-200 dark:border-navy-800 flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <ArrowUpDown className="w-3.5 h-3.5 text-teal-500" />
              <span className="font-bold">Acuity-Sorted Queue: {filteredCases.length} Studies Active</span>
            </div>
            <span className="text-[11px] text-teal-600 dark:text-cyan-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-ping"></span>
              Live DICOM C-STORE Stream
            </span>
          </div>

          <div className="divide-y divide-slate-200 dark:divide-navy-800">
            {filteredCases.map(item => {
              const isSelected = selectedCaseId === item.id;
              const isStat = item.priority === 'STAT';
              const isUrgent = item.priority === 'URGENT';

              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedCaseId(item.id)}
                  className={`p-4 cursor-pointer transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    isSelected
                      ? 'bg-teal-500/10 dark:bg-navy-850 border-l-4 border-l-teal-500'
                      : 'hover:bg-slate-50 dark:hover:bg-navy-850/50'
                  }`}
                >
                  {/* Left: Badges & Exam Info */}
                  <div className="space-y-1.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                        isStat 
                          ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30' 
                          : isUrgent 
                            ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30'
                            : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30'
                      }`}>
                        {item.priority}
                      </span>
                      
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-navy-100 dark:bg-navy-800 text-navy-800 dark:text-slate-200">
                        {item.modality}
                      </span>

                      <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                        {item.id}
                      </span>

                      {/* Automated Patient Reconciliation Badge */}
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                        <UserCheck className="w-3 h-3" />
                        Reconciled
                      </span>
                    </div>

                    <h5 className="font-bold text-sm text-navy-900 dark:text-white">
                      {item.exam}
                    </h5>

                    <p className="text-xs text-rose-600 dark:text-rose-400 font-mono font-semibold">
                      AI Triage Alert: {item.findingsTag}
                    </p>
                  </div>

                  {/* Right: Turnaround Time Counters */}
                  <div className="sm:text-right shrink-0 font-mono space-y-1">
                    <div className="flex items-center sm:justify-end gap-1.5 text-xs text-slate-700 dark:text-slate-300">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>Wait: <strong className={isStat ? 'text-rose-500' : 'text-slate-900 dark:text-white'}>{item.waitTime}</strong></span>
                      <span className="text-slate-400">/ {item.targetTurnaround}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block">
                      Location: {item.location}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

        </div>

        {/* Right (4 Cols): Case Detail Inspector */}
        <div className="lg:col-span-4 bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 p-5 shadow-medical-card dark:shadow-medical-card-dark space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-navy-800">
            <h4 className="font-bold text-navy-900 dark:text-white text-sm">
              Study Inspector
            </h4>
            <span className="text-xs font-mono text-teal-600 dark:text-cyan-400 font-bold">
              {selectedCase.id}
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-500 dark:text-slate-400 font-mono block text-[11px]">PATIENT IDENTIFIER:</span>
              <p className="font-mono font-bold text-navy-900 dark:text-white">{selectedCase.patientId}</p>
              <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
                ✓ {selectedCase.reconciliationDetails}
              </p>
            </div>

            <div>
              <span className="text-slate-500 dark:text-slate-400 font-mono block text-[11px]">AI ACUITY SCORE:</span>
              <div className="flex items-center gap-3 mt-1">
                <div className="flex-1 bg-slate-200 dark:bg-navy-950 rounded-full h-2.5 overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-teal-500 via-amber-500 to-rose-500 rounded-full"
                    style={{ width: `${selectedCase.acuityScore}%` }}
                  ></div>
                </div>
                <span className="font-mono font-extrabold text-navy-900 dark:text-white">
                  {selectedCase.acuityScore}/100
                </span>
              </div>
            </div>

            <div>
              <span className="text-slate-500 dark:text-slate-400 font-mono block text-[11px]">DIAGNOSTIC FINDING ALERT:</span>
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 font-semibold mt-1">
                {selectedCase.findingsTag}
              </div>
            </div>

            <div>
              <span className="text-slate-500 dark:text-slate-400 font-mono block text-[11px]">PIPELINE STATUS:</span>
              <p className="text-slate-700 dark:text-slate-300 font-mono">{selectedCase.status}</p>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-200 dark:border-navy-800">
            <button className="w-full py-2.5 rounded-lg text-xs font-bold text-white bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 shadow-glow-teal transition">
              Open in Diagnostic Viewer
            </button>
          </div>
        </div>

      </div>

    </div>
  );
};

export default WorklistDemo;
