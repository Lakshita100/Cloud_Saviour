import type { SystemMetrics } from "@/lib/api";
import MetricCard from "./MetricCard";

interface Props {
  metrics: SystemMetrics;
}

function getStatus(value: number, warn: number, crit: number): "ok" | "warn" | "critical" {
  if (value > crit) return "critical";
  if (value > warn) return "warn";
  return "ok";
}

const SystemHealth = ({ metrics }: Props) => {
  return (
    <section>
      <h2 className="font-semibold uppercase tracking-wider text-muted-foreground mb-4 text-center text-xl">System Health</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard
          label="CPU Usage"
          value={metrics.cpu.toFixed(1)}
          unit="%"
          status={getStatus(metrics.cpu, 70, 90)} />

        <MetricCard
          label="Memory Usage"
          value={metrics.memory.toFixed(1)}
          unit="%"
          status={getStatus(metrics.memory, 70, 90)} />

        <MetricCard
          label="DB Connections"
          value={metrics.dbConnections}
          status={getStatus(metrics.dbConnections, 70, 90)} />

        <MetricCard
          label="Error Rate"
          value={metrics.errorRate.toFixed(2)}
          unit="%"
          status={getStatus(metrics.errorRate, 1, 5)} />

        <MetricCard
          label="Latency P95"
          value={metrics.latencyP95.toFixed(0)}
          unit="ms"
          status={getStatus(metrics.latencyP95, 500, 1000)} />

        <MetricCard
          label="Deployment Version"
          value={metrics.deploymentVersion}
          status="ok" />

      </div>
    </section>);

};

export default SystemHealth;