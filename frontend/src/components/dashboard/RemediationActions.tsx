import type { Remediation } from "@/lib/api";

interface Props {
  remediation: Remediation | null;
}

const RemediationActions = ({ remediation }: Props) => {
  return (
    <section>
      <h2 className="font-semibold uppercase tracking-wider text-muted-foreground mb-4 text-center text-xl">Resolution Steps</h2>
      <div className="bg-card border border-border rounded-lg p-5 shadow-sm">
        {remediation ?
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground text-xs uppercase tracking-wider">Risk Assessment</span>
              <p className={`mt-1 font-medium ${remediation.riskAssessment === "Low Risk" ? "text-status-ok" : "text-status-critical"}`}>
                {remediation.riskAssessment}
              </p>
            </div>
            <div className="col-span-2 lg:col-span-1">
              <span className="text-muted-foreground text-xs uppercase tracking-wider">Action Taken</span>
              <p className="mt-1 text-foreground">{remediation.actionTaken}</p>
            </div>
            <div>
              <span className="text-muted-foreground text-xs uppercase tracking-wider">Execution Time</span>
              <p className="mt-1 font-mono text-foreground">{remediation.executionTime}s</p>
            </div>
            <div>
              <span className="text-muted-foreground text-xs uppercase tracking-wider">Recovery Status</span>
              <p className={`mt-1 font-bold ${remediation.recoveryStatus === "Success" ? "text-status-ok" : "text-status-critical"}`}>
                {remediation.recoveryStatus}
              </p>
            </div>
          </div> :

        <p className="text-muted-foreground italic text-sm">No remediation actions taken</p>
        }
      </div>
    </section>);

};

export default RemediationActions;