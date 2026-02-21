interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  status?: "ok" | "warn" | "critical";
}

const MetricCard = ({ label, value, unit, status = "ok" }: MetricCardProps) => {
  const statusClasses = {
    ok: "border-l-status-ok",
    warn: "border-l-status-warn",
    critical: "border-l-status-critical",
  };

  const valueClasses = {
    ok: "text-status-ok",
    warn: "text-status-warn",
    critical: "text-status-critical",
  };

  return (
    <div className={`bg-card rounded-lg border border-border border-l-4 ${statusClasses[status]} p-5 shadow-sm`}>
      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">{label}</p>
      <div className="flex items-baseline gap-1">
        <span className={`font-mono text-3xl font-bold ${valueClasses[status]}`}>{value}</span>
        {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
      </div>
    </div>
  );
};

export default MetricCard;
