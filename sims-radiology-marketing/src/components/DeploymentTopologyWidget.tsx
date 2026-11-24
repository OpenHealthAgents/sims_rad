import React, { useState } from 'react';
import { 
  Server, 
  Database, 
  ShieldCheck, 
  Lock, 
  HardDrive, 
  Layers, 
  ArrowRight, 
  ArrowLeftRight, 
  Cloud, 
  CheckCircle2, 
  AlertTriangle,
  Info
} from 'lucide-react';

export const DeploymentTopologyWidget: React.FC = () => {
  const [selectedZone, setSelectedZone] = useState<string>('gateway');

  const zoneDetails: Record<string, { title: string; subtitle: string; description: string; securityGuarantees: string[]; protocols: string[] }> = {
    pacs: {
      title: 'Hospital Imaging Zone (PACS / RIS / BackBone HMS)',
      subtitle: 'Existing Hospital Infrastructure (Zero Vendor Replacement)',
      description: 'Your existing multi-vendor PACS (Sectra, GE Centricity, Philips, Fujifilm) and BackBone HMS hospital management system continue normal operation.',
      securityGuarantees: [
        'Raw pixel data remains strictly in existing PACS storage tiers',
        'SIMS only requests DICOM metadata tags and de-identified study frames for inference',
        'Zero modifications to scanner configurations or DIMSE routing nodes'
      ],
      protocols: ['DICOM PS 3.10', 'DIMSE C-STORE', 'DIMSE C-FIND / C-MOVE', 'HL7 v2.x ADT/ORM']
    },
    gateway: {
      title: 'SIMS Integration Gateway & Agentic Core',
      subtitle: 'On-Premises DMZ Containerized Cluster',
      description: 'Fully isolated container cluster running inside the hospital DMZ. Coordinates PyDICOM parsing, LangGraph multi-agent choreography, and NVIDIA NeMo Guardrails.',
      securityGuarantees: [
        'Zero external LLM model calls or public internet egress',
        'Air-gapped local model weights on hospital NVIDIA GPU nodes',
        'Deterministic NeMo Guardrail policy boundary blocks unauthorized actions'
      ],
      protocols: ['Docker Compose / K8s', 'Local PyTorch / ONNX', 'WADO-RS / QIDO-RS', 'mTLS Internal Bus']
    },
    outbox: {
      title: 'Local PostgreSQL 16 & Transactional Outbox',
      subtitle: 'Encrypted Persistence & Idempotency Buffer',
      description: 'Stores extracted study metadata, AI triage risk percentiles, and immutable cryptographic audit trails. The Transactional Outbox pattern guarantees exactly-once dispatch.',
      securityGuarantees: [
        'AES-256 encrypted storage volumes at rest',
        'Strict idempotency keys prevent duplicate reporting during network drops',
        'Immutable audit hashes with Langfuse telemetry'
      ],
      protocols: ['SQLAlchemy 2.0 Asyncpg', 'Redis Task Queue', 'SHA-256 Audit Hashes']
    },
    ehr: {
      title: 'CharmHealth Cloud EHR Gateway',
      subtitle: 'Secure Encrypted Writeback & Scheduling Bridge',
      description: 'Connects to CharmHealth Cloud EHR APIs and hospital enterprise systems to synchronize patient encounters, orders, and verified diagnostic reports.',
      securityGuarantees: [
        'Enforces 0% unvalidated writeback (requires radiologist biometric sign-off)',
        'TLS 1.3 encryption in transit with OAuth2 / API Key authorization',
        'Bi-directional HL7 FHIR R4 DiagnosticReport synchronization'
      ],
      protocols: ['HL7 FHIR R4 Core', 'CharmHealth REST APIs', 'OAuth 2.0 / BAA Covered Channel']
    }
  };

  const currentZone = zoneDetails[selectedZone];

  return (
    <div className="w-full space-y-6">
      
      {/* Explicit Core Architectural Disclaimer */}
      <div className="p-4 sm:p-5 rounded-2xl bg-teal-500/10 dark:bg-navy-900 border border-teal-500/30 flex items-start sm:items-center gap-3.5 shadow-sm">
        <div className="p-2 rounded-xl bg-teal-500/20 text-teal-700 dark:text-cyan-300 shrink-0">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div className="text-xs sm:text-sm">
          <span className="font-extrabold text-navy-900 dark:text-white mr-1.5 block sm:inline">
            PHI Data Sovereignty Standard:
          </span>
          <span className="text-slate-700 dark:text-slate-200 font-medium">
            Raw pixel data remains in existing PACS; application stores study metadata and immutable report records.
          </span>
        </div>
      </div>

      {/* Interactive Topology Visual Diagram */}
      <div className="bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-navy-800 p-6 lg:p-8 shadow-medical-card dark:shadow-medical-card-dark space-y-8">
        
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-200 dark:border-navy-800">
          <div>
            <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-teal-600 dark:text-cyan-400">
              Hospital-Controlled Deployment Boundary
            </span>
            <h3 className="text-xl font-extrabold text-navy-900 dark:text-white">
              On-Premises DMZ Topology & EHR Integration
            </h3>
          </div>
          <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 font-semibold self-start sm:self-auto">
            ● 100% Air-Gapped DMZ Qualified
          </span>
        </div>

        {/* 4-Zone Interactive Architecture Flow */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 relative">
          
          {/* Zone 1: Hospital PACS & HMS */}
          <div
            onClick={() => setSelectedZone('pacs')}
            className={`p-5 rounded-2xl border cursor-pointer transition-all flex flex-col justify-between ${
              selectedZone === 'pacs'
                ? 'bg-teal-500/10 dark:bg-navy-850 border-teal-500 shadow-glow-teal ring-2 ring-teal-500/20'
                : 'bg-slate-50 dark:bg-navy-950 border-slate-200 dark:border-navy-800 hover:border-teal-400'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                  ZONE 01 • HOSPITAL
                </span>
                <HardDrive className="w-4 h-4 text-slate-500 dark:text-slate-400" />
              </div>
              <h4 className="font-bold text-sm text-navy-900 dark:text-white mb-1">
                Hospital Imaging Zone
              </h4>
              <p className="text-xs font-mono text-teal-600 dark:text-cyan-400 mb-3">
                PACS / RIS / BackBone HMS
              </p>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                Stores raw DICOM CT, MR, and X-ray pixel datasets. Emits standard C-STORE pushes.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-200 dark:border-navy-800 text-[11px] font-mono text-slate-500 dark:text-slate-400">
              Raw Pixels Retained In-Place
            </div>
          </div>

          {/* Zone 2: SIMS Integration Gateway */}
          <div
            onClick={() => setSelectedZone('gateway')}
            className={`p-5 rounded-2xl border cursor-pointer transition-all flex flex-col justify-between ${
              selectedZone === 'gateway'
                ? 'bg-teal-500/10 dark:bg-navy-850 border-teal-500 shadow-glow-teal ring-2 ring-teal-500/20'
                : 'bg-slate-50 dark:bg-navy-950 border-slate-200 dark:border-navy-800 hover:border-teal-400'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono font-bold text-teal-600 dark:text-cyan-400 uppercase">
                  ZONE 02 • CORE AGENT
                </span>
                <Server className="w-4 h-4 text-teal-500" />
              </div>
              <h4 className="font-bold text-sm text-navy-900 dark:text-white mb-1">
                SIMS Integration Gateway
              </h4>
              <p className="text-xs font-mono text-teal-600 dark:text-cyan-400 mb-3">
                LangGraph + NeMo Rails
              </p>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                Local GPU cluster coordinates sub-agents, clinical guardrails, and SHAP XAI heatmaps.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-200 dark:border-navy-800 text-[11px] font-mono text-teal-600 dark:text-cyan-400 font-semibold">
              Zero Public LLM Egress
            </div>
          </div>

          {/* Zone 3: PostgreSQL & Outbox */}
          <div
            onClick={() => setSelectedZone('outbox')}
            className={`p-5 rounded-2xl border cursor-pointer transition-all flex flex-col justify-between ${
              selectedZone === 'outbox'
                ? 'bg-teal-500/10 dark:bg-navy-850 border-teal-500 shadow-glow-teal ring-2 ring-teal-500/20'
                : 'bg-slate-50 dark:bg-navy-950 border-slate-200 dark:border-navy-800 hover:border-teal-400'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                  ZONE 03 • STORAGE
                </span>
                <Database className="w-4 h-4 text-cyan-500" />
              </div>
              <h4 className="font-bold text-sm text-navy-900 dark:text-white mb-1">
                PostgreSQL & Outbox
              </h4>
              <p className="text-xs font-mono text-cyan-600 dark:text-cyan-400 mb-3">
                AES-256 Encrypted Volumes
              </p>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                Stores study metadata, triage priority tags, and idempotent outbound event buffers.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-200 dark:border-navy-800 text-[11px] font-mono text-slate-500 dark:text-slate-400">
              Exactly-Once Dispatch
            </div>
          </div>

          {/* Zone 4: CharmHealth Cloud EHR */}
          <div
            onClick={() => setSelectedZone('ehr')}
            className={`p-5 rounded-2xl border cursor-pointer transition-all flex flex-col justify-between ${
              selectedZone === 'ehr'
                ? 'bg-teal-500/10 dark:bg-navy-850 border-teal-500 shadow-glow-teal ring-2 ring-teal-500/20'
                : 'bg-slate-50 dark:bg-navy-950 border-slate-200 dark:border-navy-800 hover:border-teal-400'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                  ZONE 04 • EHR CLOUD
                </span>
                <Cloud className="w-4 h-4 text-teal-500" />
              </div>
              <h4 className="font-bold text-sm text-navy-900 dark:text-white mb-1">
                CharmHealth Cloud EHR
              </h4>
              <p className="text-xs font-mono text-teal-600 dark:text-cyan-400 mb-3">
                FHIR R4 DiagnosticReport
              </p>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                Receives verified reports, clinical impressions, and billing codes post radiologist sign-off.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-200 dark:border-navy-800 text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
              Radiologist Approval Gate
            </div>
          </div>

        </div>

        {/* Selected Zone Deep-Dive Inspection Panel */}
        <div className="p-6 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200 dark:border-navy-800">
            <div>
              <h4 className="font-bold text-base text-navy-900 dark:text-white">
                {currentZone.title}
              </h4>
              <p className="text-xs text-teal-600 dark:text-cyan-400 font-mono">
                {currentZone.subtitle}
              </p>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Click any zone above to inspect network protocols & guarantees
            </span>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            {currentZone.description}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            
            {/* Guarantees */}
            <div className="space-y-2">
              <h5 className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 font-bold flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-500" />
                Security & Data Integrity Guarantees
              </h5>
              <ul className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                {currentZone.securityGuarantees.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-teal-500 font-bold">✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Protocols */}
            <div className="space-y-2">
              <h5 className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 font-bold flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-cyan-500" />
                Supported Interface Protocols
              </h5>
              <div className="flex flex-wrap gap-2">
                {currentZone.protocols.map((proto, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-md text-xs font-mono bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 text-navy-800 dark:text-slate-200 shadow-sm"
                  >
                    {proto}
                  </span>
                ))}
              </div>
            </div>

          </div>
        </div>

      </div>

    </div>
  );
};

export default DeploymentTopologyWidget;
