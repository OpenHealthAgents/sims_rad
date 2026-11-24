import React, { useState } from 'react';
import { 
  Building2, 
  User, 
  Mail, 
  Phone, 
  CheckCircle2, 
  ArrowRight, 
  ArrowLeft, 
  Layers, 
  ShieldCheck, 
  Calendar, 
  Clock, 
  AlertCircle,
  FileCheck,
  Server,
  Lock,
  Sparkles
} from 'lucide-react';

interface DemoRequestFormProps {
  onSuccess?: () => void;
}

export const DemoRequestForm: React.FC<DemoRequestFormProps> = ({ onSuccess }) => {
  // Current active step: 1, 2, or 3
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);
  const [ticketId, setTicketId] = useState<string>('');

  // Form Fields
  const [formData, setFormData] = useState({
    // Step 1: Hospital & Contact Information
    hospitalName: '',
    fullName: '',
    role: 'Radiology Director / Department Chair',
    businessEmail: '',
    phoneNumber: '',

    // Step 2: Department Profile
    dailyVolume: '300 - 600 studies/day',
    modalities: ['CT', 'MRI', 'XR'],
    pacsVendor: 'Sectra',
    ehrSystem: 'Epic Systems',

    // Step 3: Deployment Goals
    deploymentGoals: [
      'Workflow Optimization & Pre-Reads',
      'SLA Breach & Turnaround Time Monitoring',
      'EHR Integration Validation & FHIR R4 Writeback'
    ],
    deploymentTarget: 'Air-Gapped On-Premises (Docker/K8s)',
    notes: ''
  });

  // Validation Errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // List of free email providers to flag for B2B institutional validation
  const freeEmailDomains = [
    'gmail.com',
    'yahoo.com',
    'hotmail.com',
    'outlook.com',
    'aol.com',
    'icloud.com',
    'protonmail.com'
  ];

  const validateStep1 = () => {
    const errs: Record<string, string> = {};

    if (!formData.hospitalName.trim()) {
      errs.hospitalName = 'Hospital or health system name is required.';
    }
    if (!formData.fullName.trim()) {
      errs.fullName = 'Full name and title are required.';
    }

    const emailTrimmed = formData.businessEmail.trim();
    if (!emailTrimmed) {
      errs.businessEmail = 'Work email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailTrimmed)) {
      errs.businessEmail = 'Please provide a valid email format.';
    } else {
      const domain = emailTrimmed.split('@')[1]?.toLowerCase();
      if (domain && freeEmailDomains.includes(domain)) {
        errs.businessEmail = 'Please provide an official hospital, medical school, or institutional email domain.';
      }
    }

    if (!formData.phoneNumber.trim()) {
      errs.phoneNumber = 'Contact phone number is required for pilot coordination.';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const validateStep2 = () => {
    const errs: Record<string, string> = {};
    if (formData.modalities.length === 0) {
      errs.modalities = 'Please select at least one primary imaging modality.';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleNext = () => {
    if (currentStep === 1) {
      if (validateStep1()) setCurrentStep(2);
    } else if (currentStep === 2) {
      if (validateStep2()) setCurrentStep(3);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setErrors({});
      setCurrentStep(currentStep - 1);
    }
  };

  const handleModalityToggle = (mod: string) => {
    setFormData(prev => {
      const exists = prev.modalities.includes(mod);
      const updated = exists 
        ? prev.modalities.filter(m => m !== mod)
        : [...prev.modalities, mod];
      return { ...prev, modalities: updated };
    });
  };

  const handleGoalToggle = (goal: string) => {
    setFormData(prev => {
      const exists = prev.deploymentGoals.includes(goal);
      const updated = exists 
        ? prev.deploymentGoals.filter(g => g !== goal)
        : [...prev.deploymentGoals, goal];
      return { ...prev, deploymentGoals: updated };
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (currentStep === 1 && !validateStep1()) return;
    if (currentStep === 2 && !validateStep2()) return;

    // Generate reference code
    const generatedCode = `SIMS-PILOT-${Math.floor(100000 + Math.random() * 900000)}`;
    setTicketId(generatedCode);
    setIsSubmitted(true);
    onSuccess?.();
  };

  return (
    <div className="bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-navy-800 shadow-medical-card dark:shadow-medical-card-dark overflow-hidden transition-all">
      
      {/* Multi-Step Header / Progress Indicator */}
      {!isSubmitted && (
        <div className="p-6 sm:p-8 bg-slate-50 dark:bg-navy-950 border-b border-slate-200 dark:border-navy-800">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-teal-600 dark:text-cyan-400">
                Institutional Trial Onboarding
              </span>
              <h3 className="text-xl font-extrabold text-navy-900 dark:text-white">
                Request an On-Premises Clinical Pilot
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
              Step {currentStep} of 3
            </span>
          </div>

          {/* Stepper visual bar */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { stepNum: 1, label: 'Hospital & Contact' },
              { stepNum: 2, label: 'Department Profile' },
              { stepNum: 3, label: 'Deployment Goals' },
            ].map((st) => {
              const isPast = currentStep > st.stepNum;
              const isCurrent = currentStep === st.stepNum;
              return (
                <div key={st.stepNum} className="space-y-1.5">
                  <div className={`h-1.5 rounded-full transition-all duration-300 ${
                    isPast || isCurrent 
                      ? 'bg-gradient-to-r from-teal-500 to-cyan-500' 
                      : 'bg-slate-200 dark:bg-navy-800'
                  }`} />
                  <p className={`text-[11px] font-mono font-semibold hidden sm:block ${
                    isCurrent ? 'text-teal-600 dark:text-cyan-400' : 'text-slate-400'
                  }`}>
                    {st.stepNum}. {st.label}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Form Content Area */}
      <div className="p-6 sm:p-10">
        {isSubmitted ? (
          /* Confirmation Screen */
          <div className="space-y-8 py-4">
            
            <div className="text-center space-y-3">
              <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 flex items-center justify-center mx-auto text-2xl font-bold shadow-glow-emerald">
                ✓
              </div>
              <h3 className="text-2xl sm:text-3xl font-extrabold text-navy-900 dark:text-white">
                Hospital Pilot Request Confirmed
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 max-w-xl mx-auto">
                Thank you, <strong>{formData.fullName}</strong>. Your clinical pilot dossier for <strong>{formData.hospitalName}</strong> has been assigned to our Clinical AI Solutions Engineering desk.
              </p>
              <div className="inline-block px-3 py-1 rounded-md bg-teal-500/10 border border-teal-500/30 text-xs font-mono font-bold text-teal-700 dark:text-cyan-300">
                Tracking Reference: {ticketId}
              </div>
            </div>

            {/* Post-Submission Confirmation Steps */}
            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 space-y-4">
              <h4 className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 font-bold">
                Next Steps & Deployment Milestones:
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                
                {/* Milestone 1 */}
                <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="w-6 h-6 rounded-full bg-teal-500/10 text-teal-600 dark:text-cyan-400 text-xs font-bold font-mono flex items-center justify-center">
                      1
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">Within 24 Hours</span>
                  </div>
                  <h5 className="font-bold text-sm text-navy-900 dark:text-white">
                    Technical Discovery Call
                  </h5>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    A 30-minute scoping call with a Clinical Informatics Lead to map PACS C-STORE endpoints and study volumes.
                  </p>
                </div>

                {/* Milestone 2 */}
                <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="w-6 h-6 rounded-full bg-teal-500/10 text-teal-600 dark:text-cyan-400 text-xs font-bold font-mono flex items-center justify-center">
                      2
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">Day 2 to 4</span>
                  </div>
                  <h5 className="font-bold text-sm text-navy-900 dark:text-white">
                    On-Premises Architecture Review
                  </h5>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    Delivery of our standard BAA, Docker Compose network topology manifests, and CISO security documentation.
                  </p>
                </div>

                {/* Milestone 3 */}
                <div className="p-4 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="w-6 h-6 rounded-full bg-teal-500/10 text-teal-600 dark:text-cyan-400 text-xs font-bold font-mono flex items-center justify-center">
                      3
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">Week 1</span>
                  </div>
                  <h5 className="font-bold text-sm text-navy-900 dark:text-white">
                    Synthetic Data Pilot Demo
                  </h5>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    Live demonstration executing your historical de-identified DICOM series through DeepAgents and NeMo rails.
                  </p>
                </div>

              </div>
            </div>

            {/* Reassurance Callout */}
            <div className="p-4 rounded-xl bg-teal-500/5 dark:bg-teal-500/10 border border-teal-500/20 flex items-center gap-3 text-xs text-slate-600 dark:text-slate-300">
              <ShieldCheck className="w-5 h-5 text-teal-500 shrink-0" />
              <span>
                Zero Protected Health Information (PHI) is transmitted or required prior to executing the institutional Business Associate Agreement (BAA).
              </span>
            </div>

          </div>
        ) : (
          /* Multi-Step Form */
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* STEP 1: Hospital & Contact Information */}
            {currentStep === 1 && (
              <div className="space-y-5 animate-fadeIn">
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-1.5">
                      Hospital or Health System Name *
                    </label>
                    <div className="relative">
                      <Building2 className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                      <input
                        type="text"
                        placeholder="e.g. Memorial Academic Health System"
                        value={formData.hospitalName}
                        onChange={(e) => setFormData({ ...formData, hospitalName: e.target.value })}
                        className={`w-full bg-slate-50 dark:bg-navy-950 border rounded-xl pl-10 pr-4 py-3 text-sm text-navy-900 dark:text-white focus:outline-none transition ${
                          errors.hospitalName ? 'border-rose-500 focus:border-rose-500' : 'border-slate-300 dark:border-navy-800 focus:border-teal-500'
                        }`}
                      />
                    </div>
                    {errors.hospitalName && (
                      <p className="text-[11px] text-rose-500 font-mono mt-1 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {errors.hospitalName}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-1.5">
                      Full Name & Academic Title *
                    </label>
                    <div className="relative">
                      <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                      <input
                        type="text"
                        placeholder="e.g. Dr. Marcus Vance, MD"
                        value={formData.fullName}
                        onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                        className={`w-full bg-slate-50 dark:bg-navy-950 border rounded-xl pl-10 pr-4 py-3 text-sm text-navy-900 dark:text-white focus:outline-none transition ${
                          errors.fullName ? 'border-rose-500 focus:border-rose-500' : 'border-slate-300 dark:border-navy-800 focus:border-teal-500'
                        }`}
                      />
                    </div>
                    {errors.fullName && (
                      <p className="text-[11px] text-rose-500 font-mono mt-1 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {errors.fullName}
                      </p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                  <div>
                    <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-1.5">
                      Clinical Role *
                    </label>
                    <select
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                      className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-navy-800 rounded-xl px-3.5 py-3 text-xs text-navy-900 dark:text-white focus:outline-none focus:border-teal-500 transition"
                    >
                      <option value="Radiology Director / Department Chair">Radiology Director / Chair</option>
                      <option value="Staff Radiologist">Staff Radiologist</option>
                      <option value="Chief Medical Officer (CMO)">Chief Medical Officer (CMO)</option>
                      <option value="Hospital CIO / CTO">Hospital CIO / CTO</option>
                      <option value="Chief Information Security Officer (CISO)">CISO / IT Security Lead</option>
                      <option value="PACS / Clinical Informatics Admin">PACS / Imaging Admin</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-1.5">
                      Institutional / Work Email *
                    </label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                      <input
                        type="email"
                        placeholder="mvance@hospital.org"
                        value={formData.businessEmail}
                        onChange={(e) => setFormData({ ...formData, businessEmail: e.target.value })}
                        className={`w-full bg-slate-50 dark:bg-navy-950 border rounded-xl pl-10 pr-4 py-3 text-sm text-navy-900 dark:text-white focus:outline-none transition ${
                          errors.businessEmail ? 'border-rose-500 focus:border-rose-500' : 'border-slate-300 dark:border-navy-800 focus:border-teal-500'
                        }`}
                      />
                    </div>
                    {errors.businessEmail && (
                      <p className="text-[11px] text-rose-500 font-mono mt-1 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3 shrink-0" /> {errors.businessEmail}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-1.5">
                      Phone Number *
                    </label>
                    <div className="relative">
                      <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                      <input
                        type="tel"
                        placeholder="+1 (555) 234-5678"
                        value={formData.phoneNumber}
                        onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
                        className={`w-full bg-slate-50 dark:bg-navy-950 border rounded-xl pl-10 pr-4 py-3 text-sm text-navy-900 dark:text-white focus:outline-none transition ${
                          errors.phoneNumber ? 'border-rose-500 focus:border-rose-500' : 'border-slate-300 dark:border-navy-800 focus:border-teal-500'
                        }`}
                      />
                    </div>
                    {errors.phoneNumber && (
                      <p className="text-[11px] text-rose-500 font-mono mt-1 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {errors.phoneNumber}
                      </p>
                    )}
                  </div>
                </div>

              </div>
            )}

            {/* STEP 2: Department Profile */}
            {currentStep === 2 && (
              <div className="space-y-6 animate-fadeIn">
                
                <div>
                  <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-2">
                    Primary Modalities for Clinical Triage *
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[
                      { id: 'CT', label: 'Computed Tomography (CT)', badge: 'STAT Neuro & Chest' },
                      { id: 'MRI', label: 'Magnetic Resonance (MRI)', badge: 'Diffusion & Stroke' },
                      { id: 'XR', label: 'Plain Radiographs (X-Ray)', badge: 'Portable ICU / Chest' },
                      { id: 'US', label: 'Ultrasound / Other', badge: 'Emergency FAST' }
                    ].map(mod => {
                      const isSelected = formData.modalities.includes(mod.id);
                      return (
                        <div
                          key={mod.id}
                          onClick={() => handleModalityToggle(mod.id)}
                          className={`p-3 rounded-xl border cursor-pointer transition text-xs ${
                            isSelected
                              ? 'bg-teal-500/10 dark:bg-navy-850 border-teal-500 text-teal-700 dark:text-cyan-300 font-bold shadow-sm'
                              : 'bg-slate-50 dark:bg-navy-950 border-slate-300 dark:border-navy-800 text-slate-600 dark:text-slate-400'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-mono">{mod.id}</span>
                            <span className={`w-3.5 h-3.5 rounded flex items-center justify-center text-[10px] ${
                              isSelected ? 'bg-teal-500 text-white' : 'border border-slate-400'
                            }`}>
                              {isSelected ? '✓' : ''}
                            </span>
                          </div>
                          <p className="text-[11px] line-clamp-1">{mod.label}</p>
                        </div>
                      );
                    })}
                  </div>
                  {errors.modalities && (
                    <p className="text-[11px] text-rose-500 font-mono mt-1 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" /> {errors.modalities}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                  <div>
                    <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-1.5">
                      Estimated Daily Study Volume
                    </label>
                    <select
                      value={formData.dailyVolume}
                      onChange={(e) => setFormData({ ...formData, dailyVolume: e.target.value })}
                      className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-navy-800 rounded-xl px-3.5 py-3 text-xs text-navy-900 dark:text-white focus:outline-none focus:border-teal-500 transition"
                    >
                      <option value="< 150 studies/day">&lt; 150 studies / day</option>
                      <option value="150 - 300 studies/day">150 - 300 studies / day</option>
                      <option value="300 - 600 studies/day">300 - 600 studies / day</option>
                      <option value="600 - 1,000 studies/day">600 - 1,000 studies / day</option>
                      <option value="1,000+ studies/day">1,000+ studies / day</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-1.5">
                      Current PACS / VNA
                    </label>
                    <select
                      value={formData.pacsVendor}
                      onChange={(e) => setFormData({ ...formData, pacsVendor: e.target.value })}
                      className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-navy-800 rounded-xl px-3.5 py-3 text-xs text-navy-900 dark:text-white focus:outline-none focus:border-teal-500 transition"
                    >
                      <option value="Sectra">Sectra PACS</option>
                      <option value="GE Centricity">GE Centricity / AW</option>
                      <option value="Philips Intellispace">Philips Intellispace</option>
                      <option value="Fujifilm Synapse">Fujifilm Synapse</option>
                      <option value="Siemens syngo">Siemens syngo.plaza</option>
                      <option value="Agfa Enterprise">Agfa Enterprise Imaging</option>
                      <option value="Other / Open Source DICOM">Other / dcm4chee / Orthanc</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-1.5">
                      Hospital EHR Platform
                    </label>
                    <select
                      value={formData.ehrSystem}
                      onChange={(e) => setFormData({ ...formData, ehrSystem: e.target.value })}
                      className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-navy-800 rounded-xl px-3.5 py-3 text-xs text-navy-900 dark:text-white focus:outline-none focus:border-teal-500 transition"
                    >
                      <option value="Epic Systems">Epic Radiant / EHR</option>
                      <option value="Cerner / Oracle Health">Cerner / Oracle Health</option>
                      <option value="Meditech">Meditech Expanse</option>
                      <option value="CharmHealth EHR">CharmHealth Cloud EHR</option>
                      <option value="BackBone HMS">BackBone HMS</option>
                      <option value="Other HL7 v2/FHIR">Other Interface Engine</option>
                    </select>
                  </div>
                </div>

              </div>
            )}

            {/* STEP 3: Deployment Goals */}
            {currentStep === 3 && (
              <div className="space-y-6 animate-fadeIn">
                
                <div>
                  <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-2">
                    Primary Pilot Evaluation Goals (Select all that apply)
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {[
                      'Workflow Optimization & Pre-Reads',
                      'SLA Breach & Turnaround Time Monitoring',
                      'EHR Integration Validation & FHIR R4 Writeback',
                      'Air-Gapped On-Premises Compliance',
                      'Clinician Burnout & Fatigue Mitigation',
                      'Emergency Triage & Closed-Loop Alerts'
                    ].map(goal => {
                      const isSelected = formData.deploymentGoals.includes(goal);
                      return (
                        <div
                          key={goal}
                          onClick={() => handleGoalToggle(goal)}
                          className={`p-3 rounded-xl border cursor-pointer transition text-xs flex items-center justify-between ${
                            isSelected
                              ? 'bg-teal-500/10 dark:bg-navy-850 border-teal-500 text-teal-700 dark:text-cyan-300 font-bold'
                              : 'bg-slate-50 dark:bg-navy-950 border-slate-300 dark:border-navy-800 text-slate-600 dark:text-slate-400'
                          }`}
                        >
                          <span>{goal}</span>
                          <span className={`w-4 h-4 rounded flex items-center justify-center text-xs ${
                            isSelected ? 'bg-teal-500 text-white' : 'border border-slate-400'
                          }`}>
                            {isSelected ? '✓' : ''}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-1.5">
                    Infrastructure Target for Pilot
                  </label>
                  <select
                    value={formData.deploymentTarget}
                    onChange={(e) => setFormData({ ...formData, deploymentTarget: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-navy-800 rounded-xl px-3.5 py-3 text-xs text-navy-900 dark:text-white focus:outline-none focus:border-teal-500 transition"
                  >
                    <option value="Air-Gapped On-Premises (Docker/K8s)">Air-Gapped On-Premises Hospital DMZ (Docker Compose / Kubernetes)</option>
                    <option value="Dedicated Private Cloud Gov (AWS / Azure Gov)">Dedicated Sovereign Private Cloud (AWS GovCloud / Azure Health)</option>
                    <option value="Hybrid Gateway (On-Prem Ingest + Cloud EHR)">Hybrid Gateway (On-Premise DICOM Ingest + Cloud EHR Synchronizer)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-navy-900 dark:text-slate-200 mb-1.5">
                    Special Inquiries or Clinical Priorities (Optional)
                  </label>
                  <textarea
                    rows={2}
                    placeholder="e.g. Focus on overnight emergency head CT bleeds and integration with our existing Sectra PACS archive..."
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-navy-950 border border-slate-300 dark:border-navy-800 rounded-xl px-3.5 py-2.5 text-xs text-navy-900 dark:text-white focus:outline-none focus:border-teal-500 transition"
                  ></textarea>
                </div>

              </div>
            )}

            {/* Stepper Navigation Buttons */}
            <div className="pt-4 border-t border-slate-200 dark:border-navy-800 flex items-center justify-between gap-4">
              {currentStep > 1 ? (
                <button
                  type="button"
                  onClick={handleBack}
                  className="px-5 py-2.5 rounded-xl text-xs font-semibold border border-slate-300 dark:border-navy-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-navy-800 transition flex items-center gap-1.5"
                >
                  <ArrowLeft className="w-3.5 h-3.5" /> Back
                </button>
              ) : (
                <span className="text-[11px] font-mono text-slate-400">
                  🔒 HIPAA Compliant & BAA Covered
                </span>
              )}

              {currentStep < 3 ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="px-6 py-3 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 shadow-glow-teal transition flex items-center gap-1.5"
                >
                  Continue to {currentStep === 1 ? 'Department Profile' : 'Deployment Goals'}
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              ) : (
                <button
                  type="submit"
                  className="px-7 py-3 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-teal-500 via-teal-600 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 shadow-glow-teal transition flex items-center gap-2"
                >
                  <FileCheck className="w-4 h-4" />
                  Submit Pilot Dossier
                </button>
              )}
            </div>

          </form>
        )}
      </div>

    </div>
  );
};

export default DemoRequestForm;
