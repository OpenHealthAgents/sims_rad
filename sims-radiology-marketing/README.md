# SIMS Radiology Marketing & Clinical Intelligence Portal

Enterprise marketing website and interactive clinical intelligence portal for the **SIMS Radiology AI Operating Agentic Platform**.

---

## 📁 Directory Structure & Blueprint

```
sims-radiology-marketing/
├── public/                       # Assets, SVG logos, DICOM icons, and mock diagrams
│   └── logo.svg                  # Brand SVG with clinical crosshair & agent node
├── src/
│   ├── components/               # Reusable UI components
│   │   ├── ArchitectureDiagram.tsx # Clean Architecture 4-layer topology view
│   │   ├── DicomMockViewer.tsx   # Interactive CT Axial viewer with SHAP heatmaps & NeMo status
│   │   ├── Features.tsx          # Multi-agent autonomous pipeline cards
│   │   ├── Hero.tsx              # Conversion-focused hero with live triage simulation
│   │   ├── PersonaTabs.tsx       # Stakeholder matrix (Chief Radiologist, Hospital CIO, PACS Admin)
│   │   ├── RoiCalculator.tsx     # Dynamic financial ROI & clinical turnaround slider
│   │   └── SecurityMatrix.tsx    # Air-gap on-premise comparison vs generic SaaS
│   ├── data/                     # Content matrices, feature specs, persona data
│   │   ├── features.ts           # Agentic triage, NeMo safety, SHAP XAI specs
│   │   ├── personas.ts           # Pain/gain profiles & quotes for buyers & clinical users
│   │   ├── pricingRoi.ts         # Economic calculator algorithms & licensing tiers
│   │   └── securitySpecs.ts      # Zero-egress, HIPAA, SOC 2 Type II, and FHIR specs
│   ├── layouts/                  # Base layout, Navigation header, Footer
│   │   ├── BaseLayout.tsx        # Shell layout with responsive container
│   │   ├── Header.tsx            # Sticky navigation bar with mobile sheet
│   │   └── Footer.tsx            # Enterprise footer with compliance badges & navigation
│   ├── pages/                    # Marketing pages
│   │   ├── DemoRequest.tsx       # Interactive clinical pilot questionnaire & PACS picker
│   │   ├── Home.tsx              # Complete conversion narrative
│   │   ├── SecurityAndArch.tsx   # Air-gapped on-premise deep dive & whitepaper request
│   │   └── Solutions.tsx         # Modality-specific triage (CT, MRI, XR, CTPA)
│   ├── styles/                   # Tailwind CSS / Design Tokens (Medical Dark/Light Palette)
│   │   ├── index.css             # Base styles, scanline animations, glassmorphism panels
│   │   └── tokens.ts             # Medical palette, modality tags, and typography tokens
│   ├── App.tsx                   # Client-side router and state container
│   └── main.tsx                  # Application entry point
├── package.json                  # Vite, React, Tailwind CSS, Lucide dependencies
├── postcss.config.js             # PostCSS Tailwind plugins
├── tailwind.config.js            # Custom clinical color scales, glow shadows, and font configs
├── tsconfig.json                 # TypeScript compiler configuration
└── vite.config.ts                # Vite build bundler configuration
```

---

## 🎨 Design System & Medical Tokens

The UI adopts a **Clinical Obsidian & Diagnostic Teal** palette designed for dark radiology viewing reading rooms and executive hospital presentations:

| Token Name | Hex Code | Purpose |
|---|---|---|
| `clinical-950` | `#070B14` | Deep background (reduces eye strain in reading rooms) |
| `clinical-900` | `#0B132B` | Elevated card surfaces and control panes |
| `cyan-400` / `500` | `#06B6D4` | Primary brand accent & AI agent interaction nodes |
| `emerald-500` | `#10B981` | NVIDIA NeMo Guardrail safety validation status |
| `rose-500` | `#F43F5E` | STAT Critical triage flags (ICH, Tension Pneumothorax) |
| `amber-500` | `#F59E0B` | Priority Urgent queue items |

---

## 🚀 Running Locally

```bash
# Navigate to the marketing package
cd sims-radiology-marketing

# Install dependencies
npm install

# Run Vite development server
npm run dev

# Build for production
npm run build
```
