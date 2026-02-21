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
  type DashboardData,
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

  const refresh = useCallback(async () => {
    try {
      const d = await fetchDashboard();
      setData(d);
      setError(null);
    } catch (e) {
      setError("Backend unreachable — is uvicorn running on :8000?");
    }
  }, []);

  // Auto-refresh every 5 seconds
  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  const handlePipeline = async () => {
    setPipelineRunning(true);
    try {
      await runPipeline();
      await refresh();
    } catch {
      setError("Pipeline failed — check backend logs");
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
      await refresh();                 // show incident immediately
      await runPipeline();             // auto-run AI analysis
      await refresh();                 // show RCA + remediation results
    } catch {
      // crash endpoint may throw — still try pipeline
      try {
        await refresh();
        await runPipeline();
        await refresh();
      } catch {
        setError("Pipeline failed after incident injection — check backend logs");
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
      </main>
    </div>
  );
};

export default Index;
