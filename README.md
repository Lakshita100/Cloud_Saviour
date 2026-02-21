# ☁️ Autonomous Cloud Incident Detection & Remediation System

> **An AI-powered, self-healing cloud monitoring platform that autonomously detects incidents, performs root cause analysis, assesses risk, executes remediation, and learns from every resolved incident.**

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.129-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript)
![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-E6522C?logo=prometheus)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![SQLite](https://img.shields.io/badge/SQLite-Storage-003B57?logo=sqlite)
![Ollama](https://img.shields.io/badge/Ollama-LLM-black)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
  - [Docker Deployment](#docker-deployment)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Frontend Dashboard](#frontend-dashboard)
- [AI Pipeline](#ai-pipeline)
- [Security & Authentication](#security--authentication)
- [Learning Loop](#learning-loop)
- [Monitoring](#monitoring)
- [Incident Report Downloads](#incident-report-downloads)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The **Autonomous Cloud Incident System** is a full-stack platform that simulates, detects, analyzes, and remediates cloud infrastructure incidents — all without human intervention. It combines real-time system monitoring with AI-driven root cause analysis (via local LLMs through Ollama), automated remediation orchestration (via n8n webhooks), and a self-improving learning loop that gets smarter with every resolved incident.

### How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Monitor    │────▶│   Detect     │────▶│  AI RCA     │────▶│ Risk Score   │
│  (Metrics)   │     │ (Anomalies)  │     │ (Ollama)    │     │ (Composite)  │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                                                                     │
┌─────────────┐     ┌──────────────┐     ┌─────────────┐            │
│   Learn     │◀────│   Report     │◀────│  Remediate  │◀───────────┘
│  (Feedback) │     │ (Generate)   │     │ (n8n/Direct) │
└─────────────┘     └──────────────┘     └─────────────┘
```

---

## Architecture

```
autonomous_cloud_incident_system/
│
├── app/                    # FastAPI backend application
│   ├── service.py          # Main API server (endpoints, middleware, pipeline)
│   ├── security.py         # API key auth & RBAC (admin/operator/viewer)
│   ├── storage.py          # SQLite persistence layer (incidents, metrics, audit, learning)
│   └── learning.py         # Self-improving learning loop
│
├── agent/                  # Autonomous incident management agents
│   ├── cloud_connector.py  # Prometheus / direct metrics fetcher
│   ├── detector.py         # Threshold & health-based incident detection
│   ├── anomaly_engine.py   # Statistical Z-score anomaly detection
│   ├── context_builder.py  # AI prompt construction
│   ├── rca_engine.py       # Root Cause Analysis via Ollama LLM
│   ├── risk_engine.py      # Composite risk scoring (0.0 – 1.0)
│   ├── knowledge_base.py   # Incident pattern knowledge base
│   ├── remediation_engine.py   # Multi-strategy remediation orchestrator
│   ├── remediation_trigger.py  # n8n webhook integration
│   └── report_generator.py     # Structured incident report generation
│
├── dashboard/              # Standalone monitoring loop
│   └── main.py             # Continuous autonomous pipeline runner
│
├── frontend/               # React + TypeScript dashboard
│   ├── src/
│   │   ├── pages/          # Main dashboard page
│   │   ├── components/     # Dashboard widgets & shadcn/ui components
│   │   ├── lib/            # API client, utilities, mock data
│   │   └── hooks/          # Custom React hooks
│   └── vite.config.ts      # Vite config with backend proxy
│
├── data/                   # Persistent data
│   ├── knowledge.json      # Incident pattern knowledge base
│   ├── api_keys.json       # API key hashes & roles
│   └── cloudsaviour.db     # SQLite database (auto-created)
│
├── monitoring/             # Observability
│   └── prometheus.yml      # Prometheus scrape configuration
│
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Python 3.11 container
└── requirements.txt        # Python dependencies
```

---

## Key Features

### 🔍 Real-Time Monitoring
- Live CPU, memory, error rate, latency (P95), and DB connection metrics via **psutil** and **Prometheus**
- Auto-refreshing dashboard with 5-second polling interval
- Historical metrics storage for trend analysis

### 🚨 Intelligent Incident Detection
- **Five incident types**: Memory Leak, DB Overload, Crash, CPU Spike, Latency Spike
- Dual detection strategy: health-endpoint flags + metric threshold analysis
- **Statistical anomaly detection** using sliding-window Z-score analysis (window=60, threshold=±2.5)
- Direction-aware anomaly classification (spike vs. drop)

### 🧠 AI-Powered Root Cause Analysis
- Local LLM inference via **Ollama** (phi3 → tinyllama fallback chain)
- Low-temperature (0.2) structured JSON output for deterministic analysis
- Robust response parsing with regex fallback for non-JSON LLM output
- Context-enriched prompts incorporating historical patterns and success rates

### ⚖️ Composite Risk Scoring
- Four weighted signals combined into a 0.0–1.0 risk score:
  - **Knowledge Base Weight** (40%) — historical severity of incident type
  - **AI Confidence Inversion** (25%) — lower AI confidence = higher risk
  - **Metric Severity** (20%) — deviation from normal thresholds
  - **Anomaly Z-Score** (15%) — statistical outlier magnitude
- Risk levels: `low` (0–0.3), `medium` (0.3–0.6), `high` (0.6–0.8), `critical` (0.8–1.0)

### 🔧 Automated Remediation
- **Primary**: n8n webhook-triggered workflow automation
- **Fallback**: Direct service endpoint remediation calls
- Multi-step strategy: Trigger → Wait → Verify → Fallback → Verify
- Max auto-attempts (3) with automatic escalation after repeated failures
- Complete remediation audit trail

### 📚 Self-Improving Learning Loop
- Every resolved incident feeds back into the knowledge base
- Historical root causes enrich future AI prompts
- Confidence calibration (0.6x–1.2x) based on past prediction accuracy
- Auto-suggests best remediation action from past successes
- Auto-updates `knowledge.json` when new root causes reach frequency threshold

### 📋 Incident Report Downloads
- Download detailed incident reports as `.txt` files from the dashboard
- Reports include: incident overview, risk assessment, metric snapshots, AI root cause analysis, remediation actions, and resolution summary
- Bulk download all incident reports at once

### 🔐 Enterprise Security
- API key authentication with SHA-256 hashing
- Role-based access control (admin / operator / viewer)
- Granular permissions per role
- Full audit logging of every API request (user, IP, action, timestamp)
- Public endpoints for health checks and Prometheus scraping

### 📊 Interactive Dashboard
- Real-time system health visualization
- Incident status tracking with severity badges
- AI RCA output display
- Remediation action monitoring
- Historical incident timeline
- Audit log viewer
- Learning loop analytics with success rates and top root causes

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend API** | FastAPI 0.129, Uvicorn, Pydantic 2.x |
| **AI / LLM** | Ollama (phi3, tinyllama), OpenAI SDK |
| **Database** | SQLite (WAL mode, thread-local connections) |
| **Monitoring** | Prometheus, prometheus_client |
| **Metrics Collection** | psutil, Prometheus queries |
| **Automation** | n8n webhooks |
| **Frontend** | React 18, TypeScript 5, Vite |
| **UI Components** | shadcn/ui (Radix UI), Tailwind CSS |
| **State Management** | TanStack React Query |
| **Testing** | Vitest (frontend), pytest (backend) |
| **Containerization** | Docker, Docker Compose |

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm** (or **Bun**)
- **Ollama** — for local LLM inference ([Install Ollama](https://ollama.ai))
- **Docker & Docker Compose** _(optional, for containerized deployment)_
- **n8n** _(optional, for webhook-based remediation workflows)_

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/autonomous_cloud_incident_system.git
   cd autonomous_cloud_incident_system
   ```

2. **Set up the Python virtual environment**
   ```bash
   python -m venv venv

   # Windows
   .\venv\Scripts\Activate.ps1

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Ollama models**
   ```bash
   ollama pull phi3
   ollama pull tinyllama    # fallback model
   ```

5. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Running the Application

#### Start the Backend (FastAPI)

```bash
# Activate virtual environment first
.\venv\Scripts\Activate.ps1          # Windows
source venv/bin/activate              # macOS/Linux

# Start the API server
uvicorn app.service:app --host 0.0.0.0 --port 8000
```

The backend will:
- Start on `http://localhost:8000`
- Initialize the SQLite database automatically
- Generate a default admin API key (printed in the console on first run)
- Begin background metric collection every 5 seconds

#### Start the Frontend (React)

```bash
cd frontend
npm run dev
```

The frontend will:
- Start on `http://localhost:8080`
- Proxy API requests to the backend at `:8000`

#### Start the Autonomous Pipeline (Optional)

```bash
python dashboard/main.py
```

This runs the full autonomous monitoring loop:
- Polls metrics every 10 seconds
- Automatically detects, analyzes, and remediates incidents
- 30-second cooldown after remediation cycles

### Docker Deployment

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f service

# Stop all services
docker-compose down
```

Services:
| Service | Port | Description |
|---------|------|-------------|
| `service` | 8000 | FastAPI backend |
| `prometheus` | 9090 | Prometheus monitoring |

---

## Configuration

### Knowledge Base (`data/knowledge.json`)

Defines five incident patterns with:
- Common causes and indicators
- Severity mappings (LOW / MEDIUM / HIGH)
- Remediation steps and endpoints
- Expected recovery times
- Risk weights for scoring

### API Keys (`data/api_keys.json`)

Auto-generated on first startup. Contains:
- SHA-256 hashed API keys
- Role assignments (admin / operator / viewer)
- Revocation status

### Prometheus (`monitoring/prometheus.yml`)

- Scrapes the FastAPI service at `service:8000/metrics` every 5 seconds
- 7-day data retention
- Docker bridge networking

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `N8N_WEBHOOK_URL` | `http://localhost:5678/webhook/remediation` | n8n remediation webhook |

---

## API Reference

### Public Endpoints (No Auth Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service status |
| `GET` | `/health` | Health check (healthy/degraded/crashed) |
| `GET` | `/metrics` | Prometheus scrape endpoint |

### Authenticated Endpoints

#### Dashboard & Pipeline
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| `GET` | `/api/dashboard` | `view_dashboard` | Full dashboard data (metrics, incident, RCA, remediation, timeline) |
| `POST` | `/api/pipeline` | `run_pipeline` | Run full AI pipeline: Detect → RCA → Risk → Remediate → Report |

#### Incident Simulation
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| `POST` | `/trigger/memory_leak` | `trigger_incident` | Inject memory leak |
| `POST` | `/trigger/db_overload` | `trigger_incident` | Inject DB overload |
| `POST` | `/trigger/crash` | `trigger_incident` | Inject service crash |
| `POST` | `/trigger/cpu_spike` | `trigger_incident` | Inject CPU spike |
| `POST` | `/trigger/latency_spike` | `trigger_incident` | Inject latency spike |

#### Remediation
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| `POST` | `/remediate/memory_leak` | `remediate` | Fix memory leak |
| `POST` | `/remediate/db_overload` | `remediate` | Fix DB overload |
| `POST` | `/remediate/crash` | `remediate` | Fix crash |
| `POST` | `/restart` | `restart` | Full service state reset |

#### Incident History & Reports
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| `GET` | `/api/incidents` | `view_history` | List recent incidents |
| `GET` | `/api/incidents/{id}/report` | `view_history` | Full incident report for download |
| `GET` | `/api/incidents/stats` | `view_history` | Aggregated incident statistics |
| `GET` | `/api/metrics/history` | `view_dashboard` | Historical metrics time-series |

#### Security & Admin
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| `GET` | `/api/keys` | `manage_keys` | List all API keys |
| `POST` | `/api/keys` | `manage_keys` | Create a new API key |
| `DELETE` | `/api/keys/{name}` | `manage_keys` | Revoke an API key |
| `GET` | `/api/audit` | `view_audit` | View audit log |

#### Learning Loop
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| `GET` | `/api/learning` | `view_dashboard` | Learning data and insights |
| `POST` | `/api/learning/feedback` | `give_feedback` | Submit feedback on AI analysis |

---

## Frontend Dashboard

The React-based dashboard features four main tabs:

### 📊 Dashboard
- **System Health**: Real-time CPU, memory, error rate, latency (P95), DB connections
- **Incident Status**: Current active incident with severity badge
- **RCA Output**: AI-generated root cause, confidence score, impact scope, remediation steps
- **Remediation Actions**: Action taken, execution time, recovery status
- **Timeline**: Chronological event log

### 📋 Incident History
- Table of all past incidents with ID, type, severity, status, risk level, timestamps
- **Download Report** button on each row — generates a comprehensive `.txt` report
- **Download All Reports** — bulk export of all incident reports

### 🔒 Audit Log
- Every API request logged with timestamp, action, user, source IP, and HTTP status
- Sticky header table with scrollable entries

### 🧠 Learning Loop
- Total learning records and incident types tracked
- Per-type analytics: success rate, average confidence, top root causes
- KB auto-update status

---

## AI Pipeline

The full AI pipeline executes these steps in sequence when triggered via `POST /api/pipeline`:

```
1. FETCH METRICS      →  psutil CPU/memory + Prometheus latency + TCP connections
2. ANOMALY DETECTION  →  Z-score analysis on sliding windows (60 samples)
3. INCIDENT DETECTION →  Health endpoint checks + threshold-based classification
4. AI ROOT CAUSE      →  Ollama phi3 LLM with prompt enriched by learning history
     ANALYSIS            → Confidence calibration from past accuracy
5. RISK SCORING       →  Composite score: KB weight + AI confidence + metrics + anomaly
6. REMEDIATION        →  n8n webhook → wait → verify → fallback direct call → verify
7. REPORT GENERATION  →  Structured report with all pipeline data
8. LEARNING RECORD    →  Save outcome for future prompt enrichment & KB updates
9. PERSIST            →  Save incident lifecycle to SQLite
```

---

## Security & Authentication

### Roles & Permissions

| Permission | Admin | Operator | Viewer |
|------------|:-----:|:--------:|:------:|
| `view_dashboard` | ✅ | ✅ | ✅ |
| `view_history` | ✅ | ✅ | ✅ |
| `view_audit` | ✅ | ✅ | ❌ |
| `trigger_incident` | ✅ | ✅ | ❌ |
| `run_pipeline` | ✅ | ✅ | ❌ |
| `remediate` | ✅ | ✅ | ❌ |
| `restart` | ✅ | ✅ | ❌ |
| `give_feedback` | ✅ | ✅ | ❌ |
| `manage_keys` | ✅ | ❌ | ❌ |

### Authentication Flow
1. Backend generates a default admin key on first startup (printed to console)
2. User enters the key in the frontend login screen
3. Key is stored in `localStorage` and sent as `X-API-Key` header on every request
4. Backend validates by hashing the key and comparing against stored hashes
5. Every request is logged to the audit table

---

## Learning Loop

The system implements a **closed-loop learning** mechanism:

1. **Record**: Every resolved incident (root cause, confidence, remediation outcome) is saved
2. **Enrich**: Future AI prompts include historical root causes and success rates for similar incidents
3. **Calibrate**: AI confidence is adjusted by a multiplier (0.6x–1.2x) based on past accuracy
4. **Suggest**: Best remediation action is recommended from past successes
5. **Update**: When a root cause appears frequently (≥3 times), it's auto-merged into `knowledge.json`

This creates a self-improving system where each resolved incident makes future detections faster and more accurate.

---

## Monitoring

### Prometheus Metrics Exposed

| Metric | Type | Description |
|--------|------|-------------|
| `service_cpu_usage_percent` | Gauge | Current CPU usage |
| `service_memory_usage_percent` | Gauge | Current memory usage |
| `service_errors_total` | Counter | Total errors by type |
| `service_request_latency_seconds` | Histogram | Request latency distribution |

### Accessing Prometheus

- **Prometheus UI**: `http://localhost:9090`
- **Targets**: `http://localhost:9090/targets`
- **Metrics endpoint**: `http://localhost:8000/metrics`

---

## Incident Report Downloads

Reports downloaded from the Incident History tab include:

```
═══════════════════════════════════════════════════════════════════════
              INCIDENT REPORT — AUTONOMOUS CLOUD INCIDENT SYSTEM
═══════════════════════════════════════════════════════════════════════

  1. INCIDENT OVERVIEW         — ID, type, severity, status, timestamps
  2. RISK ASSESSMENT           — Composite score and risk level
  3. WHAT HAPPENED             — Incident details and metrics snapshot
  4. ROOT CAUSE ANALYSIS       — AI root cause, confidence, impact, steps
  5. REMEDIATION ACTIONS TAKEN — Action, execution time, recovery status
  6. RESOLUTION SUMMARY        — Resolution time and final outcome

═══════════════════════════════════════════════════════════════════════
```

---

## Testing

### Frontend Tests
```bash
cd frontend
npm run test           # Run once
npm run test:watch     # Watch mode
```

### Backend Tests
```bash
python -m pytest agent/test_rca.py -v
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is open-source. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for autonomous cloud operations**

</div>