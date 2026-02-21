import { useEffect, useState } from "react";

const DashboardHeader = () => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-card border-b border-border px-6 py-4 shadow-md">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-status-ok" />
          <h1 className="text-foreground tracking-tight text-left font-extrabold text-2xl font-sans">CloudSaviour

          </h1>
        </div>
        <div className="font-mono text-sm text-muted-foreground">
          {time.toLocaleDateString("en-US", {
            weekday: "short",
            year: "numeric",
            month: "short",
            day: "numeric"
          })}{" "}
          <span className="text-foreground">{time.toLocaleTimeString("en-US", { hour12: false })}</span>
        </div>
      </div>
    </header>);

};

export default DashboardHeader;