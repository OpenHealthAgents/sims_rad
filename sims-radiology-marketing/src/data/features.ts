export interface FeatureSpec {
  id: string;
  category: 'AI Agents' | 'Clinical Safety' | 'Interoperability' | 'Workflow';
  title: string;
  badge: string;
  description: string;
  technicalHighlights: string[];
  metrics: string;
}

export const featureSpecs: FeatureSpec[] = [
  {
    id: 'deep-agents-triage',
    category: 'AI Agents',
    title: 'Autonomous Multi-Agent Diagnostic Triage',
    badge: 'LangGraph & Deep Agents',
    description: 'Specialized diagnostic sub-agents coordinate via LangGraph state machines to detect ICH, pulmonary embolism, tension pneumothorax, and acute fractures within seconds of image transmission.',
    technicalHighlights: [
      'LangGraph deterministic state transitions with checkpointing',
      'Dynamic multi-modality dispatch (CT, MR, X-Ray, Ultrasound)',
      'Sub-second DICOM header parsing and accession routing'
    ],
    metrics: '< 45s Mean Time to Triage'
  },
  {
    id: 'nemo-guardrails',
    category: 'Clinical Safety',
    title: 'NVIDIA NeMo Clinical Safety Rails',
    badge: '100% Policy Adherence',
    description: 'Enforces hard clinical guardrails on all agent outputs. Automatically flags, blocks, and audits any ungrounded assertions or out-of-scope diagnostic suggestions prior to radiologist review.',
    technicalHighlights: [
      'Self-check hallucination detection & topical boundary rails',
      'Clinical guideline policy checks against ACR Appropriateness Criteria',
      'Audit log with immutable compliance hashes'
    ],
    metrics: '0.0% Ungrounded Hallucinations'
  },
  {
    id: 'shap-explainability',
    category: 'AI Agents',
    title: 'Pixel-Level SHAP Explainability (XAI)',
    badge: 'Interpretable AI',
    description: 'No black boxes. Radiologists inspect transparent SHAP attribution maps superimposed on DICOM slices, revealing the exact anatomical features that triggered the triage alert.',
    technicalHighlights: [
      'Direct integration with PyDICOM pixel arrays',
      'Interactive slice-by-slice heat map visualizer',
      'Quantified confidence percentiles and anatomical bounding bounds'
    ],
    metrics: '99.4% Radiologist Alignment'
  },
  {
    id: 'clean-arch-kestra',
    category: 'Workflow',
    title: 'Clean Architecture & Kestra Pipeline Orchestration',
    badge: 'Enterprise Architecture',
    description: 'Built following Uncle Bob’s Clean Architecture with strict inward dependency rules. Kestra workflows manage large-scale DICOM ingestion and Celery asynchronous task distribution.',
    technicalHighlights: [
      'Decoupled Domain Entities, Use Cases, and Infrastructure Adapters',
      'Fault-tolerant Kestra DAGs with instant retry policies',
      'Horizontal scale across multi-node GPU compute clusters'
    ],
    metrics: '99.99% Ingestion Uptime'
  },
  {
    id: 'fhir-dicom-core',
    category: 'Interoperability',
    title: 'Native DICOMweb & FHIR R4 Core Integration',
    badge: 'Universal Healthcare Interop',
    description: 'Connect seamlessly with Epic, Cerner, Sectra, GE Centricity, and Philips Intellispace. Exports structured FHIR DiagnosticReport resources directly into the hospital EHR.',
    technicalHighlights: [
      'DICOM Part 10 file format & DIMSE protocol adapters',
      'HL7 FHIR R4 DiagnosticReport and Observation resources',
      'A2UI compliant reactive Web Components'
    ],
    metrics: 'Zero-Egress On-Prem Ready'
  }
];
