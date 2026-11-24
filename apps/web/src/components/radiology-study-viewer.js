var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
let RadiologyStudyViewer = class RadiologyStudyViewer extends LitElement {
    constructor() {
        super(...arguments);
        this.studyInstanceUid = "1.2.840.10008.5.1.4.1.1.2.20261124.001";
        this.modality = "CT";
        this.findings = [
            {
                id: "f-101",
                findingType: "Intracranial Hemorrhage",
                confidence: 0.94,
                location: "Right temporal lobe",
                status: "escalated",
            },
            {
                id: "f-102",
                findingType: "Midline Shift",
                confidence: 0.88,
                location: "Subfalcine 3.2mm",
                status: "escalated",
            },
        ];
    }
    static { this.styles = css `
    :host {
      display: block;
      background: #1e293b;
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
      color: #e2e8f0;
    }
    h1 {
      margin-top: 0;
      color: #38bdf8;
      font-size: 1.5rem;
      border-bottom: 1px solid #334155;
      padding-bottom: 0.75rem;
    }
    .grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 1.5rem;
      margin-top: 1rem;
    }
    .panel {
      background: #0f172a;
      padding: 1rem;
      border-radius: 8px;
      border: 1px solid #334155;
    }
    .finding-card {
      background: #1e293b;
      margin-bottom: 0.75rem;
      padding: 0.75rem;
      border-radius: 6px;
      border-left: 4px solid #38bdf8;
    }
    .finding-card.escalated {
      border-left-color: #f43f5e;
    }
    .badge {
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      background: #334155;
      color: #94a3b8;
    }
    .badge.high-conf {
      background: #065f46;
      color: #6ee7b7;
    }
  `; }
    render() {
        return html `
      <div>
        <h1>SIMS Radiology AI Workstation</h1>
        <div class="grid">
          <div class="panel">
            <h3>Active DICOM Study: ${this.studyInstanceUid}</h3>
            <p>Modality: <strong>${this.modality}</strong></p>
            <p>Protocol: Non-Contrast Head CT | DeepAgents Analysis Pipeline</p>
            <div style="height: 240px; background: #020617; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #64748b;">
              [DICOM Viewport - WebGL Renderer / A2UI Surface]
            </div>
          </div>
          <div class="panel">
            <h3>Agentic Findings & SHAP Attribution</h3>
            ${this.findings.map((f) => html `
                <div class="finding-card ${f.status}">
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>${f.findingType}</strong>
                    <span class="badge ${f.confidence > 0.9 ? 'high-conf' : ''}">
                      ${Math.round(f.confidence * 100)}% Conf
                    </span>
                  </div>
                  <p style="margin: 0.25rem 0 0; font-size: 0.875rem; color: #94a3b8;">
                    Location: ${f.location}
                  </p>
                </div>
              `)}
          </div>
        </div>
      </div>
    `;
    }
};
__decorate([
    property({ type: String })
], RadiologyStudyViewer.prototype, "studyInstanceUid", void 0);
__decorate([
    property({ type: String })
], RadiologyStudyViewer.prototype, "modality", void 0);
__decorate([
    state()
], RadiologyStudyViewer.prototype, "findings", void 0);
RadiologyStudyViewer = __decorate([
    customElement("radiology-study-viewer")
], RadiologyStudyViewer);
export { RadiologyStudyViewer };
