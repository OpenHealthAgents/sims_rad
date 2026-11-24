/**
 * MetricsDashboardWidget Web Component (A2UI Catalog Widget).
 * Visualizes operational telemetry: average TAT, modality volume breakdown,
 * SLA compliance rate, and queue exception counts.
 */
import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";

export interface MetricsData {
  total_work_items: number;
  total_studies_ingested: number;
  average_turnaround_time_minutes: number;
  median_turnaround_time_minutes: number;
  sla_compliance_rate_percent: number;
  exception_count: number;
  volume_by_modality: {
    CT: number;
    MRI: number;
    XRAY: number;
    OTHER: number;
  };
  volume_by_priority: {
    STAT: number;
    URGENT: number;
    ROUTINE: number;
  };
}

@customElement("metrics-dashboard-widget")
export class MetricsDashboardWidget extends LitElement {
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
    .telemetry-badge {
      background: #1e3a5f;
      color: #38bdf8;
      font-size: 0.7rem;
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 0.75rem;
      margin-bottom: 1.25rem;
    }
    .kpi-card {
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 0.75rem;
      text-align: center;
    }
    .kpi-val {
      font-size: 1.35rem;
      font-weight: 800;
      color: #38bdf8;
    }
    .kpi-label {
      font-size: 0.68rem;
      color: #94a3b8;
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.04em;
      margin-top: 0.2rem;
    }
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }
    .chart-box {
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 0.75rem 1rem;
    }
    .chart-box-title {
      font-size: 0.75rem;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.75rem;
    }
    .bar-row {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.5rem;
      font-size: 0.78rem;
    }
    .bar-label {
      width: 45px;
      font-weight: 600;
      color: #cbd5e1;
    }
    .bar-track {
      flex: 1;
      height: 10px;
      background: #1e293b;
      border-radius: 5px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      border-radius: 5px;
    }
    .bar-count {
      width: 30px;
      text-align: right;
      font-weight: 700;
      color: #94a3b8;
      font-family: monospace;
    }
  `;

  @property({ type: Object })
  metrics: MetricsData = {
    total_work_items: 24,
    total_studies_ingested: 28,
    average_turnaround_time_minutes: 22.4,
    median_turnaround_time_minutes: 16.5,
    sla_compliance_rate_percent: 95.8,
    exception_count: 1,
    volume_by_modality: {
      CT: 14,
      MRI: 6,
      XRAY: 4,
      OTHER: 0,
    },
    volume_by_priority: {
      STAT: 4,
      URGENT: 8,
      ROUTINE: 12,
    },
  };

  override render() {
    const totalMod =
      (this.metrics.volume_by_modality?.CT || 0) +
      (this.metrics.volume_by_modality?.MRI || 0) +
      (this.metrics.volume_by_modality?.XRAY || 0) || 1;

    const totalPrio =
      (this.metrics.volume_by_priority?.STAT || 0) +
      (this.metrics.volume_by_priority?.URGENT || 0) +
      (this.metrics.volume_by_priority?.ROUTINE || 0) || 1;

    return html`
      <div>
        <div class="widget-header">
          <div class="title">
            <span>📈 Department Operational Telemetry</span>
          </div>
          <span class="telemetry-badge">Real-time Metrics</span>
        </div>

        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-val" style="color: #38bdf8;">
              ${this.metrics.average_turnaround_time_minutes}m
            </div>
            <div class="kpi-label">Average TAT</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-val" style="color: #34d399;">
              ${this.metrics.sla_compliance_rate_percent}%
            </div>
            <div class="kpi-label">SLA Compliance</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-val" style="color: #f59e0b;">
              ${this.metrics.total_work_items}
            </div>
            <div class="kpi-label">Active Worklist</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-val" style="color: #f43f5e;">
              ${this.metrics.exception_count}
            </div>
            <div class="kpi-label">Exceptions</div>
          </div>
        </div>

        <div class="charts-row">
          <div class="chart-box">
            <div class="chart-box-title">Volume by Modality</div>
            <div class="bar-row">
              <span class="bar-label">CT</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  style="width: ${(this.metrics.volume_by_modality.CT / totalMod) * 100}%; background: #38bdf8;"
                ></div>
              </div>
              <span class="bar-count">${this.metrics.volume_by_modality.CT}</span>
            </div>
            <div class="bar-row">
              <span class="bar-label">MRI</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  style="width: ${(this.metrics.volume_by_modality.MRI / totalMod) * 100}%; background: #a855f7;"
                ></div>
              </div>
              <span class="bar-count">${this.metrics.volume_by_modality.MRI}</span>
            </div>
            <div class="bar-row">
              <span class="bar-label">XRAY</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  style="width: ${(this.metrics.volume_by_modality.XRAY / totalMod) * 100}%; background: #10b981;"
                ></div>
              </div>
              <span class="bar-count">${this.metrics.volume_by_modality.XRAY}</span>
            </div>
          </div>

          <div class="chart-box">
            <div class="chart-box-title">Queue Priority Distribution</div>
            <div class="bar-row">
              <span class="bar-label">STAT</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  style="width: ${(this.metrics.volume_by_priority.STAT / totalPrio) * 100}%; background: #ef4444;"
                ></div>
              </div>
              <span class="bar-count">${this.metrics.volume_by_priority.STAT}</span>
            </div>
            <div class="bar-row">
              <span class="bar-label">URG</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  style="width: ${(this.metrics.volume_by_priority.URGENT / totalPrio) * 100}%; background: #f59e0b;"
                ></div>
              </div>
              <span class="bar-count">${this.metrics.volume_by_priority.URGENT}</span>
            </div>
            <div class="bar-row">
              <span class="bar-label">ROUT</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  style="width: ${(this.metrics.volume_by_priority.ROUTINE / totalPrio) * 100}%; background: #0ea5e9;"
                ></div>
              </div>
              <span class="bar-count">${this.metrics.volume_by_priority.ROUTINE}</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }
}
