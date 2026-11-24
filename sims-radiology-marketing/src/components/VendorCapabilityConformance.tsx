import React, { useState } from 'react';
import { CheckCircle2, ShieldCheck, Layers, FileCode, Check, Search, ExternalLink } from 'lucide-react';

export const VendorCapabilityConformance: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<'ALL' | 'DICOM' | 'FHIR_HL7' | 'EHR_HMS'>('ALL');

  const standards = [
    {
      standard: 'DICOMweb (QIDO-RS)',
      category: 'DICOM',
      role: 'Query Based on ID for DICOM Objects',
      supportLevel: 'Full Native Conformance',
      protocol: 'RESTful HTTP / JSON / DICOM PS 3.18',
      details: 'Queries study lists, modalities, accession numbers, and patient identifiers without opening legacy heavy DIMSE socket loops.',
      status: 'production'
    },
    {
      standard: 'DICOMweb (WADO-RS)',
      category: 'DICOM',
      role: 'Web Access to DICOM Objects by Retrieve',
      supportLevel: 'Full Native Conformance',
      protocol: 'RESTful HTTP / multipart related',
      details: 'Pulls full-resolution multi-slice CT, MRI, and X-ray series for browser-based A2UI Web Component viewing and inference staging.',
      status: 'production'
    },
    {
      standard: 'DICOM DIMSE (C-STORE / C-FIND)',
      category: 'DICOM',
      role: 'Legacy PACS Transmission Standard',
      supportLevel: 'Full Native Conformance',
      protocol: 'TCP/IP DICOM PS 3.10 Port 104 / 11112',
      details: 'Direct compatibility with legacy Sectra, GE Centricity, Philips, and Siemens PACS servers. No intermediate translation box needed.',
      status: 'production'
    },
    {
      standard: 'HL7 FHIR R4 (DiagnosticReport)',
      category: 'FHIR_HL7',
      role: 'Structured Diagnostic Report Synchronization',
      supportLevel: 'Full Native Conformance',
      protocol: 'RESTful JSON / FHIR Core R4 Specs',
      details: 'Writes validated findings, ACR impression narratives, radiologist sign-off timestamps, and critical alert codes back into the hospital EHR.',
      status: 'production'
    },
    {
      standard: 'HL7 FHIR R4 (Observation & ServiceRequest)',
      category: 'FHIR_HL7',
      role: 'Quantitative Biometrics & Order Lifecycle',
      supportLevel: 'Full Native Conformance',
      protocol: 'RESTful JSON / LOINC / SNOMED-CT',
      details: 'Exports quantitative measurements (e.g. ICH volume 28cc, midline shift 4.2mm) as discrete, machine-queryable clinical observations.',
      status: 'production'
    },
    {
      standard: 'HL7 v2.x (ADT / ORM / ORU)',
      category: 'FHIR_HL7',
      role: 'Clinical Admissions, Orders & Unsolicited Results',
      supportLevel: 'Supported via MLLP Gateway',
      protocol: 'Minimal Lower Layer Protocol (MLLP) TCP/IP',
      details: 'Ingests inbound patient admission demographics and exam orders from legacy interface engines (Mirth Connect, Rhapsody, Cloverleaf).',
      status: 'production'
    },
    {
      standard: 'BackBone HMS',
      category: 'EHR_HMS',
      role: 'Hospital Management & Inpatient Bedside Roster',
      supportLevel: 'Integrated Partner Adapter',
      protocol: 'Secure REST API & Direct Event Stream',
      details: 'Matches accession records against active inpatient beds, surgical rosters, and on-call attending registries to determine critical alert targets.',
      status: 'production'
    },
    {
      standard: 'CharmHealth Cloud EHR APIs',
      category: 'EHR_HMS',
      role: 'Outpatient & Ambulatory Cloud Integration',
      supportLevel: 'Certified Cloud Gateway',
      protocol: 'OAuth 2.0 / REST API / TLS 1.3',
      details: 'Bi-directional synchronization of outpatient imaging orders, clinical consultation notes, and final signed diagnostic report writebacks.',
      status: 'production'
    }
  ];

  const filtered = selectedCategory === 'ALL'
    ? standards
    : standards.filter(s => s.category === selectedCategory);

  return (
    <div className="space-y-6">
      
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-teal-600 dark:text-cyan-400 bg-teal-500/10 px-3 py-1 rounded-full border border-teal-500/20 inline-block mb-1">
            Healthcare Informatics Interoperability
          </span>
          <h3 className="text-xl sm:text-2xl font-extrabold text-navy-900 dark:text-white">
            Vendor Capability & Interface Conformance
          </h3>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 bg-slate-100 dark:bg-navy-900 p-1 rounded-xl text-xs font-mono font-semibold self-start sm:self-auto border border-slate-200 dark:border-navy-800">
          {[
            { id: 'ALL', label: 'All Standards' },
            { id: 'DICOM', label: 'DICOMweb & DIMSE' },
            { id: 'FHIR_HL7', label: 'FHIR R4 & HL7' },
            { id: 'EHR_HMS', label: 'BackBone & CharmHealth' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setSelectedCategory(tab.id as any)}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                selectedCategory === tab.id
                  ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white font-bold shadow-glow-teal'
                  : 'text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Conformance Matrix Table */}
      <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-medical-card dark:shadow-medical-card-dark overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="bg-slate-50 dark:bg-navy-950 border-b border-slate-200 dark:border-navy-800 text-slate-500 dark:text-slate-400 font-mono text-[11px]">
                <th className="py-3.5 px-5 font-semibold">Standard / Interface</th>
                <th className="py-3.5 px-4 font-semibold">Protocol & Transport</th>
                <th className="py-3.5 px-4 font-semibold">Conformance Level</th>
                <th className="py-3.5 px-5 font-semibold">Technical Capability & Use Case</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-navy-800 text-slate-700 dark:text-slate-300">
              {filtered.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80 dark:hover:bg-navy-850/50 transition-colors">
                  <td className="py-4 px-5">
                    <div className="font-bold text-navy-900 dark:text-white text-sm">
                      {item.standard}
                    </div>
                    <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                      {item.role}
                    </div>
                  </td>
                  <td className="py-4 px-4 font-mono text-xs text-teal-600 dark:text-cyan-400">
                    {item.protocol}
                  </td>
                  <td className="py-4 px-4">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                      <Check className="w-3 h-3 text-emerald-500" />
                      {item.supportLevel}
                    </span>
                  </td>
                  <td className="py-4 px-5 text-xs text-slate-600 dark:text-slate-300 leading-relaxed max-w-md">
                    {item.details}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer Summary Strip */}
        <div className="p-4 bg-slate-50 dark:bg-navy-950 border-t border-slate-200 dark:border-navy-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400 font-mono">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>All interfaces certified for Zero-Data-Egress on-premises deployment</span>
          </div>
          <span>IHE Profiles: BIR, SWF.b, RAD-68, RAD-69, PAM</span>
        </div>
      </div>

    </div>
  );
};

export default VendorCapabilityConformance;
