import type { TimelineEvent } from "@/lib/mock-data";

interface Props {
  events: TimelineEvent[];
}

const Timeline = ({ events }: Props) => {
  return (
    <section>
      <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-4">Event Timeline</h2>
      <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden">
        <div className="h-56 overflow-y-auto p-4 font-mono text-sm">
          {events.length > 0 ? (
            events.map((event, i) => (
              <div key={i} className="flex gap-3 py-1.5 border-b border-border last:border-0">
                <span className="text-muted-foreground shrink-0">[{event.timestamp}]</span>
                <span className="text-foreground">{event.message}</span>
              </div>
            ))
          ) : (
            <p className="text-muted-foreground italic">No events recorded</p>
          )}
        </div>
      </div>
    </section>
  );
};

export default Timeline;
