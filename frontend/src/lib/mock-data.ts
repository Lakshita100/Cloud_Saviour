export interface SystemMetrics {
  cpu: number;
  memory: number;
  dbConnections: number;
  errorRate: number;
  latencyP95: number;
  deploymentVersion: string;
}

export interface Incident {
  id: string;
  type: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
  status: "Detected" | "RCA Complete" | "Remediated";
}

export interface RCAOutput {
  rootCause: string;
  confidence: number;
  impactScope: string;
  remediationSteps: string[];
}

export interface Remediation {
  riskAssessment: "Low Risk" | "High Risk";
  actionTaken: string;
  executionTime: number;
  recoveryStatus: "Success" | "Failed";
}

export interface TimelineEvent {
  timestamp: string;
  message: string;
}

export interface DashboardData {
  metrics: SystemMetrics;
  incident: Incident | null;
  rca: RCAOutput | null;
  remediation: Remediation | null;
  timeline: TimelineEvent[];
}

// Simulated data for demo purposes
let cycle = 0;

export function getMockData(): DashboardData {
  cycle++;
  const phase = cycle % 20;

  if (phase < 5) {
    // Stable
    return {
      metrics: {
        cpu: 32 + Math.random() * 10,
        memory: 45 + Math.random() * 5,
        dbConnections: 24,
        errorRate: 0.02 + Math.random() * 0.05,
        latencyP95: 120 + Math.random() * 30,
        deploymentVersion: "v3.12.1",
      },
      incident: null,
      rca: null,
      remediation: null,
      timeline: [
        { timestamp: "10:44:50", message: "Health check passed" },
        { timestamp: "10:44:45", message: "Deployment v3.12.1 stable" },
        { timestamp: "10:44:30", message: "All services healthy" },
      ],
    };
  }

  if (phase < 10) {
    // Incident detected
    return {
      metrics: {
        cpu: 78 + Math.random() * 15,
        memory: 72 + Math.random() * 10,
        dbConnections: 89,
        errorRate: 4.2 + Math.random() * 2,
        latencyP95: 850 + Math.random() * 200,
        deploymentVersion: "v3.12.1",
      },
      incident: {
        id: "INC-20250221-001",
        type: "Database Connection Pool Exhaustion",
        severity: "HIGH",
        status: phase < 7 ? "Detected" : "RCA Complete",
      },
      rca: phase >= 7 ? {
        rootCause: "Connection pool leak in payment-service due to unclosed transactions in retry logic after v3.12.1 deployment",
        confidence: 94,
        impactScope: "Payment processing pipeline — affecting 12% of checkout transactions",
        remediationSteps: [
          "Scale down payment-service replicas to drain leaked connections",
          "Apply hotfix patch to close orphaned DB transactions",
          "Restart connection pool with increased timeout thresholds",
          "Re-deploy payment-service with fix (v3.12.2)",
        ],
      } : null,
      remediation: null,
      timeline: [
        { timestamp: "10:45:08", message: "RCA engine analyzing root cause" },
        { timestamp: "10:45:05", message: "Anomaly confirmed — DB pool at 89/100" },
        { timestamp: "10:45:03", message: "RCA Started" },
        { timestamp: "10:45:01", message: "Incident Detected — Error rate spike" },
        { timestamp: "10:44:55", message: "Alert triggered: Error rate > 4%" },
        { timestamp: "10:44:50", message: "Health check passed" },
      ],
    };
  }

  // Remediated
  return {
    metrics: {
      cpu: 41 + Math.random() * 8,
      memory: 52 + Math.random() * 5,
      dbConnections: 31,
      errorRate: 0.08 + Math.random() * 0.05,
      latencyP95: 145 + Math.random() * 20,
      deploymentVersion: "v3.12.2",
    },
    incident: {
      id: "INC-20250221-001",
      type: "Database Connection Pool Exhaustion",
      severity: "HIGH",
      status: "Remediated",
    },
    rca: {
      rootCause: "Connection pool leak in payment-service due to unclosed transactions in retry logic after v3.12.1 deployment",
      confidence: 94,
      impactScope: "Payment processing pipeline — affecting 12% of checkout transactions",
      remediationSteps: [
        "Scale down payment-service replicas to drain leaked connections",
        "Apply hotfix patch to close orphaned DB transactions",
        "Restart connection pool with increased timeout thresholds",
        "Re-deploy payment-service with fix (v3.12.2)",
      ],
    },
    remediation: {
      riskAssessment: "Low Risk",
      actionTaken: "Auto-scaled payment-service, applied connection pool hotfix, redeployed v3.12.2",
      executionTime: 4.2,
      recoveryStatus: "Success",
    },
    timeline: [
      { timestamp: "10:45:12", message: "System Stable — All metrics nominal" },
      { timestamp: "10:45:10", message: "Recovery verified — Error rate normalized" },
      { timestamp: "10:45:08", message: "Remediation Executed — v3.12.2 deployed" },
      { timestamp: "10:45:05", message: "RCA Completed — Root cause identified" },
      { timestamp: "10:45:03", message: "RCA Started" },
      { timestamp: "10:45:01", message: "Incident Detected — Error rate spike" },
      { timestamp: "10:44:55", message: "Alert triggered: Error rate > 4%" },
    ],
  };
}
