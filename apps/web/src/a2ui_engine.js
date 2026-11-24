/**
 * A2UI Protocol Engine (Clean Architecture Presentation Layer).
 * Initializes A2UI MessageProcessor, registers the widget component catalog,
 * and maintains real-time SSE connection with FastAPI /api/v1/agent/stream.
 */
import { MessageProcessor, RELAXED_VALIDATION } from "@a2ui/web_core";

// Import native web components to register them with customElements
import "./components/worklist-table.ts";
import "./components/case-concierge-panel.ts";
import "./components/report-editor-widget.ts";
import "./components/explainability-widget.ts";
import "./components/metrics-dashboard-widget.ts";
import "./components/radiology-study-viewer.ts";

export class A2UIEngine {
  constructor() {
    this.processor = null;
    this.eventSource = null;
    this.catalog = new Map();
    this.listeners = new Map();
    this.isConnected = false;
    this.activeSurfaceId = "workbench-root";
  }

  /**
   * Initialize A2UI Engine and register the widget catalog.
   */
  async init(apiBaseUrl = "http://localhost:8000") {
    console.log("[A2UI Engine] Initializing MessageProcessor and Component Catalog...");
    this.apiBaseUrl = apiBaseUrl;

    // 1. Initialize A2UI MessageProcessor with relaxed validation for flexible clinical widgets
    this.processor = new MessageProcessor({
      version: "v0.9",
      validationConfig: RELAXED_VALIDATION,
      outboundListener: (message) => {
        console.log("[A2UI Outbound Message]:", message);
      },
      errorHandler: (error) => {
        console.warn("[A2UI Processor Error]:", error);
      },
      reportErrorsOnly: true,
    });

    // 2. Register Native Components in A2UI Catalog
    this._registerComponent("WorklistTable", "worklist-table");
    this._registerComponent("CaseConciergePanel", "case-concierge-panel");
    this._registerComponent("ReportEditorWidget", "report-editor-widget");
    this._registerComponent("ExplainabilityWidget", "explainability-widget");
    this._registerComponent("MetricsDashboardWidget", "metrics-dashboard-widget");
    this._registerComponent("RadiologyStudyViewer", "radiology-study-viewer");

    console.log(`[A2UI Engine] Registered ${this.catalog.size} components in A2UI catalog.`);

    // 3. Connect to Agent SSE Stream
    this.connectStream();

    return this;
  }

  /**
   * Register a component in the A2UI widget catalog.
   */
  _registerComponent(widgetName, tagName) {
    this.catalog.set(widgetName, {
      tagName,
      elementClass: customElements.get(tagName),
    });
  }

  /**
   * Establish Server-Sent Events (SSE) connection to Deep Agents stream.
   */
  connectStream(workItemId = null) {
    const streamUrl = `${this.apiBaseUrl}/api/v1/agent/stream${
      workItemId ? `?work_item_id=${encodeURIComponent(workItemId)}` : ""
    }`;

    console.log(`[A2UI Engine] Connecting to SSE stream: ${streamUrl}`);

    if (this.eventSource) {
      this.eventSource.close();
    }

    try {
      this.eventSource = new EventSource(streamUrl);

      this.eventSource.onopen = () => {
        this.isConnected = true;
        console.log("[A2UI Engine] SSE stream connection established.");
        this._emit("connection", { status: "connected" });
      };

      this.eventSource.onmessage = (event) => {
        try {
          const a2uiMessage = JSON.parse(event.data);
          this._handleA2UIMessage(a2uiMessage);
        } catch (err) {
          console.warn("[A2UI Engine] Malformed message received:", event.data, err);
        }
      };

      this.eventSource.onerror = (err) => {
        console.warn("[A2UI Engine] SSE connection warning (auto-reconnecting):", err);
        this.isConnected = false;
        this._emit("connection", { status: "disconnected" });
      };
    } catch (e) {
      console.error("[A2UI Engine] Failed to initialize EventSource:", e);
    }
  }

  /**
   * Handle incoming A2UI protocol message envelope.
   */
  _handleA2UIMessage(message) {
    const { type, surfaceId, payload } = message;

    // Process through A2UI MessageProcessor
    try {
      if (this.processor && message.messages) {
        this.processor.processMessages(message);
      }
    } catch (err) {
      console.debug("[A2UI Processor pass-through]:", err);
    }

    // Dispatch to registered UI listeners
    if (type === "surfaceCreate" || type === "surfaceUpdate") {
      this._emit("surfaceUpdate", { surfaceId, payload });
    } else if (type === "dataUpdate") {
      this._emit("dataUpdate", { surfaceId, payload });
      // Specialized events
      if (surfaceId === "worklist-table") {
        this._emit("worklistUpdate", payload.items);
      } else if (surfaceId === "case-concierge") {
        this._emit("conciergeUpdate", payload);
      } else if (surfaceId === "explainability-panel") {
        this._emit("explainabilityUpdate", payload);
      }
    }
  }

  /**
   * Event emitter helpers.
   */
  on(eventName, callback) {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, new Set());
    }
    this.listeners.get(eventName).add(callback);
    return () => this.listeners.get(eventName).delete(callback);
  }

  _emit(eventName, data) {
    if (this.listeners.has(eventName)) {
      for (const cb of this.listeners.get(eventName)) {
        try {
          cb(data);
        } catch (err) {
          console.error(`[A2UI Engine] Error in listener for '${eventName}':`, err);
        }
      }
    }
  }

  /**
   * Dispatch client action back to agent.
   */
  async dispatchAction(actionName, payload = {}) {
    console.log(`[A2UI Action] '${actionName}':`, payload);
    this._emit("clientAction", { actionName, payload });
  }

  /**
   * Close connections and cleanup.
   */
  destroy() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.listeners.clear();
  }
}

// Global singleton instance
export const a2uiEngine = new A2UIEngine();
