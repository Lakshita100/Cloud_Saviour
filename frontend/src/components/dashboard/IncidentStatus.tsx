import type { Incident } from "@/lib/mock-data";

interface Props {
  incident: Incident | null;
}

const severityClasses = {
  LOW: "bg-status-ok text-status-ok-foreground",
  MEDIUM: "bg-status-warn text-status-warn-foreground",
  HIGH: "bg-status-critical text-status-critical-foreground"
};

const statusDotClasses = {
  Detected: "bg-status-critical",
  "RCA Complete": "bg-status-warn",
  Remediated: "bg-status-ok"
};

const IncidentStatus = ({ incident }: Props) => {
  return (
    <section>
      <h2 className="font-semibold uppercase tracking-wider text-muted-foreground mb-4 text-center text-xl">Incident Status</h2>
      <div className="bg-card border border-border rounded-lg p-5 shadow-sm">
        {incident ?
        <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm text-muted-foreground">{incident.id}</span>
              <span className={`px-2.5 py-0.5 rounded text-xs font-bold uppercase ${severityClasses[incident.severity]}`}>
                {incident.severity}
              </span>
            </div>
            <p className="text-foreground font-medium">{incident.type}</p>
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${statusDotClasses[incident.status]}`} />
              <span className="text-sm text-muted-foreground">{incident.status}</span>
            </div>
          </div> :

        <div className="flex items-center gap-3">
            <span className="h-2.5 w-2.5 rounded-full bg-status-ok" />
            <span className="text-status-ok font-medium">System Stable</span>
            <span className="text-muted-foreground text-sm">— No active incidents</span>
          </div>
        }
      </div>
    </section>);

};

export default IncidentStatus;