/**
 * API client — fetches real data from the FastAPI backend.
 *
 * Backend runs on :8000, Vite dev server proxies /api → :8000.
 * All requests include the X-API-Key header for authentication.
 */

const API_BASE = "https://cloud-saviour.onrender.com/api";

// ── API Key Management ──
// Stored in localStorage so it persists across refreshes
const API_KEY_STORAGE_KEY = "cloudsaviour_api_key";

export function getApiKey(): string {
  return localStorage.getItem(API_KEY_STORAGE_KEY) || "";
}

export function setApiKey(key: string) {
  localStorage.setItem(API_KEY_STORAGE_KEY, key);
}

export function clearApiKey() {
  localStorage.removeItem(API_KEY_STORAGE_KEY);
}

function authHeaders(): HeadersInit {
  const key = getApiKey();
  return key ? { "X-API-Key": key } : {};
}

// ── Types matching backend response ──

export interface SystemMetrics {
  cpu: number;
  memory: number;
  dbConnections: number;
  errorRate: number;
  latencyP95: number;
  deploymentVersion: string;
}

export interface Incident {
  id: string;
  type: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
  status: "Detected" | "RCA Complete" | "Remediated";
}

export interface RCAOutput {
  rootCause: string;
  confidence: number;
  impactScope: string;
  remediationSteps: string[];
}

export interface Remediation {
  riskAssessment: "Low Risk" | "High Risk";
  actionTaken: string;
  executionTime: number;
  recoveryStatus: "Success" | "Failed";
}

export interface TimelineEvent {
  timestamp: string;
  message: string;
}

export interface DashboardData {
  metrics: SystemMetrics;
  incident: Incident | null;
  rca: RCAOutput | null;
  remediation: Remediation | null;
  timeline: TimelineEvent[];
  health: {
    status: string;
    active_incidents: string[];
  };
}

// ── API Functions ──

export async function fetchDashboard(): Promise<DashboardData> {
  const res = await fetch(`${API_BASE}/dashboard`, { headers: authHeaders() });
  if (res.status === 401 || res.status === 403) throw new Error("AUTH_REQUIRED");
  if (!res.ok) throw new Error(`Dashboard API error: ${res.status}`);
  return res.json();
}

export async function runPipeline(): Promise<{
  status: string;
  incident?: Incident;
  rca?: RCAOutput;
  remediation?: Remediation;
}> {
  const res = await fetch(`${API_BASE}/pipeline`, { method: "POST", headers: authHeaders() });
  if (res.status === 401 || res.status === 403) throw new Error("AUTH_REQUIRED");
  if (!res.ok) throw new Error(`Pipeline API error: ${res.status}`);
  return res.json();
}

export async function triggerIncident(
  type: "memory_leak" | "db_overload" | "crash" | "cpu_spike" | "latency_spike"
): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/trigger/${type}`, { method: "POST", headers: authHeaders() });
  if (res.status === 401 || res.status === 403) throw new Error("AUTH_REQUIRED");
  if (!res.ok) throw new Error(`Trigger error: ${res.status}`);
  return res.json();
}

export async function restartService(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/restart`, { method: "POST", headers: authHeaders() });
  if (res.status === 401 || res.status === 403) throw new Error("AUTH_REQUIRED");
  if (!res.ok) throw new Error(`Restart error: ${res.status}`);
  return res.json();
}

// ── New Endpoints ──

export interface AuditEntry {
  id: number;
  action: string;
  endpoint: string;
  method: string;
  api_key_name: string;
  source_ip: string;
  details: string;
  timestamp: string;
}

export interface IncidentRecord {
  id: string;
  type: string;
  severity: string;
  status: string;
  created_at: string;
  resolved_at: string | null;
  rca_result: Record<string, unknown> | null;
  risk_score: number | null;
  risk_level: string | null;
}

export interface LearningData {
  total_learning_records?: number;
  by_type?: Record<string, unknown>;
  incident_type?: string;
  summary?: {
    total_records: number;
    top_root_causes: { cause: string; count: number }[];
    success_rate: number;
    avg_confidence: number;
  };
}

export async function fetchAuditLog(limit = 50): Promise<{ audit_log: AuditEntry[] }> {
  const res = await fetch(`${API_BASE}/audit?limit=${limit}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Audit API error: ${res.status}`);
  return res.json();
}

