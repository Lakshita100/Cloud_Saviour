import { useEffect, useState } from "react";
import { Cloud } from "lucide-react";

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
          <div className="relative">
            <Cloud className="h-8 w-8 text-indigo-500" fill="currentColor" strokeWidth={1.5} />
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-[8px] font-bold text-white mt-0.5">CS</span>
            </div>
          </div>
          <h1 className="text-foreground tracking-tight text-left font-extrabold text-2xl font-sans">
            <span className="text-indigo-500">Cloud</span><span className="text-purple-500">Saviour</span>
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