/**
 * CaseConciergePanel Web Component (A2UI Catalog Widget).
 * Displays Deep Agents prepared clinical context, referral questions,
 * prior study links, and clinical safety alerts.
 */
import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";

export interface ConciergeData {
  work_item_id?: string;
  patient_name?: string;
  mrn?: string;
  study_type?: string;
  referral_question?: string;
  clinical_alerts?: string[];
  relevant_priors_summary?: string;
  patient_context_summary?: string;
}

@customElement("case-concierge-panel")
export class CaseConciergePanel extends LitElement {
  static override styles = css`
    :host {
      display: block;
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 1.25rem;
      font-family: inherit;
      color: #f1f5f9;
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid #334155;
    }
    .title {
      font-size: 1.05rem;
      font-weight: 700;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .ai-badge {
      background: #0369a1;
      color: #e0f2fe;
      font-size: 0.7rem;
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .section {
      margin-bottom: 1rem;
    }
    .section-title {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      color: #94a3b8;
      letter-spacing: 0.05em;
      margin-bottom: 0.35rem;
    }
    .referral-box {
      background: #0f172a;
      border-left: 3px solid #38bdf8;
      padding: 0.75rem 1rem;
      border-radius: 0 6px 6px 0;
      font-size: 0.9rem;
      line-height: 1.45;
      color: #e2e8f0;
    }
    .alert-card {
      background: #450a0a;
      border: 1px solid #991b1b;
      border-left: 4px solid #ef4444;
      padding: 0.6rem 0.85rem;
      border-radius: 6px;
      margin-bottom: 0.5rem;
      font-size: 0.82rem;
      color: #fecaca;
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
    }
    .alert-card.warning {
      background: #451a03;
      border-color: #92400e;
      border-left-color: #f59e0b;
      color: #fde68a;
    }
    .priors-box {
      background: #0f172a;
      border: 1px solid #334155;
      padding: 0.75rem;
      border-radius: 6px;
      font-size: 0.85rem;
      line-height: 1.4;
      color: #cbd5e1;
    }
    .prior-link {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      color: #38bdf8;
      text-decoration: none;
      font-weight: 600;
      font-size: 0.8rem;
      margin-top: 0.4rem;
      cursor: pointer;
    }
    .prior-link:hover {
      text-decoration: underline;
    }
    .demographics {
      display: flex;
      gap: 1rem;
      font-size: 0.8rem;
      color: #94a3b8;
      margin-bottom: 0.75rem;
    }
    .demographics strong {
      color: #e2e8f0;
    }
  `;

  @property({ type: Object })
  data: ConciergeData = {
    work_item_id: "WI-001",
    patient_name: "Eleanor Vance (Age 64, F)",
    mrn: "MRN-1001",
    study_type: "CT Head Non-Contrast",
    referral_question:
      "Rule out acute intracranial hemorrhage following fall with blunt head trauma.",
    clinical_alerts: [
      "CRITICAL: Patient on high-dose anticoagulant therapy (Warfarin, INR 2.8).",
      "ALERT: Prior ischemic stroke noted in 2024 left MCA territory.",
    ],
    relevant_priors_summary:
      "CT Head (2024-03-12): Encephalomalacia in left middle cerebral artery territory, unchanged ventricular size.",
    patient_context_summary:
      "Hypertension, chronic atrial fibrillation, recent syncopal episode.",
  };

  override render() {
    const alerts = this.data.clinical_alerts || [];

    return html`
      <div>
        <div class="panel-header">
          <div class="title">
            <span>🧠 Case Concierge AI</span>
            <span class="ai-badge">DeepAgents Active</span>
          </div>
          <span style="font-size: 0.8rem; color: #38bdf8; font-weight: 600;">
            ${this.data.work_item_id || "WI-001"}
          </span>
        </div>

        <div class="demographics">
          <div>Patient: <strong>${this.data.patient_name || "Eleanor Vance"}</strong></div>
          <div>MRN: <strong>${this.data.mrn || "MRN-1001"}</strong></div>
          <div>Study: <strong>${this.data.study_type || "CT Head"}</strong></div>
        </div>

        <div class="section">
          <div class="section-title">Clinical Referral Question</div>
          <div class="referral-box">
            ${this.data.referral_question || "Diagnostic evaluation requested."}
          </div>
        </div>

        ${alerts.length > 0
          ? html`
              <div class="section">
                <div class="section-title">Clinical Safety Alerts</div>
                ${alerts.map(
                  (alert) => html`
                    <div
                      class="alert-card ${alert.toLowerCase().includes("critical")
                        ? ""
                        : "warning"}"
                    >
                      <span>⚠️</span>
                      <div>${alert}</div>
                    </div>
                  `
                )}
              </div>
            `
          : ""}

        <div class="section">
          <div class="section-title">Relevant Prior Imaging</div>
          <div class="priors-box">
            <div>${this.data.relevant_priors_summary || "No prior imaging on record."}</div>
            <a class="prior-link" @click=${this._viewPriorStudy}>
              🔍 Open Prior Study in DICOMweb Viewer →
            </a>
          </div>
        </div>

        <div class="section" style="margin-bottom: 0;">
          <div class="section-title">Synthesized Clinical History</div>
          <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.4;">
            ${this.data.patient_context_summary || "No prior history documented."}
          </div>
        </div>
      </div>
    `;
  }

  private _viewPriorStudy(e: Event) {
    e.preventDefault();
    this.dispatchEvent(
      new CustomEvent("open-study-viewer", {
        detail: { study_uid: "1.2.840.10008.5.1.4.1.1.2.20240312.001" },
        bubbles: true,
        composed: true,
      })
    );
  }
}
