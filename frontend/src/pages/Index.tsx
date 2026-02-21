import { useEffect, useState, useCallback } from "react";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import SystemHealth from "@/components/dashboard/SystemHealth";
import IncidentStatus from "@/components/dashboard/IncidentStatus";
import RCAOutput from "@/components/dashboard/RCAOutput";
import RemediationActions from "@/components/dashboard/RemediationActions";
import Timeline from "@/components/dashboard/Timeline";
import {
  fetchDashboard,
  runPipeline,
  triggerIncident,
  restartService,
  fetchAuditLog,
  fetchIncidentHistory,
  fetchLearningData,
  fetchIncidentReport,
  generateReportText,
  downloadReportAsFile,
  getApiKey,
  setApiKey,
  clearApiKey,
  type DashboardData,
  type AuditEntry,
  type IncidentRecord,
  type LearningData,
} from "@/lib/api";

const EMPTY_DATA: DashboardData = {
  metrics: {
    cpu: 0,
    memory: 0,
    dbConnections: 0,
    errorRate: 0,
    latencyP95: 0,
    deploymentVersion: "v1.0.0",
  },
  incident: null,
  rca: null,
  remediation: null,
  timeline: [],
  health: { status: "unknown", active_incidents: [] },
};

const Index = () => {
  const [data, setData] = useState<DashboardData>(EMPTY_DATA);
  const [loading, setLoading] = useState(false);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(!getApiKey());
  const [keyInput, setKeyInput] = useState("");
  const [activeTab, setActiveTab] = useState<"dashboard" | "history" | "audit" | "learning">("dashboard");
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [incidentHistory, setIncidentHistory] = useState<IncidentRecord[]>([]);
  const [learningData, setLearningData] = useState<LearningData | null>(null);
  const [downloadingReport, setDownloadingReport] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const d = await fetchDashboard();
      setData(d);
      setError(null);
      setNeedsAuth(false);
    } catch (e: any) {
      if (e?.message === "AUTH_REQUIRED") {
        setNeedsAuth(true);
        setError("Authentication required — enter your API key below.");
      } else {
        setError("Backend unreachable — is uvicorn running on :8000?");
      }
    }
  }, []);

  // Auto-refresh every 5 seconds
  useEffect(() => {
    if (!needsAuth) {
      refresh();
      const interval = setInterval(refresh, 5000);
      return () => clearInterval(interval);
    }
  }, [refresh, needsAuth]);

  const handleLogin = () => {
    if (keyInput.trim()) {
      setApiKey(keyInput.trim());
      setNeedsAuth(false);
      setKeyInput("");
      setError(null);
      refresh();
    }
  };

  const handleLogout = () => {
    clearApiKey();
    setNeedsAuth(true);
    setData(EMPTY_DATA);
  };

  const handlePipeline = async () => {
    setPipelineRunning(true);
    try {
      await runPipeline();
      await refresh();
    } catch (e: any) {
      if (e?.message === "AUTH_REQUIRED") setNeedsAuth(true);
      else setError("Pipeline failed — check backend logs");
    } finally {
      setPipelineRunning(false);
    }
  };

  const handleTrigger = async (
    type: "memory_leak" | "db_overload" | "crash" | "cpu_spike" | "latency_spike"
  ) => {
    setPipelineRunning(true);
    setError(null);
    try {
      await triggerIncident(type);
      await refresh();
      await runPipeline();
      await refresh();
    } catch (e: any) {
      if (e?.message === "AUTH_REQUIRED") { setNeedsAuth(true); }
      else {
        try {
          await refresh();
          await runPipeline();
          await refresh();
        } catch {
          setError("Pipeline failed after incident injection — check backend logs");
        }
      }
    } finally {
      setPipelineRunning(false);
    }
  };

  const handleRestart = async () => {
    setLoading(true);
    try {
      await restartService();
      await refresh();
    } finally {
      setLoading(false);
    }
  };

  const loadAudit = async () => {
    try {
      const res = await fetchAuditLog(100);
      setAuditLog(res.audit_log);
    } catch { setAuditLog([]); }
  };

  const loadHistory = async () => {
    try {
      const res = await fetchIncidentHistory(50);
      setIncidentHistory(res.incidents);
    } catch { setIncidentHistory([]); }
  };

  const loadLearning = async () => {
    try {
      const res = await fetchLearningData();
      setLearningData(res);
    } catch { setLearningData(null); }
  };

  const handleDownloadReport = async (incidentId: string) => {
    setDownloadingReport(incidentId);
    try {
      const reportData = await fetchIncidentReport(incidentId);
      const reportText = generateReportText(reportData);
      const safeId = incidentId.replace(/[^a-zA-Z0-9-_]/g, "_");
      downloadReportAsFile(reportText, `Incident_Report_${safeId}.txt`);
    } catch (e: any) {
      setError(e?.message || "Failed to download report");
    } finally {
      setDownloadingReport(null);
    }
  };

  const handleDownloadAllReports = async () => {
    if (incidentHistory.length === 0) return;
    setDownloadingReport("all");
    try {
      const reports: string[] = [];
      for (const inc of incidentHistory) {
        try {
          const reportData = await fetchIncidentReport(inc.id);
          reports.push(generateReportText(reportData));
        } catch {
          reports.push(`\n[ERROR] Could not fetch report for incident ${inc.id}\n`);
        }
      }
      const combined = reports.join("\n\n");
      downloadReportAsFile(combined, `All_Incident_Reports_${new Date().toISOString().slice(0, 10)}.txt`);
    } catch (e: any) {
      setError(e?.message || "Failed to download reports");
    } finally {
      setDownloadingReport(null);
    }
  };

  useEffect(() => {
    if (activeTab === "audit") loadAudit();
    if (activeTab === "history") loadHistory();
    if (activeTab === "learning") loadLearning();
  }, [activeTab]);

  // ── Auth Gate ──
  if (needsAuth) {
    return (
      <div className="min-h-screen bg-background">
        <DashboardHeader />
        <div className="max-w-md mx-auto mt-20 p-6 bg-card border border-border rounded-xl shadow-lg">
          <div className="text-center mb-6">
            <div className="text-4xl mb-2">🔐</div>
            <h2 className="text-xl font-bold text-foreground">Authentication Required</h2>
            <p className="text-sm text-muted-foreground mt-1">Enter your API key to access CloudSaviour</p>
          </div>
          {error && (
            <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-2 text-destructive text-xs mb-4">
              {error}
            </div>
          )}
          <input
            type="password"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            placeholder="cs-admin-xxxx..."
            className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm font-mono text-foreground placeholder:text-muted-foreground mb-3 focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            onClick={handleLogin}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
          >
            Authenticate
          </button>
          <p className="text-xs text-muted-foreground mt-3 text-center">
            Check backend console for the default admin key on first startup.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />

      {/* Error banner */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-4">
          <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-3 text-destructive text-sm">
            {error}
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Tabs + Logout */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-1 bg-card border border-border rounded-lg p-1">
            {(
              [
                ["dashboard", "📊 Dashboard"],
                ["history", "📋 Incident History"],
                ["audit", "🔒 Audit Log"],
                ["learning", "🧠 Learning Loop"],
              ] as const
            ).map(([tab, label]) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  activeTab === tab
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 bg-card border border-border rounded-md text-xs text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
          >
            🔓 Logout
          </button>
        </div>

        {/* ─── Dashboard Tab ─── */}
        {activeTab === "dashboard" && (
          <>
            {/* Control bar */}
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={handlePipeline}
                disabled={pipelineRunning}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
              >
                {pipelineRunning ? "⏳ Running AI Pipeline..." : "🤖 Run Full AI Pipeline"}
              </button>

              <div className="h-6 w-px bg-border mx-1" />

              {(
                [
                  ["memory_leak", "💾 Memory Leak"],
                  ["db_overload", "🗄️ DB Overload"],
                  ["crash", "💀 Crash"],
                  ["cpu_spike", "🔥 CPU Spike"],
                  ["latency_spike", "🐌 Latency Spike"],
                ] as const
              ).map(([type, label]) => (
                <button
                  key={type}
                  onClick={() => handleTrigger(type)}
                  disabled={pipelineRunning || loading}
                  className="px-3 py-1.5 bg-card border border-border rounded-md text-xs font-mono hover:bg-accent disabled:opacity-50"
                >
                  {label}
                </button>
              ))}

              <div className="h-6 w-px bg-border mx-1" />

              <button
                onClick={handleRestart}
                disabled={loading}
                className="px-3 py-1.5 bg-status-ok/10 border border-status-ok/30 text-status-ok rounded-md text-xs font-medium hover:bg-status-ok/20 disabled:opacity-50"
              >
                🔄 Restart Service
              </button>

              <button
                onClick={refresh}
                className="px-3 py-1.5 bg-card border border-border rounded-md text-xs font-mono hover:bg-accent ml-auto"
              >
                ↻ Refresh
              </button>
            </div>

            <SystemHealth metrics={data.metrics} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <IncidentStatus incident={data.incident} />
              <RemediationActions remediation={data.remediation} />
            </div>
            <RCAOutput rca={data.rca} />
            <Timeline events={data.timeline} />
          </>
        )}

        {/* ─── Incident History Tab ─── */}
        {activeTab === "history" && (
          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-foreground">📋 Incident History</h2>
              <div className="flex items-center gap-2">
                {incidentHistory.length > 0 && (
                  <button
                    onClick={handleDownloadAllReports}
                    disabled={downloadingReport === "all"}
                    className="px-3 py-1 bg-primary/10 border border-primary/30 text-primary rounded-md text-xs font-medium hover:bg-primary/20 disabled:opacity-50"
                  >
                    {downloadingReport === "all" ? "⏳ Generating..." : "📥 Download All Reports"}
                  </button>
                )}
                <button onClick={loadHistory} className="px-3 py-1 bg-accent rounded-md text-xs hover:bg-accent/80">
                  ↻ Refresh
                </button>
              </div>
            </div>
            {incidentHistory.length === 0 ? (
              <p className="text-muted-foreground text-sm">No incidents recorded yet. Run a pipeline to generate data.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="py-2 pr-4 font-medium">ID</th>
                      <th className="py-2 pr-4 font-medium">Type</th>
                      <th className="py-2 pr-4 font-medium">Severity</th>
                      <th className="py-2 pr-4 font-medium">Status</th>
                      <th className="py-2 pr-4 font-medium">Risk</th>
                      <th className="py-2 pr-4 font-medium">Created</th>
                      <th className="py-2 pr-4 font-medium">Resolved</th>
                      <th className="py-2 font-medium">Report</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incidentHistory.map((inc) => (
                      <tr key={inc.id} className="border-b border-border/50 hover:bg-accent/30">
                        <td className="py-2 pr-4 font-mono text-xs">{inc.id}</td>
                        <td className="py-2 pr-4">{inc.type}</td>
                        <td className="py-2 pr-4">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            inc.severity === "HIGH" ? "bg-destructive/20 text-destructive" :
                            inc.severity === "MEDIUM" ? "bg-yellow-500/20 text-yellow-600" :
                            "bg-blue-500/20 text-blue-600"
                          }`}>{inc.severity}</span>
                        </td>
                        <td className="py-2 pr-4">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            inc.status === "remediated" ? "bg-green-500/20 text-green-600" :
                            "bg-yellow-500/20 text-yellow-600"
                          }`}>{inc.status}</span>
                        </td>
                        <td className="py-2 pr-4 font-mono text-xs">{inc.risk_level || "—"}</td>
                        <td className="py-2 pr-4 text-xs text-muted-foreground">{inc.created_at}</td>
                        <td className="py-2 pr-4 text-xs text-muted-foreground">{inc.resolved_at || "—"}</td>
                        <td className="py-2">
                          <button
                            onClick={() => handleDownloadReport(inc.id)}
                            disabled={downloadingReport === inc.id}
                            className="px-2 py-1 bg-primary/10 border border-primary/30 text-primary rounded-md text-xs font-medium hover:bg-primary/20 disabled:opacity-50 whitespace-nowrap"
                            title={`Download full report for ${inc.id}`}
                          >
                            {downloadingReport === inc.id ? "⏳" : "📄 Download"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ─── Audit Log Tab ─── */}
        {activeTab === "audit" && (
          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-foreground">🔒 Audit Log</h2>
              <button onClick={loadAudit} className="px-3 py-1 bg-accent rounded-md text-xs hover:bg-accent/80">
                ↻ Refresh
              </button>
            </div>
            <p className="text-xs text-muted-foreground mb-4">
              Every API request is logged with the user identity, source IP, and action taken.
            </p>
            {auditLog.length === 0 ? (
              <p className="text-muted-foreground text-sm">No audit entries yet.</p>
            ) : (
              <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-card">
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="py-2 pr-4 font-medium">Timestamp</th>
                      <th className="py-2 pr-4 font-medium">Action</th>
                      <th className="py-2 pr-4 font-medium">User</th>
                      <th className="py-2 pr-4 font-medium">Source IP</th>
                      <th className="py-2 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLog.map((entry) => {
                      const details = typeof entry.details === "string" ? JSON.parse(entry.details || "{}") : entry.details;
                      return (
                        <tr key={entry.id} className="border-b border-border/50 hover:bg-accent/30">
                          <td className="py-2 pr-4 text-xs font-mono text-muted-foreground">{entry.timestamp}</td>
                          <td className="py-2 pr-4 text-xs font-mono">
                            <span className={`font-medium ${
                              entry.method === "POST" ? "text-yellow-600" :
                              entry.method === "DELETE" ? "text-destructive" : "text-foreground"
                            }`}>{entry.method}</span> {entry.endpoint}
                          </td>
                          <td className="py-2 pr-4 text-xs">{entry.api_key_name}</td>
                          <td className="py-2 pr-4 text-xs font-mono">{entry.source_ip}</td>
                          <td className="py-2 text-xs">
                            <span className={`px-2 py-0.5 rounded-full text-xs ${
                              details?.status_code < 400 ? "bg-green-500/20 text-green-600" :
                              "bg-destructive/20 text-destructive"
                            }`}>{details?.status_code || "—"}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ─── Learning Loop Tab ─── */}
        {activeTab === "learning" && (
          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-foreground">🧠 Learning Loop</h2>
              <button onClick={loadLearning} className="px-3 py-1 bg-accent rounded-md text-xs hover:bg-accent/80">
                ↻ Refresh
              </button>
            </div>
            <p className="text-xs text-muted-foreground mb-4">
              The system learns from every resolved incident. Past root causes, success rates, and confidence calibrations
              are used to improve future AI analysis and automatically update the knowledge base.
            </p>
            {!learningData || learningData.total_learning_records === 0 ? (
              <div className="text-center py-8">
                <div className="text-4xl mb-2">📚</div>
                <p className="text-muted-foreground text-sm">No learning data yet.</p>
                <p className="text-muted-foreground text-xs mt-1">
                  Resolve some incidents through the AI pipeline to start building the learning loop.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-background border border-border rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-foreground">{learningData.total_learning_records}</div>
                    <div className="text-xs text-muted-foreground">Total Learning Records</div>
                  </div>
                  <div className="bg-background border border-border rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-foreground">{Object.keys(learningData.by_type || {}).length}</div>
                    <div className="text-xs text-muted-foreground">Incident Types Tracked</div>
                  </div>
                  <div className="bg-background border border-border rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-green-600">Active</div>
                    <div className="text-xs text-muted-foreground">KB Auto-Update</div>
                  </div>
                </div>
                {learningData.by_type && Object.entries(learningData.by_type).map(([type, data]: [string, any]) => (
                  <div key={type} className="bg-background border border-border rounded-lg p-4">
                    <h3 className="font-semibold text-sm text-foreground mb-2">{type}</h3>
                    <div className="grid grid-cols-3 gap-4 text-xs">
                      <div>
                        <span className="text-muted-foreground">Records:</span>{" "}
                        <span className="font-mono">{data.total_records}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Success Rate:</span>{" "}
                        <span className={`font-mono ${data.success_rate >= 80 ? "text-green-600" : "text-yellow-600"}`}>
                          {data.success_rate}%
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Avg Confidence:</span>{" "}
                        <span className="font-mono">{(data.avg_confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    {data.top_root_causes?.length > 0 && (
                      <div className="mt-2">
                        <span className="text-xs text-muted-foreground">Top root causes:</span>
                        <ul className="mt-1 space-y-0.5">
                          {data.top_root_causes.map((rc: any, i: number) => (
                            <li key={i} className="text-xs text-foreground">
                              • {rc.cause} <span className="text-muted-foreground">({rc.count}x)</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default Index;
