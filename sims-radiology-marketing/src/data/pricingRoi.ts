export interface TierPlan {
  id: string;
  name: string;
  tagline: string;
  idealFor: string;
  deploymentType: 'Hybrid Cloud' | 'Air-Gapped On-Premises' | 'Global Health System';
  features: string[];
  recommended?: boolean;
}

export const deploymentTiers: TierPlan[] = [
  {
    id: 'clinical-center',
    name: 'Diagnostic Core',
    tagline: 'Ideal for independent imaging centers and regional community hospitals',
    idealFor: 'Up to 50,000 studies / year',
    deploymentType: 'Hybrid Cloud',
    features: [
      'Sub-agent triage for Chest X-Ray & Brain CT',
      'NVIDIA NeMo Guardrails safety pipeline',
      'DICOM C-STORE and Query/Retrieve',
      'Web-based study viewer with A2UI components',
      'Standard 8x5 support SLA with 99.9% uptime'
    ]
  },
  {
    id: 'enterprise-health',
    name: 'Health System Enterprise',
    tagline: 'Full autonomous agentic orchestration with on-prem air-gapped security',
    idealFor: '50,000 - 500,000+ studies / year',
    deploymentType: 'Air-Gapped On-Premises',
    recommended: true,
    features: [
      'Full Multi-Modality Agent Fleet (CT, MRI, XR, US)',
      'Custom NVIDIA NeMo clinical safety rails',
      'SHAP XAI feature attribution maps on full DICOM series',
      'Bi-directional FHIR R4 DiagnosticReport EHR write-back',
      'Kestra orchestrated batch and streaming pipelines',
      'Zero external network egress (100% on-premises DMZ)',
      '24/7/365 dedicated medical informatics SLA'
    ]
  },
  {
    id: 'academic-research',
    name: 'Academic & Network',
    tagline: 'Custom agent training, research harnesses, and multi-facility federation',
    idealFor: 'Multi-hospital consortiums & Research Universities',
    deploymentType: 'Global Health System',
    features: [
      'Everything in Health System Enterprise',
      'Custom Deep Agents harness configuration',
      'Langfuse deep observability and trace analytics',
      'Federated learning & retrospective cohort research mode',
      'Custom PACS gateway and DICOM metadata sanitization hooks',
      'Dedicated Solutions Architect & Clinical AI Lead'
    ]
  }
];

export interface RoiMetricFormula {
  studiesPerYear: number;
  avgRadHourlyRate: number;
  minutesSavedPerStudy: number;
  statTurnaroundMinutesBefore: number;
  statTurnaroundMinutesAfter: number;
}

export function calculateRoi(studiesPerYear: number, radCount: number) {
  // Calculations based on 38% radiologist triage time efficiency and emergency triage speedups
  const avgHourlyRate = 220; // Average radiologist hourly cost in USD
  const hoursSavedPerStudy = 0.08; // ~4.8 minutes per complex study saved via pre-triage & drafting
  const annualHoursSaved = Math.round(studiesPerYear * hoursSavedPerStudy);
  const annualDollarsSaved = Math.round(annualHoursSaved * avgHourlyRate);
  
  // STAT critical alert turnaround time reduction
  const turnaroundBefore = 75; // minutes
  const turnaroundAfter = 21; // minutes
  const turnaroundPercentReduction = 72; // %

  return {
    annualHoursSaved,
    annualDollarsSaved,
    turnaroundBefore,
    turnaroundAfter,
    turnaroundPercentReduction,
    capacityMultiplier: (1 + (annualHoursSaved / (radCount * 1800))).toFixed(1)
  };
}
