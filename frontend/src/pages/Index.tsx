import { useEffect, useState } from "react";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import SystemHealth from "@/components/dashboard/SystemHealth";
import IncidentStatus from "@/components/dashboard/IncidentStatus";
import RCAOutput from "@/components/dashboard/RCAOutput";
import RemediationActions from "@/components/dashboard/RemediationActions";
import Timeline from "@/components/dashboard/Timeline";
import { getMockData, type DashboardData } from "@/lib/mock-data";

const Index = () => {
  const [data, setData] = useState<DashboardData>(getMockData());

  useEffect(() => {
    const interval = setInterval(() => {
      setData(getMockData());
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
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
