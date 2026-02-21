/**
 * API client — fetches real data from the FastAPI backend.
 *
 * Backend runs on :8000, Vite dev server proxies /api → :8000.
 * All requests include the X-API-Key header for authentication.
 */

const API_BASE = "/api";

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
  const res = await fetch(`/trigger/${type}`, { method: "POST", headers: authHeaders() });
  if (res.status === 401 || res.status === 403) throw new Error("AUTH_REQUIRED");
  if (!res.ok) throw new Error(`Trigger error: ${res.status}`);
  return res.json();
}

export async function restartService(): Promise<Record<string, unknown>> {
  const res = await fetch("/restart", { method: "POST", headers: authHeaders() });
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
