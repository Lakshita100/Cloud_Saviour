# ☁️ CloudSaviour — Frontend Dashboard

> **Real-time monitoring dashboard for the Autonomous Cloud Incident Detection & Remediation System.**

Built with **React 18**, **TypeScript**, **Vite**, **Tailwind CSS**, and **shadcn/ui** (Radix UI primitives).

---

## Features

### 📊 Dashboard Tab
- **System Health** — Live CPU, memory, error rate, latency P95, DB connections
- **Incident Status** — Active incident with severity badge and detection status
- **RCA Output** — AI-generated root cause, confidence score, impact scope, recommended steps
- **Remediation Actions** — Action taken, execution time, recovery status
- **Timeline** — Chronological event history
- **Controls** — Run full AI pipeline, inject simulated incidents (memory leak, DB overload, crash, CPU spike, latency spike), restart service

### 📋 Incident History Tab
- Sortable table of all past incidents (ID, type, severity, status, risk level, timestamps)
- **📄 Download Report** — Per-incident detailed report download (`.txt`)
- **📥 Download All Reports** — Bulk export of all incident reports

### 🔒 Audit Log Tab
- Full audit trail of every API request
- Timestamp, action, user, source IP, HTTP status

### 🧠 Learning Loop Tab
- Total learning records and incident types tracked
- Per-type analytics: success rate, average confidence, top root causes
- Knowledge base auto-update status

---

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| React 18 | UI framework |
| TypeScript 5 | Type safety |
| Vite + SWC | Build tool (fast HMR) |
| Tailwind CSS | Utility-first styling |
| shadcn/ui | Pre-built accessible components (Radix UI) |
| TanStack React Query | Server state management |
| React Router | Client-side routing |
| Vitest | Unit testing |

---

## Getting Started

### Prerequisites

- **Node.js 18+** and **npm** (or **Bun**)
- Backend server running on `http://localhost:8000` (see [root README](../README.md))

### Installation

```bash
# Install dependencies
npm install
```

### Development

```bash
# Start dev server (port 8080, proxies API to backend :8000)
npm run dev
```

Open [http://localhost:8080](http://localhost:8080) in your browser.

### Build for Production

```bash
npm run build
```

Output is written to `dist/`.

### Preview Production Build

```bash
npm run preview
```

### Testing

```bash
# Run tests once
npm run test

# Watch mode
npm run test:watch
```

### Linting

```bash
npm run lint
```

---

## Project Structure

```
frontend/
├── public/
│   └── robots.txt
├── src/
│   ├── main.tsx                 # App entry point
│   ├── App.tsx                  # Router configuration
│   ├── App.css / index.css      # Global styles
│   ├── pages/
│   │   ├── Index.tsx            # Main dashboard (all 4 tabs)
│   │   └── NotFound.tsx         # 404 page
│   ├── components/
│   │   ├── NavLink.tsx          # Navigation link component
│   │   ├── dashboard/           # Dashboard-specific widgets
│   │   │   ├── DashboardHeader.tsx
│   │   │   ├── SystemHealth.tsx
│   │   │   ├── IncidentStatus.tsx
│   │   │   ├── RCAOutput.tsx
│   │   │   ├── RemediationActions.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   └── Timeline.tsx
│   │   └── ui/                  # shadcn/ui components (40+)
│   ├── lib/
│   │   ├── api.ts               # Backend API client & report generation
│   │   ├── mock-data.ts         # Demo/fallback mock data
│   │   └── utils.ts             # Utility functions (cn, etc.)
│   ├── hooks/
│   │   ├── use-mobile.tsx       # Mobile detection hook
│   │   └── use-toast.ts         # Toast notification hook
│   └── test/
│       ├── setup.ts             # Vitest setup
│       └── example.test.ts      # Example test
├── index.html                   # HTML entry point
├── vite.config.ts               # Vite config (proxy, aliases)
├── vitest.config.ts             # Test configuration
├── tailwind.config.ts           # Tailwind theme & plugins
├── tsconfig.json                # TypeScript configuration
├── package.json                 # Dependencies & scripts
└── components.json              # shadcn/ui configuration
```

---

## API Proxy

The Vite dev server proxies these paths to the backend at `http://localhost:8000`:

| Path | Backend Route |
|------|--------------|
| `/api/*` | All dashboard, pipeline, incidents, learning endpoints |
| `/trigger/*` | Incident injection endpoints |
| `/remediate/*` | Remediation endpoints |
| `/restart` | Service restart |
| `/health` | Health check |
| `/state` | Internal state |
| `/metrics` | Prometheus metrics |

---

## Authentication

The dashboard uses API key authentication:

1. On first load, user is prompted for an API key
2. Key is stored in `localStorage` (`cloudsaviour_api_key`)
3. Sent as `X-API-Key` header on every request
4. Logout clears the stored key

---

## Scripts Reference

| Script | Command | Description |
|--------|---------|-------------|
| `dev` | `vite` | Start dev server with HMR |
| `build` | `vite build` | Production build |
| `build:dev` | `vite build --mode development` | Development build |
| `preview` | `vite preview` | Preview production build |
| `lint` | `eslint .` | Run ESLint |
| `test` | `vitest run` | Run tests once |
| `test:watch` | `vitest` | Run tests in watch mode |
