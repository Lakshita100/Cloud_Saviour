import type { RCAOutput as RCAData } from "@/lib/mock-data";

interface Props {
  rca: RCAData | null;
}

const RCAOutput = ({ rca }: Props) => {
  return (
    <section>
      <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-4">
        AI Root Cause Analysis
      </h2>
      <div className="border border-border rounded-lg p-5 shadow-sm bg-popover">
        {rca ?
        <div className="space-y-4 text-sm">
            <div>
              <span className="text-muted-foreground text-xs uppercase tracking-wider">Root Cause</span>
              <p className="text-foreground mt-1">{rca.rootCause}</p>
            </div>
            <div className="flex gap-8">
              <div>
                <span className="text-muted-foreground text-xs uppercase tracking-wider">Confidence</span>
                <p className="font-mono text-xl font-bold text-status-ok mt-1">{rca.confidence}%</p>
              </div>
              <div className="flex-1">
                <span className="text-muted-foreground text-xs uppercase tracking-wider">Impact Scope</span>
                <p className="text-foreground mt-1">{rca.impactScope}</p>
              </div>
            </div>
            <div>
              <span className="text-muted-foreground text-xs uppercase tracking-wider">Recommended Remediation</span>
              <ul className="mt-2 space-y-1.5">
                {rca.remediationSteps.map((step, i) =>
              <li key={i} className="flex items-start gap-2 text-foreground">
                    <span className="font-mono text-muted-foreground text-xs mt-0.5">{i + 1}.</span>
                    <span>{step}</span>
                  </li>
              )}
              </ul>
            </div>
          </div> :

        <p className="text-muted-foreground italic">Awaiting analysis…</p>
        }
      </div>
    </section>);

};

export default RCAOutput;