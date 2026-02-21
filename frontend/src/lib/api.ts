/**
 * API client — fetches real data from the FastAPI backend.
 *
 * Backend runs on :8000, Vite dev server proxies /api → :8000.
 */

const API_BASE = "/api";

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
  const res = await fetch(`${API_BASE}/dashboard`);
  if (!res.ok) throw new Error(`Dashboard API error: ${res.status}`);
  return res.json();
}

export async function runPipeline(): Promise<{
  status: string;
  incident?: Incident;
  rca?: RCAOutput;
  remediation?: Remediation;
}> {
  const res = await fetch(`${API_BASE}/pipeline`, { method: "POST" });
  if (!res.ok) throw new Error(`Pipeline API error: ${res.status}`);
  return res.json();
}

export async function triggerIncident(
  type: "memory_leak" | "db_overload" | "crash" | "cpu_spike" | "latency_spike"
): Promise<Record<string, unknown>> {
  const res = await fetch(`/trigger/${type}`, { method: "POST" });
  if (!res.ok) throw new Error(`Trigger error: ${res.status}`);
  return res.json();
}

export async function restartService(): Promise<Record<string, unknown>> {
  const res = await fetch("/restart", { method: "POST" });
  if (!res.ok) throw new Error(`Restart error: ${res.status}`);
  return res.json();
}