export async function fetchIncidentHistory(limit = 50): Promise<{ incidents: IncidentRecord[] }> {
  const res = await fetch(`${API_BASE}/incidents?limit=${limit}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Incidents API error: ${res.status}`);
  return res.json();
}

export async function fetchIncidentStats(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/incidents/stats`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Stats API error: ${res.status}`);
  return res.json();
}

export async function fetchLearningData(type?: string): Promise<LearningData> {
  const url = type ? `${API_BASE}/learning?incident_type=${type}` : `${API_BASE}/learning`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Learning API error: ${res.status}`);
  return res.json();
}

export async function fetchMetricsHistory(minutes = 60): Promise<{ history: unknown[] }> {
  const res = await fetch(`${API_BASE}/metrics/history?minutes=${minutes}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Metrics history API error: ${res.status}`);
  return res.json();
}

// ── Incident Report Download ──

export interface IncidentReportData {
  incident: {
    id: string;
    type: string;
    severity: string;
    status: string;
    details: Record<string, unknown>;
    metrics_snapshot: Record<string, unknown>;
    rca_result: Record<string, unknown> | null;
    risk_score: number | null;
    risk_level: string | null;
    remediation_result: Record<string, unknown> | null;
    created_at: string;
    resolved_at: string | null;
    updated_at: string;
  };
  report_generated_at: string;
}

export async function fetchIncidentReport(incidentId: string): Promise<IncidentReportData> {
  const res = await fetch(`${API_BASE}/incidents/${encodeURIComponent(incidentId)}/report`, {
    headers: authHeaders(),
  });
  if (res.status === 401 || res.status === 403) throw new Error("AUTH_REQUIRED");
  if (res.status === 404) throw new Error("Incident not found");
  if (!res.ok) throw new Error(`Report API error: ${res.status}`);
  return res.json();
}

export function generateReportText(data: IncidentReportData): string {
  const inc = data.incident;
  const divider = "═".repeat(70);
  const thinDivider = "─".repeat(70);

  const lines: string[] = [];

  lines.push(divider);
  lines.push("              INCIDENT REPORT — AUTONOMOUS CLOUD INCIDENT SYSTEM");
  lines.push(divider);
  lines.push("");
  lines.push(`  Report Generated : ${new Date(data.report_generated_at).toLocaleString()}`);
  lines.push("");
  lines.push(thinDivider);
  lines.push("  1. INCIDENT OVERVIEW");
  lines.push(thinDivider);
  lines.push(`  Incident ID      : ${inc.id}`);
  lines.push(`  Type              : ${inc.type}`);
  lines.push(`  Severity          : ${inc.severity}`);
  lines.push(`  Status            : ${inc.status}`);
  lines.push(`  Created At        : ${inc.created_at}`);
  lines.push(`  Resolved At       : ${inc.resolved_at || "Not yet resolved"}`);
  lines.push(`  Last Updated      : ${inc.updated_at}`);

  // Risk Assessment
  lines.push("");
  lines.push(thinDivider);
  lines.push("  2. RISK ASSESSMENT");
  lines.push(thinDivider);
  if (inc.risk_score != null) {
    lines.push(`  Risk Score        : ${inc.risk_score}`);
    lines.push(`  Risk Level        : ${inc.risk_level || "N/A"}`);
  } else {
    lines.push("  Risk assessment was not performed for this incident.");
  }

  // What Happened — Details & Metrics
  lines.push("");
  lines.push(thinDivider);
  lines.push("  3. WHAT HAPPENED — INCIDENT DETAILS");
  lines.push(thinDivider);
  if (inc.details && Object.keys(inc.details).length > 0) {
    for (const [key, value] of Object.entries(inc.details)) {
      lines.push(`  ${key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()).padEnd(20)}: ${typeof value === "object" ? JSON.stringify(value) : value}`);
    }
  } else {
    lines.push("  No additional details recorded.");
  }

  lines.push("");
  lines.push("  Metrics Snapshot at Time of Incident:");
  if (inc.metrics_snapshot && Object.keys(inc.metrics_snapshot).length > 0) {
    for (const [key, value] of Object.entries(inc.metrics_snapshot)) {
      lines.push(`    • ${key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}: ${typeof value === "object" ? JSON.stringify(value) : value}`);
    }
  } else {
    lines.push("    No metrics snapshot available.");
  }

  // Root Cause Analysis
  lines.push("");
  lines.push(thinDivider);
  lines.push("  4. ROOT CAUSE ANALYSIS (AI-GENERATED)");
  lines.push(thinDivider);
  if (inc.rca_result && Object.keys(inc.rca_result).length > 0) {
    const rca = inc.rca_result as Record<string, unknown>;
    if (rca.root_cause || rca.rootCause) {
      lines.push(`  Root Cause        : ${rca.root_cause || rca.rootCause}`);
    }
    if (rca.confidence) {
      lines.push(`  Confidence        : ${typeof rca.confidence === "number" ? (rca.confidence * 100).toFixed(1) + "%" : rca.confidence}`);
    }
    if (rca.impact_scope || rca.impactScope) {
      lines.push(`  Impact Scope      : ${rca.impact_scope || rca.impactScope}`);
    }
    if (rca.remediation_steps || rca.remediationSteps) {
      const steps = (rca.remediation_steps || rca.remediationSteps) as string[];
      if (Array.isArray(steps) && steps.length > 0) {
        lines.push("");
        lines.push("  Recommended Remediation Steps:");
        steps.forEach((step, i) => {
          lines.push(`    ${i + 1}. ${step}`);
        });
      }
    }
    // Print any other RCA fields
    const knownRcaKeys = new Set(["root_cause", "rootCause", "confidence", "impact_scope", "impactScope", "remediation_steps", "remediationSteps"]);
    for (const [key, value] of Object.entries(rca)) {
      if (!knownRcaKeys.has(key)) {
        lines.push(`  ${key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()).padEnd(20)}: ${typeof value === "object" ? JSON.stringify(value, null, 2) : value}`);
      }
    }
  } else {
    lines.push("  Root cause analysis was not performed for this incident.");
  }

  // Remediation Actions
  lines.push("");
  lines.push(thinDivider);
  lines.push("  5. REMEDIATION ACTIONS TAKEN");
  lines.push(thinDivider);
  if (inc.remediation_result && Object.keys(inc.remediation_result).length > 0) {
    const rem = inc.remediation_result as Record<string, unknown>;
    if (rem.action || rem.actionTaken || rem.action_taken) {
      lines.push(`  Action Taken      : ${rem.action || rem.actionTaken || rem.action_taken}`);
    }
    if (rem.execution_time || rem.executionTime) {
      lines.push(`  Execution Time    : ${rem.execution_time || rem.executionTime}s`);
    }
    if (rem.recovery_status || rem.recoveryStatus) {
      lines.push(`  Recovery Status   : ${rem.recovery_status || rem.recoveryStatus}`);
    }
    if (rem.risk_assessment || rem.riskAssessment) {
      lines.push(`  Risk Assessment   : ${rem.risk_assessment || rem.riskAssessment}`);
    }
    // Print any other remediation fields
    const knownRemKeys = new Set(["action", "actionTaken", "action_taken", "execution_time", "executionTime", "recovery_status", "recoveryStatus", "risk_assessment", "riskAssessment"]);
    for (const [key, value] of Object.entries(rem)) {
      if (!knownRemKeys.has(key)) {
        lines.push(`  ${key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()).padEnd(20)}: ${typeof value === "object" ? JSON.stringify(value, null, 2) : value}`);
      }
    }
  } else {
    lines.push("  No remediation actions were recorded for this incident.");
  }

  // Resolution Summary
  lines.push("");
  lines.push(thinDivider);
  lines.push("  6. RESOLUTION SUMMARY");
  lines.push(thinDivider);
  if (inc.resolved_at) {
    const created = new Date(inc.created_at).getTime();
    const resolved = new Date(inc.resolved_at).getTime();
    const durationMs = resolved - created;
    const durationMin = Math.round(durationMs / 60000);
    lines.push(`  Resolution Time   : ${durationMin > 0 ? durationMin + " minutes" : "< 1 minute"}`);
    lines.push(`  Final Status      : ${inc.status.toUpperCase()}`);
    lines.push("  Outcome           : Incident successfully resolved through automated remediation.");
  } else {
    lines.push(`  Current Status    : ${inc.status.toUpperCase()}`);
    lines.push("  Outcome           : Incident is still open / pending resolution.");
  }

  lines.push("");
  lines.push(divider);
  lines.push("  END OF REPORT");
  lines.push(divider);
  lines.push("");

  return lines.join("\n");
}

export function downloadReportAsFile(text: string, filename: string) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
