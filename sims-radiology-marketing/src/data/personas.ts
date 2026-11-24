export interface Persona {
  id: string;
  role: string;
  title: string;
  organization: string;
  avatarText: string;
  quote: string;
  keyPains: string[];
  keyOutcomes: string[];
  primaryFeatureHook: string;
}

export const personas: Persona[] = [
  {
    id: 'chief-radiologist',
    role: 'Clinical Leadership',
    title: 'Chief of Radiology & Diagnostic Imaging',
    organization: 'Academic Medical Centers & Multi-Hospital Health Systems',
    avatarText: 'CR',
    quote: 'Our volume increased 28% year-over-year while staffing remained flat. SIMS AI triages STAT neuro and pulmonary cases into our top-of-list within 42 seconds of PACS ingestion, with full SHAP explainability.',
    keyPains: [
      'Critical findings buried in chronological worklists',
      'Diagnostic fatigue leading to burnout during night shifts',
      'Black-box AI models that radiologists cannot verify or trust'
    ],
    keyOutcomes: [
      '72% reduction in turnaround time for STAT critical emergencies',
      'Visual SHAP heatmaps showing exact pixel rationale for every triage suggestion',
      'NeMo Guardrail clinical rail ensures 0% hallucinated report formulations'
    ],
    primaryFeatureHook: 'Agentic Worklist Prioritization & XAI Attribution'
  },
  {
    id: 'hospital-cio',
    role: 'IT & Security Leadership',
    title: 'Chief Information Officer (CIO / CISO)',
    organization: 'Enterprise Healthcare Networks',
    avatarText: 'CIO',
    quote: 'Deploying AI across 14 hospital sites cannot require SaaS data egress. SIMS runs fully containerized on-premises in our secure air-gapped DMZ with native DICOM & FHIR R4 interoperability.',
    keyPains: [
      'PHI data sovereignty and cloud vendor lock-in risks',
      'Fragile point-to-point interface engines that crash during peak hours',
      'Lengthy compliance and FDA 510(k) auditing overhead'
    ],
    keyOutcomes: [
      '100% on-prem air-gapped deployment option via Docker / K8s',
      'Automated Kestra pipeline with Celery task isolation and asyncpg resilience',
      'SOC2 Type II & HIPAA audit trails integrated into existing SIEM'
    ],
    primaryFeatureHook: 'Air-Gapped Clean Architecture & Enterprise Interoperability'
  },
  {
    id: 'pacs-admin',
    role: 'Clinical Operations',
    title: 'Director of Imaging Informatics & PACS Admin',
    organization: 'Regional Imaging Centers & Teleradiology Networks',
    avatarText: 'PA',
    quote: 'Integrating new algorithms usually takes 6 months of custom HL7 scripting. SIMS connected to our Sectra and GE PACS over standard DICOM C-STORE and FHIR Core in under 48 hours.',
    keyPains: [
      'DICOM tag corruption and modality incompatibility across scanner vendors',
      'Disjointed third-party viewer plugins that slow down radiologist reading stations',
      'Manual reconciliation of accession numbers and patient identifiers'
    ],
    keyOutcomes: [
      'Native DICOM Part 10 & DIMSE C-STORE / C-FIND protocol support',
      'Zero-footprint web viewer with A2UI web components',
      'Bi-directional FHIR DiagnosticReport synchronizer'
    ],
    primaryFeatureHook: 'Plug-and-Play DICOMweb & FHIR Bridge'
  }
];
