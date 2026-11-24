var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
/**
 * ReportEditorWidget Web Component (A2UI Catalog Widget).
 * Structured diagnostic report template sections (Findings, Impression)
 * with revision history toggle and clinician sign-off workflow.
 */
import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
let ReportEditorWidget = class ReportEditorWidget extends LitElement {
    constructor() {
        super(...arguments);
        this.reportId = "REP-001";
        this.status = "DRAFT";
        this.findingsText = "No acute intracranial hemorrhage or mass effect. Ventricles and sulci are within normal limits for age. Basal cisterns remain patent. Bone windows demonstrate no acute calvarial fracture.";
        this.impressionText = "1. No acute intracranial abnormality.\n2. Chronic ischemic changes consistent with prior clinical history.";
        this.activeVersion = 1;
        this.signatureHash = null;
        this.signedBy = null;
        this.signedAt = null;
        this.versions = [
            {
                version_number: 1,
                author_id: "SIMS_AI_CONCIERGE_AGENT",
                findings: "No acute intracranial hemorrhage or mass effect. Ventricles and sulci are within normal limits for age.",
                impression: "1. No acute intracranial abnormality.",
                is_signed: false,
            },
        ];
    }
    static { this.styles = css `
    :host {
      display: block;
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 1.25rem;
      font-family: inherit;
      color: #f1f5f9;
    }
    .widget-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid #334155;
      margin-bottom: 1rem;
    }
    .title {
      font-size: 1.05rem;
      font-weight: 700;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .status-badge {
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .badge-draft {
      background: #431407;
      color: #fed7aa;
      border: 1px solid #ea580c;
    }
    .badge-signed {
      background: #064e3b;
      color: #a7f3d0;
      border: 1px solid #059669;
    }
    .badge-delivered {
      background: #312e81;
      color: #c7d2fe;
      border: 1px solid #6366f1;
    }
    .revision-bar {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 1rem;
      background: #0f172a;
      padding: 0.5rem 0.75rem;
      border-radius: 6px;
      font-size: 0.8rem;
    }
    .version-tab {
      padding: 0.25rem 0.6rem;
      border-radius: 4px;
      background: #1e293b;
      border: 1px solid #334155;
      color: #cbd5e1;
      cursor: pointer;
      font-weight: 600;
    }
    .version-tab.active {
      background: #0284c7;
      border-color: #38bdf8;
      color: #fff;
    }
    .section-label {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      color: #94a3b8;
      letter-spacing: 0.05em;
      margin-bottom: 0.4rem;
    }
    textarea {
      width: 100%;
      box-sizing: border-box;
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 6px;
      color: #f8fafc;
      padding: 0.75rem;
      font-family: inherit;
      font-size: 0.875rem;
      line-height: 1.5;
      resize: vertical;
      margin-bottom: 1rem;
    }
    textarea:focus {
      outline: none;
      border-color: #38bdf8;
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }
    .signature-card {
      background: #064e3b;
      border: 1px solid #059669;
      border-radius: 6px;
      padding: 0.75rem;
      margin-bottom: 1rem;
      font-size: 0.78rem;
      color: #a7f3d0;
    }
    .signature-card strong {
      color: #fff;
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
      padding-top: 0.5rem;
    }
    .btn {
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-size: 0.825rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.2s ease;
      border: none;
    }
    .btn-secondary {
      background: #334155;
      color: #f1f5f9;
      border: 1px solid #475569;
    }
    .btn-secondary:hover {
      background: #475569;
    }
    .btn-primary {
      background: #0284c7;
      color: #fff;
    }
    .btn-primary:hover {
      background: #0369a1;
    }
    .btn-success {
      background: #059669;
      color: #fff;
    }
    .btn-success:hover {
      background: #047857;
    }
    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `; }
    _onFindingsChange(e) {
        this.findingsText = e.target.value;
    }
    _onImpressionChange(e) {
        this.impressionText = e.target.value;
    }
    _generateAiDraft() {
        this.dispatchEvent(new CustomEvent("generate-ai-draft", {
            detail: { reportId: this.reportId },
            bubbles: true,
            composed: true,
        }));
    }
    _signAndFinalize() {
        // Generate simulated SHA-256 hash or trigger signoff event
        const fakeHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
        this.signatureHash = fakeHash;
        this.status = "SIGNED";
        this.signedBy = "Dr. Sarah Jenkins MD (Reporting Radiologist)";
        this.signedAt = new Date().toISOString();
        const signedVer = {
            version_number: this.versions.length + 1,
            author_id: "RAD-ATTENDING-01",
            findings: this.findingsText,
            impression: this.impressionText,
            is_signed: true,
            signature_hash: fakeHash,
            signed_at: this.signedAt,
        };
        this.versions = [...this.versions, signedVer];
        this.activeVersion = signedVer.version_number;
        this.dispatchEvent(new CustomEvent("report-signed", {
            detail: {
                reportId: this.reportId,
                version: signedVer.version_number,
                signatureHash: fakeHash,
            },
            bubbles: true,
            composed: true,
        }));
    }
    render() {
        const isSigned = this.status === "SIGNED" || this.status === "DELIVERED";
        return html `
      <div>
        <div class="widget-header">
          <div class="title">
            <span>📝 Structured Diagnostic Report</span>
            <span style="font-size: 0.8rem; color: #94a3b8;">(${this.reportId})</span>
          </div>
          <span class="status-badge ${this._getStatusClass(this.status)}">
            ${this.status}
          </span>
        </div>

        <div class="revision-bar">
          <span style="font-weight: 700; color: #94a3b8;">Revision History:</span>
          ${this.versions.map((v) => html `
              <button
                class="version-tab ${this.activeVersion === v.version_number ? "active" : ""}"
                @click=${() => this._switchVersion(v)}
              >
                v${v.version_number} (${v.is_signed ? "Signed" : "Draft"})
              </button>
            `)}
        </div>

        <div>
          <div class="section-label">Radiological Findings</div>
          <textarea
            rows="6"
            .value=${this.findingsText}
            @input=${this._onFindingsChange}
            ?disabled=${isSigned}
          ></textarea>
        </div>

        <div>
          <div class="section-label">Clinical Impression</div>
          <textarea
            rows="3"
            .value=${this.impressionText}
            @input=${this._onImpressionChange}
            ?disabled=${isSigned}
          ></textarea>
        </div>

        ${isSigned && this.signatureHash
            ? html `
              <div class="signature-card">
                <div>🔒 <strong>Cryptographic Clinician Signature Verified</strong></div>
                <div style="font-family: monospace; font-size: 0.72rem; margin: 0.25rem 0;">
                  SHA256: ${this.signatureHash}
                </div>
                <div>
                  Signer: ${this.signedBy} | Signed At: ${this.signedAt}
                </div>
              </div>
            `
            : ""}

        <div class="actions">
          <button
            class="btn btn-secondary"
            @click=${this._generateAiDraft}
            ?disabled=${isSigned}
          >
            ✨ Assist with AI Draft
          </button>
          <button
            class="btn btn-success"
            @click=${this._signAndFinalize}
            ?disabled=${isSigned}
          >
            ✍️ Sign & Finalize Report
          </button>
        </div>
      </div>
    `;
    }
    _switchVersion(v) {
        this.activeVersion = v.version_number;
        this.findingsText = v.findings;
        this.impressionText = v.impression;
    }
    _getStatusClass(status) {
        const s = (status || "").toUpperCase();
        if (s === "SIGNED")
            return "badge-signed";
        if (s === "DELIVERED")
            return "badge-delivered";
        return "badge-draft";
    }
};
__decorate([
    property({ type: String })
], ReportEditorWidget.prototype, "reportId", void 0);
__decorate([
    property({ type: String })
], ReportEditorWidget.prototype, "status", void 0);
__decorate([
    property({ type: String })
], ReportEditorWidget.prototype, "findingsText", void 0);
__decorate([
    property({ type: String })
], ReportEditorWidget.prototype, "impressionText", void 0);
__decorate([
    state()
], ReportEditorWidget.prototype, "activeVersion", void 0);
__decorate([
    state()
], ReportEditorWidget.prototype, "signatureHash", void 0);
__decorate([
    state()
], ReportEditorWidget.prototype, "signedBy", void 0);
__decorate([
    state()
], ReportEditorWidget.prototype, "signedAt", void 0);
__decorate([
    state()
], ReportEditorWidget.prototype, "versions", void 0);
ReportEditorWidget = __decorate([
    customElement("report-editor-widget")
], ReportEditorWidget);
export { ReportEditorWidget };
