/**
 * Radiologist Workbench Layout (A2UI Presentation View).
 * Responsive layout containing:
 * - Header with agent stream connection indicator and clinician profile
 * - Worklist table with status indicators and modality filters
 * - Study launcher bar
 * - Case Concierge AI clinical context & prior study comparisons
 * - SHAP explainability risk breakdown
 * - Structured Diagnostic Report Editor with revision history and cryptographic sign-off
 * - Operational Telemetry dashboard view
 */
import { LitElement, html, css } from "lit";
import { a2uiEngine } from "../a2ui_engine.js";

export class RadiologistWorkbench extends LitElement {
  static styles = css`
    :host {
      display: block;
      min-height: 100vh;
      background: #0b1120;
      color: #f8fafc;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .topbar {
      background: #0f172a;
      border-bottom: 1px solid #1e293b;
      padding: 0.75rem 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 50;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .brand-logo {
      font-size: 1.4rem;
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #38bdf8;
    }
    .brand-subtitle {
      font-size: 0.75rem;
      color: #94a3b8;
    }
    .topbar-center {
      display: flex;
      gap: 0.5rem;
    }
    .nav-btn {
      background: #1e293b;
      border: 1px solid #334155;
      color: #cbd5e1;
      padding: 0.4rem 0.85rem;
      border-radius: 6px;
      font-size: 0.825rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .nav-btn:hover {
      background: #334155;
      color: #fff;
    }
    .nav-btn.active {
      background: #0284c7;
      border-color: #38bdf8;
      color: #fff;
    }
    .topbar-right {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      background: #064e3b;
      color: #6ee7b7;
      border: 1px solid #059669;
    }
    .status-pill.disconnected {
      background: #450a0a;
      color: #fca5a5;
      border-color: #dc2626;
    }
    .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #34d399;
    }
    .status-pill.disconnected .status-dot {
      background: #ef4444;
    }
    .user-profile {
      font-size: 0.8rem;
      text-align: right;
    }
    .user-name {
      font-weight: 700;
      color: #f1f5f9;
    }
    .user-role {
      font-size: 0.7rem;
      color: #38bdf8;
    }

    /* Main Container */
    .container {
      max-width: 1600px;
      margin: 0 auto;
      padding: 1.25rem;
    }

    /* Study Launcher Bar */
    .study-launcher {
      background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 0.85rem 1.25rem;
      margin-bottom: 1.25rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.75rem;
    }
    .study-meta {
      display: flex;
      align-items: center;
      gap: 1.25rem;
    }
    .study-id {
      font-size: 1.05rem;
      font-weight: 800;
      color: #38bdf8;
    }
    .launcher-actions {
      display: flex;
      gap: 0.5rem;
    }
    .btn {
      padding: 0.45rem 0.85rem;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      border: none;
      transition: all 0.15s ease;
    }
    .btn-primary {
      background: #0284c7;
      color: #fff;
    }
    .btn-primary:hover {
      background: #0369a1;
    }
    .btn-secondary {
      background: #334155;
      color: #e2e8f0;
      border: 1px solid #475569;
    }
    .btn-secondary:hover {
      background: #475569;
    }

    /* Responsive Grid */
    .workbench-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.25rem;
    }
    @media (max-width: 1080px) {
      .workbench-grid {
        grid-template-columns: 1fr;
      }
    }
    .left-col {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .right-col {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }

    /* Notification banner */
    .notification-toast {
      background: #064e3b;
      border: 1px solid #059669;
      color: #a7f3d0;
      padding: 0.65rem 1rem;
      border-radius: 6px;
      font-size: 0.825rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
  `;

  static get properties() {
    return {
      activeView: { state: true },
      sseConnected: { state: true },
      selectedWorkItem: { state: true },
      conciergeData: { state: true },
      shapData: { state: true },
      notificationMessage: { state: true },
    };
  }

