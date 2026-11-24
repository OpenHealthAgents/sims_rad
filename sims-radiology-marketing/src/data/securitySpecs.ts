export interface SecurityPillar {
  title: string;
  badge: string;
  description: string;
  items: string[];
}

export const securityPillars: SecurityPillar[] = [
  {
    title: 'Zero Data Egress / Air-Gapped Deployment',
    badge: 'On-Premises Sovereignty',
    description: 'SIMS is engineered from the ground up to operate completely isolated from the public internet within the hospital’s secure VLAN/DMZ.',
    items: [
      'No outbound model calls to third-party public LLMs',
      'Local PyTorch / ONNX runtime for on-prem NVIDIA GPU nodes',
      'Containerized PostgreSQL 16 & Redis encrypted volumes',
      'Native BAA provided with dedicated on-prem support'
    ]
  },
  {
    title: 'NVIDIA NeMo Clinical Rails & Safety Verification',
    badge: 'Clinical Guardrails',
    description: 'Deterministic safety boundaries eliminate non-factual medical statements and strictly enforce hospital policy before any text is shown.',
    items: [
      'Topical restraint prevents hallucination of unexamined findings',
      'Policy-enforced moderation against non-standard terminology',
      'Audit log with timestamped input-output validation checks',
      'Radiologist human-in-the-loop sign-off required for final reporting'
    ]
  },
  {
    title: 'HIPAA, SOC 2 Type II & FHIR R4 Conformance',
    badge: 'Regulatory Standards',
    description: 'Full alignment with international healthcare informatics privacy and security standards.',
    items: [
      'End-to-end TLS 1.3 encryption in transit & AES-256 at rest',
      'Strict DICOM de-identification (PS 3.15 Annex E compliant)',
      'Immutable audit trails with Langfuse observability',
      'Role-based access control (RBAC) with Active Directory / LDAP'
    ]
  }
];
