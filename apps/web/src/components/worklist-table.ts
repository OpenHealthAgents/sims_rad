/**
 * WorklistTable Web Component (A2UI Catalog Widget).
 * Sortable, filterable worklist with modality filters and clinical status indicators.
 */
import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";

export interface WorkItemData {
  work_item_id: string;
  study_id: string;
  modality: string;
  priority: "STAT" | "URGENT" | "ROUTINE" | string;
  state: string;
  assigned_radiologist_id?: string | null;
  sla_deadline?: string;
  version?: number;
}

@customElement("worklist-table")
export class WorklistTable extends LitElement {
  static override styles = css`
    :host {
      display: block;
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 10px;
      overflow: hidden;
      font-family: inherit;
      color: #f1f5f9;
    }
    .header-bar {
      padding: 0.85rem 1.25rem;
      background: #0f172a;
      border-bottom: 1px solid #334155;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.75rem;
    }
    .title {
      font-size: 1rem;
      font-weight: 700;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .controls {
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }
    .filter-btn {
      background: #334155;
      color: #cbd5e1;
      border: 1px solid #475569;
      border-radius: 6px;
      padding: 0.35rem 0.75rem;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .filter-btn:hover {
      background: #475569;
      color: #fff;
    }
    .filter-btn.active {
      background: #0284c7;
      border-color: #38bdf8;
      color: #fff;
    }
    .table-container {
      max-height: 420px;
      overflow-y: auto;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.85rem;
    }
    th {
      background: #1e293b;
      color: #94a3b8;
      padding: 0.75rem 1rem;
      font-weight: 600;
      border-bottom: 2px solid #334155;
      position: sticky;
      top: 0;
      z-index: 1;
    }
    td {
      padding: 0.75rem 1rem;
      border-bottom: 1px solid #334155;
      vertical-align: middle;
    }
    tr {
      cursor: pointer;
      transition: background 0.15s ease;
    }
    tr:hover {
      background: #273549;
    }
    tr.selected {
      background: #0c4a6e;
      border-left: 4px solid #38bdf8;
    }
    .badge {
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 4px;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .priority-stat {
      background: #881337;
      color: #fecdd3;
      border: 1px solid #e11d48;
      animation: pulse 2s infinite;
    }
    .priority-urgent {
      background: #78350f;
      color: #fef08a;
      border: 1px solid #d97706;
    }
    .priority-routine {
      background: #1e3a5f;
      color: #bae6fd;
      border: 1px solid #0284c7;
    }
    .badge-state {
      background: #334155;
      color: #cbd5e1;
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
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.75; }
    }
  `;

  @property({ type: Array })
  items: WorkItemData[] = [
    {
      work_item_id: "WI-001",
      study_id: "STUDY-001",
      modality: "CT",
      priority: "STAT",
      state: "draft_ready",
      assigned_radiologist_id: "RAD-001",
      sla_deadline: "2026-11-24T17:00:00Z",
      version: 2,
    },
    {
      work_item_id: "WI-002",
      study_id: "STUDY-002",
      modality: "XRAY",
      priority: "URGENT",
      state: "assigned",
      assigned_radiologist_id: "RAD-002",
      sla_deadline: "2026-11-24T19:30:00Z",
      version: 1,
    },
    {
      work_item_id: "WI-003",
      study_id: "STUDY-003",
      modality: "MRI",
      priority: "ROUTINE",
      state: "finalized",
      assigned_radiologist_id: "RAD-001",
      sla_deadline: "2026-11-25T08:00:00Z",
      version: 3,
    },
  ];

  @property({ type: String })
  selectedWorkItemId = "WI-001";

  @state()
  activeModalityFilter = "ALL";

  private _selectItem(item: WorkItemData) {
    this.selectedWorkItemId = item.work_item_id;
    this.dispatchEvent(
      new CustomEvent("work-item-selected", {
        detail: item,
        bubbles: true,
        composed: true,
      })
    );
  }

  private _setFilter(filter: string) {
    this.activeModalityFilter = filter;
  }

  override render() {
    const filteredItems =
      this.activeModalityFilter === "ALL"
        ? this.items
        : this.items.filter((i) => i.modality.toUpperCase() === this.activeModalityFilter);

    return html`
      <div>
        <div class="header-bar">
          <div class="title">
            <span>📋 Clinical Worklist</span>
            <span style="font-size: 0.8rem; color: #94a3b8;">(${filteredItems.length} studies)</span>
          </div>
          <div class="controls">
            ${["ALL", "CT", "MRI", "XRAY"].map(
              (mod) => html`
                <button
                  class="filter-btn ${this.activeModalityFilter === mod ? "active" : ""}"
                  @click=${() => this._setFilter(mod)}
                >
                  ${mod}
                </button>
              `
            )}
          </div>
        </div>

        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Priority</th>
                <th>Work Item ID</th>
                <th>Modality</th>
                <th>Study ID</th>
                <th>State</th>
                <th>Assigned To</th>
              </tr>
            </thead>
            <tbody>
              ${filteredItems.map(
                (item) => html`
                  <tr
                    class="${item.work_item_id === this.selectedWorkItemId ? "selected" : ""}"
                    @click=${() => this._selectItem(item)}
                  >
                    <td>
                      <span class="badge ${this._getPriorityClass(item.priority)}">
                        ${item.priority}
                      </span>
                    </td>
                    <td><strong>${item.work_item_id}</strong></td>
                    <td>
                      <span style="font-weight: 600; color: #38bdf8;">${item.modality}</span>
                    </td>
                    <td>${item.study_id}</td>
                    <td>
                      <span class="badge ${this._getStateClass(item.state)}">
                        ${item.state}
                      </span>
                    </td>
                    <td>${item.assigned_radiologist_id || html`<span style="color: #64748b;">Unassigned</span>`}</td>
                  </tr>
                `
              )}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  private _getPriorityClass(priority: string): string {
    const p = (priority || "").toUpperCase();
    if (p === "STAT") return "priority-stat";
    if (p === "URGENT") return "priority-urgent";
    return "priority-routine";
  }

  private _getStateClass(state: string): string {
    const s = (state || "").toLowerCase();
    if (s.includes("draft")) return "badge-draft";
    if (s.includes("sign") || s.includes("final")) return "badge-signed";
    if (s.includes("deliver")) return "badge-delivered";
    return "badge-state";
  }
}