  constructor() {
    super();
    this.activeView = "workbench";
    this.sseConnected = false;
    this.selectedWorkItem = {
      work_item_id: "WI-001",
      study_id: "STUDY-001",
      modality: "CT",
      priority: "STAT",
      state: "draft_ready",
      assigned_radiologist_id: "Dr. Sarah Jenkins MD",
      version: 2,
    };
    this.conciergeData = {
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
    this.shapData = {
      work_item_id: "WI-001",
      predicted_sla_breach_probability: 0.22,
      base_expected_value: 0.48,
      top_drivers: [
        { feature: "modality_complexity_score", attribution: 0.12, impact: "INCREASES_RISK" },
        { feature: "emergency_volume_surge_index", attribution: 0.08, impact: "INCREASES_RISK" },
        { feature: "elapsed_turnaround_ratio", attribution: -0.15, impact: "DECREASES_RISK" },
      ],
      recommendation:
        "LOW RISK (22.0%): Operational queue throughput is currently within normal clinical limits.",
    };
    this.notificationMessage = null;
  }

  connectedCallback() {
    super.connectedCallback();

    // Initialize A2UI Protocol Engine
    a2uiEngine.init();

    // Listen to SSE connection updates
    a2uiEngine.on("connection", ({ status }) => {
      this.sseConnected = status === "connected";
    });

    // Listen to streaming data updates from Deep Agents
    a2uiEngine.on("conciergeUpdate", (data) => {
      this.conciergeData = { ...this.conciergeData, ...data };
    });

    a2uiEngine.on("explainabilityUpdate", (data) => {
      this.shapData = { ...this.shapData, ...data };
    });

    // Listen to component events
    this.addEventListener("work-item-selected", (e) => {
      this._handleWorkItemSelected(e.detail);
    });

    this.addEventListener("generate-ai-draft", () => {
      this._handleAiDraft();
    });

    this.addEventListener("report-signed", (e) => {
      this._handleReportSigned(e.detail);
    });

    this.addEventListener("open-study-viewer", () => {
      this.activeView = "viewer";
    });
  }

  _handleWorkItemSelected(item) {
    this.selectedWorkItem = item;
    this.notificationMessage = `Loaded active study ${item.study_id} (${item.modality} - ${item.priority})`;
    setTimeout(() => {
      this.notificationMessage = null;
    }, 4000);

    // Request agent stream focus on this work item
    a2uiEngine.connectStream(item.work_item_id);
  }

  _handleAiDraft() {
    this.notificationMessage = "✨ Deep Agents generated structured report draft for clinical review.";
    setTimeout(() => {
      this.notificationMessage = null;
    }, 4000);
  }

  _handleReportSigned(detail) {
    this.selectedWorkItem = {
      ...this.selectedWorkItem,
      state: "finalized",
    };
    this.notificationMessage = `🔒 Cryptographic signature applied (SHA256: ${detail.signatureHash.substring(0, 16)}...). Report finalized.`;
    setTimeout(() => {
      this.notificationMessage = null;
    }, 6000);
  }

  render() {
    return html`
      <div>
        <!-- Top Application Navigation Bar -->
        <header class="topbar">
          <div class="brand">
            <span class="brand-logo">☢️</span>
            <div>
              <div class="brand-title">SIMS Radiology AI</div>
              <div class="brand-subtitle">Agentic Operating Platform · A2UI Protocol</div>
            </div>
          </div>

          <div class="topbar-center">
            <button
              class="nav-btn ${this.activeView === "workbench" ? "active" : ""}"
              @click=${() => (this.activeView = "workbench")}
            >
              📋 Clinical Workbench
            </button>
            <button
              class="nav-btn ${this.activeView === "viewer" ? "active" : ""}"
              @click=${() => (this.activeView = "viewer")}
            >
              🔬 DICOMweb Viewer
            </button>
            <button
              class="nav-btn ${this.activeView === "metrics" ? "active" : ""}"
              @click=${() => (this.activeView = "metrics")}
            >
              📊 Telemetry & Metrics
            </button>
          </div>

          <div class="topbar-right">
            <div class="status-pill ${this.sseConnected ? "" : "disconnected"}">
              <span class="status-dot"></span>
              ${this.sseConnected ? "DeepAgents SSE Live" : "Connecting..."}
            </div>
            <div class="user-profile">
              <div class="user-name">Dr. Sarah Jenkins MD</div>
              <div class="user-role">Reporting Radiologist</div>
            </div>
          </div>
        </header>

        <!-- Main Workspace Container -->
        <main class="container">
          ${this.notificationMessage
            ? html`
                <div class="notification-toast">
                  <span>${this.notificationMessage}</span>
                  <button
                    style="background:none; border:none; color:inherit; cursor:pointer;"
                    @click=${() => (this.notificationMessage = null)}
                  >
                    ✕
                  </button>
                </div>
              `
            : ""}

          <!-- VIEW: Full Metrics View -->
          ${this.activeView === "metrics"
            ? html`<metrics-dashboard-widget></metrics-dashboard-widget>`
            : ""}

          <!-- VIEW: DICOM Study Viewer View -->
          ${this.activeView === "viewer"
            ? html`
                <radiology-study-viewer
                  .studyInstanceUid=${this.selectedWorkItem.study_id}
                  .modality=${this.selectedWorkItem.modality}
                ></radiology-study-viewer>
              `
            : ""}

          <!-- VIEW: Radiologist Workbench Main Split View -->
          ${this.activeView === "workbench"
            ? html`
                <!-- Study Launcher Header Bar -->
                <div class="study-launcher">
                  <div class="study-meta">
                    <div>
                      <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">
                        Active Clinical Task
                      </span>
                      <div class="study-id">
                        ${this.selectedWorkItem.work_item_id} · ${this.selectedWorkItem.study_id}
                      </div>
                    </div>
                    <div>
                      <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">
                        Modality & Priority
                      </span>
                      <div style="font-weight: 700; color: #f1f5f9;">
                        ${this.selectedWorkItem.modality} (${this.selectedWorkItem.priority})
                      </div>
                    </div>
                    <div>
                      <span style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">
                        Workflow Status
                      </span>
                      <div style="font-weight: 700; color: #38bdf8;">
                        ${this.selectedWorkItem.state.toUpperCase()}
                      </div>
                    </div>
                  </div>

                  <div class="launcher-actions">
                    <button
                      class="btn btn-primary"
                      @click=${() => (this.activeView = "viewer")}
                    >
                      👁️ Launch DICOMweb Viewer
                    </button>
                    <button
                      class="btn btn-secondary"
                      @click=${() => (this.activeView = "metrics")}
                    >
                      📈 Department TAT
                    </button>
                  </div>
                </div>

                <!-- Two-Column Responsive Layout -->
                <div class="workbench-grid">
                  <!-- Left Column: Worklist & Explainability -->
                  <div class="left-col">
                    <worklist-table
                      .selectedWorkItemId=${this.selectedWorkItem.work_item_id}
                    ></worklist-table>
                    <explainability-widget .data=${this.shapData}></explainability-widget>
                  </div>

                  <!-- Right Column: Case Concierge AI & Report Editor -->
                  <div class="right-col">
                    <case-concierge-panel .data=${this.conciergeData}></case-concierge-panel>
                    <report-editor-widget
                      .reportId=${"REP-" + this.selectedWorkItem.work_item_id}
                      .status=${this.selectedWorkItem.state === "finalized"
                        ? "SIGNED"
                        : "DRAFT"}
                    ></report-editor-widget>
                  </div>
                </div>
              `
            : ""}
        </main>
      </div>
    `;
  }
}

if (!customElements.get("radiologist-workbench")) {
  customElements.define("radiologist-workbench", RadiologistWorkbench);
}
