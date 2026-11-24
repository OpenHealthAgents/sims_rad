var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
/**
 * ExplainabilityWidget Web Component (A2UI Catalog Widget).
 * Visualizes SHAP feature importance bars for study priority,
 * queue delay attribution, and SLA breach risk predictions.
 */
import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
let ExplainabilityWidget = class ExplainabilityWidget extends LitElement {
    constructor() {
        super(...arguments);
        this.data = {
            work_item_id: "WI-001",
            predicted_sla_breach_probability: 0.22,
            base_expected_value: 0.48,
            top_drivers: [
                {
                    feature: "modality_complexity_score",
                    attribution: 0.12,
                    impact: "INCREASES_RISK",
                },
                {
                    feature: "emergency_volume_surge_index",
                    attribution: 0.08,
                    impact: "INCREASES_RISK",
                },
                {
                    feature: "elapsed_turnaround_ratio",
                    attribution: -0.15,
                    impact: "DECREASES_RISK",
                },
                {
                    feature: "unassigned_duration_minutes",
                    attribution: 0.05,
                    impact: "INCREASES_RISK",
                },
                {
                    feature: "off_hours_shift_flag",
                    attribution: -0.04,
                    impact: "DECREASES_RISK",
                },
            ],
            recommendation: "LOW RISK (22.0%): Operational queue throughput is currently within normal clinical limits.",
        };
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
    .shap-badge {
      background: #4c1d95;
      color: #e9d5ff;
      font-size: 0.7rem;
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .metrics-summary {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.75rem;
      margin-bottom: 1.25rem;
    }
    .stat-card {
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 0.75rem;
      text-align: center;
    }
    .stat-val {
      font-size: 1.35rem;
      font-weight: 800;
      color: #38bdf8;
    }
    .stat-val.high-risk {
      color: #f43f5e;
    }
    .stat-val.low-risk {
      color: #34d399;
    }
    .stat-label {
      font-size: 0.7rem;
      color: #94a3b8;
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.04em;
      margin-top: 0.25rem;
    }
    .chart-container {
      margin-bottom: 1rem;
    }
    .chart-title {
      font-size: 0.75rem;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.75rem;
    }
    .factor-row {
      margin-bottom: 0.75rem;
    }
    .factor-labels {
      display: flex;
      justify-content: space-between;
      font-size: 0.78rem;
      margin-bottom: 0.25rem;
    }
    .factor-name {
      font-weight: 600;
      color: #e2e8f0;
    }
    .factor-attr {
      font-weight: 700;
      font-family: monospace;
    }
    .factor-attr.positive {
      color: #f87171;
    }
    .factor-attr.negative {
      color: #4ade80;
    }
    .bar-bg {
      height: 8px;
      background: #0f172a;
      border-radius: 4px;
      overflow: hidden;
      border: 1px solid #334155;
      position: relative;
    }
    .bar-fill {
      height: 100%;
      border-radius: 4px;
      transition: width 0.5s ease-out;
    }
    .bar-fill.danger {
      background: linear-gradient(90deg, #f97316, #ef4444);
    }
    .bar-fill.success {
      background: linear-gradient(90deg, #0ea5e9, #10b981);
    }
    .recommendation-card {
      background: #0f172a;
      border-left: 3px solid #a855f7;
      padding: 0.75rem;
      border-radius: 0 6px 6px 0;
      font-size: 0.82rem;
      line-height: 1.4;
      color: #cbd5e1;
    }
  `; }
    render() {
        const riskProb = this.data.predicted_sla_breach_probability ?? 0.22;
        const riskPct = Math.round(riskProb * 100);
        const drivers = this.data.top_drivers || [];
        return html `
      <div>
        <div class="widget-header">
          <div class="title">
            <span>📊 SLA Risk & SHAP Explainability</span>
          </div>
          <span class="shap-badge">SHAP v0.46.0</span>
        </div>

        <div class="metrics-summary">
          <div class="stat-card">
            <div class="stat-val ${riskPct > 50 ? "high-risk" : "low-risk"}">
              ${riskPct}%
            </div>
            <div class="stat-label">SLA Breach Risk</div>
          </div>
          <div class="stat-card">
            <div class="stat-val">
              ${this.data.base_expected_value ?? 0.48}
            </div>
            <div class="stat-label">Model Base E[X]</div>
          </div>
        </div>

        <div class="chart-container">
          <div class="chart-title">Feature Attribution Vectors</div>
          ${drivers.map((d) => {
            const isPos = d.attribution > 0;
            const widthPct = Math.min(100, Math.abs(d.attribution) * 350);
            return html `
              <div class="factor-row">
                <div class="factor-labels">
                  <span class="factor-name">${this._formatFeatureName(d.feature)}</span>
                  <span class="factor-attr ${isPos ? "positive" : "negative"}">
                    ${isPos ? "+" : ""}${d.attribution.toFixed(3)}
                  </span>
                </div>
                <div class="bar-bg">
                  <div
                    class="bar-fill ${isPos ? "danger" : "success"}"
                    style="width: ${widthPct}%;"
                  ></div>
                </div>
              </div>
            `;
        })}
        </div>

        <div class="recommendation-card">
          <strong style="color: #c084fc;">AI Operational Recommendation:</strong><br />
          ${this.data.recommendation || "Maintain active monitoring of queue capacity."}
        </div>
      </div>
    `;
    }
    _formatFeatureName(name) {
        return name
            .split("_")
            .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
            .join(" ");
    }
};
__decorate([
    property({ type: Object })
], ExplainabilityWidget.prototype, "data", void 0);
ExplainabilityWidget = __decorate([
    customElement("explainability-widget")
], ExplainabilityWidget);
export { ExplainabilityWidget };
