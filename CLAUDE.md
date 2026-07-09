# CLAUDE.md — AI Race Engineer Platform

## Project Overview

Real-time AI race engineer platform that reads telemetry data from the Assetto Corsa
simulator, analyzes driver performance using AI, and displays results on a React dashboard.
The system uses a provider-agnostic AI adapter layer — switchable between Claude, OpenAI,
Ollama, and Mock provider via configuration. Fully functional without a Claude subscription,
including completely offline with a local model.

## Physical Architecture

```
Windows PC                         Mac (development machine)
─────────────────                  ──────────────────────────────────────
Assetto Corsa                      FastAPI backend
  + Python telemetry agent    →    PostgreSQL database
  (Shared Memory API)              AI adapter layer
                                   React dashboard
                                        ↓
                                   AWS / Kubernetes
                                   (Terraform, Prometheus, Grafana)
```

## Tech Stack

| Layer | Technology |
|---|---|
| Simulator | Assetto Corsa (Shared Memory API) |
| Telemetry agent | Python 3.11+ |
| Backend API | FastAPI + WebSocket |
| Database | PostgreSQL (AWS RDS in production) |
| AI adapter | Provider-agnostic Python layer |
| AI providers | Claude API, OpenAI API, Ollama (local), MockProvider |
| Frontend | React (Vite) |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Cloud | AWS (EKS, RDS, S3, Secrets Manager) |
| IaC | Terraform |
| Observability | Prometheus, Grafana, Loki |

## Folder Structure

```
ai-race-engineer/
├── telemetry-agent/         # Python agent, Assetto Corsa Shared Memory reader
├── backend/                 # FastAPI REST/WebSocket API
│   ├── routers/             # Route handlers split by module
│   ├── ai/                  # AI adapter layer
│   │   ├── base.py          # Abstract AIProvider interface
│   │   ├── claude.py        # ClaudeProvider
│   │   ├── openai.py        # OpenAIProvider
│   │   ├── ollama.py        # OllamaProvider (local, free)
│   │   └── mock.py          # MockProvider (for testing, no API key needed)
│   └── models/              # Pydantic v2 schemas
├── frontend/                # React (Vite) dashboard
├── infra/                   # Terraform, Kubernetes manifests
│   ├── terraform/
│   └── k8s/
├── monitoring/              # Prometheus, Grafana, Loki config
├── .github/workflows/       # GitHub Actions CI/CD pipelines
├── docker-compose.yml       # Local development environment
├── CLAUDE.md
├── .gitignore
└── README.md
```

## AI Adapter Layer

The AI layer is provider-agnostic — the active provider is configurable via `.env`,
the rest of the codebase has no dependency on any specific provider.

```python
# Switch provider in .env
AI_PROVIDER=mock        # development and testing (free, offline)
AI_PROVIDER=ollama      # local LLM (free, offline)
AI_PROVIDER=claude      # Anthropic Claude API
AI_PROVIDER=openai      # OpenAI API
```

### Provider priority by phase

- Phases 1–2: MockProvider — no API key required
- Phase 3: OllamaProvider — local, free testing
- Phases 4–5: ClaudeProvider — demo and production

## Development Phases

### Phase 1 — Telemetry agent + backend + database
- Assetto Corsa Shared Memory API → Python agent → FastAPI → PostgreSQL
- MockProvider in place of AI (no API key needed)
- Local setup with Docker Compose

### Phase 2 — AI analysis + React dashboard MVP
- ClaudeProvider integration (first real AI calls)
- Lap data displayed on dashboard
- First working, demonstrable demo

### Phase 3 — Containerization + CI/CD
- Docker Compose (local Mac development)
- GitHub Actions pipeline
- AWS deploy with Terraform

### Phase 4 — Kubernetes + cloud-native observability
- Kubernetes (AWS EKS)
- Prometheus + Grafana + Loki monitoring stack

### Phase 5 — AI Incident Analyst + OllamaProvider
- Local LLM integration with Ollama
- Platform incident analysis with root cause analysis
- Full offline mode

## Success Criteria

- **MVP:** Live telemetry collection, laps stored in PostgreSQL, AI analysis generated, dashboard displays a full session
- **Advanced:** Docker + CI/CD, AWS deploy with Terraform, Kubernetes, Prometheus/Grafana monitoring
- **Stretch goal:** AI Incident Analyst, OllamaProvider offline mode, additional simulator integrations

## Development Guidelines

### General
- Commit convention: `feat:`, `fix:`, `chore:`, `docs:` prefixes
- Every new feature developed on its own branch: `feat/feature-name`

### Python
- Python 3.11+ syntax
- Type hints everywhere (mypy compatible)
- `pyproject.toml` for dependencies (not requirements.txt)
- Async/await where possible (align with FastAPI)
- Tests: `pytest`, filename pattern `test_*.py`

### FastAPI
- Pydantic v2 models for all request/response schemas
- Routers split by module (`/routers/` folder)
- `.env` for config, loaded with `pydantic-settings`
- Never put API keys in code

### React
- TypeScript
- Vite as build tool
- Components: PascalCase filenames
- Hooks: `use` prefix

### Database
- PostgreSQL locally in Docker, AWS RDS in production
- Migrations: Alembic
- ORM: SQLAlchemy 2.0 (async)

### AWS
- All infrastructure code in `infra/terraform/`
- IAM: least privilege — only necessary permissions
- Secrets in AWS Secrets Manager, not env variables

### Security
- Never commit `.env`, AWS credentials, or API keys
- `.env.example` is fine — without values, as documentation only

## Workflow Convention

Before every new feature branch:
1. Assign the issue to the developer
2. Move it to In Progress on the Project board
3. Create a feat/[feature-name] branch and check it out

## Key Reminders

1. **Two machines:** The telemetry agent runs on Windows PC, the backend on Mac — network communication required between them
2. **Provider switching:** The AI adapter layer is the only place with provider-specific code — all other layers use the base interface
3. **Latency:** Race engineer decisions are time-critical — backend response time must be <500ms
4. **WebSocket:** Real-time data streaming requires a WebSocket connection between backend and frontend
5. **MockProvider first:** In Phase 1, do not call any real AI API — MockProvider is sufficient for development and costs nothing

## Current State

### Phase 1 — DONE
- FastAPI backend running, MockProvider returns AI analysis
- PostgreSQL schema ready, Alembic migration executable
- POST /laps/ → DB save + MockProvider AI analysis ✅
- GET /laps/{id} → fetch lap from DB ✅
- .env at project root, config.py uses Path(__file__)-based path
- Telemetry agent (ac_telemetry.py + agent.py) tested on Windows with live AC session — Shared Memory reading and backend POST both working

### API Endpoints
- GET /health → {"status":"ok","ai_provider":"mock"} (includes `ollama_status` when provider is ollama)
- POST /laps/ → LapResponse (id, session_id, lap_time_ms, ai_summary, ai_recommendations, created_at)
- GET /laps/{id} → LapResponse
- POST /sessions/ → SessionResponse (id, track, car, created_at)
- GET /sessions/ → list of SessionResponse
- GET /sessions/{id} → SessionResponse
- POST /sessions/{id}/incidents → IncidentReportResponse (incidents, provider)

### Key Decisions
- .env at project root (not inside backend/)
- Docker postgres port: 5433 (5432 occupied by local postgres)
- Python 3.13 everywhere (Dockerfile, pyproject `requires-python`, ruff `target-version`, CI `setup-python`); hatchling>=1.27.0. (3.14 was only the local dev machine, never a real requirement — unified in #19.)
- schemas/ as a separate folder for Pydantic models (not models/)

### Phase 2 — DONE
- React dashboard MVP: Vite + TypeScript, LapDashboard component, useLap hook
- ClaudeProvider implemented with async Anthropic SDK and forced tool use for structured output
- Note: ClaudeProvider not yet tested with a live API key (deferred — no subscription yet); MockProvider covers all development

### Phase 3 — DONE
- Docker Compose + GitHub Actions CI done (#7, PR #16):
  - Full stack (`db` + `backend` + `frontend`) comes up healthy with `docker compose up` — healthchecks, `depends_on: service_healthy`, `restart: unless-stopped`
  - Frontend: multi-stage Dockerfile (node build → nginx serving `dist/`), SPA fallback `nginx.conf`; mapped `5173:80` to keep the backend CORS origin valid
  - Backend: `entrypoint.sh` runs `alembic upgrade head` before uvicorn (schema auto-created); ruff lint config + `/health` pytest smoke test added
  - CI (`.github/workflows/ci.yml`): backend ruff+pytest, frontend tsc+vite build, docker build (both images, no push) — on push/PR to `main`
  - Healthcheck gotcha: containers must hit `127.0.0.1` not `localhost` (nginx/uvicorn listen IPv4-only; busybox wget doesn't fall back from IPv6)
- Compose `backend` overrides `DATABASE_URL` to `db:5432` (the `.env` value points at `localhost:5433` for native dev)
- AWS deploy with Terraform + CD done (#8, PR #17) — backend-only scope:
  - Terraform (`infra/terraform/`): VPC with 2 public + 2 private subnets, **no NAT gateway** (Fargate tasks run in public subnets with a public IP → reach ECR/Secrets/CloudWatch directly; RDS stays private)
  - ECS Fargate cluster + service behind an internet-facing ALB (target health check `/health`, port 8000)
  - RDS PostgreSQL (`db.t4g.micro`, encrypted, private); full async `DATABASE_URL` stored in Secrets Manager, injected into the task
  - ECR repo for the backend image; IAM least privilege (ECS exec role reads only the DB secret, empty task role, GitHub OIDC provider + scoped CD role — no long-lived keys)
  - CD (`.github/workflows/cd.yml`): on merge to `main`, OIDC role assume → build → ECR push (`sha`+`latest`) → render + deploy new ECS task def with `wait-for-service-stability`. **No-op until the `AWS_DEPLOY_ROLE_ARN` repo variable is set** from the `github_actions_role_arn` Terraform output (keeps `main` green before infra exists)
  - Backend `entrypoint.sh`: `uvicorn --reload` now only when `APP_ENV=development` (compose sets it for local dev; prod/ECS runs without reload)
  - Secrets Manager secrets use `recovery_window_in_days = 0` so `terraform destroy` deletes them immediately — otherwise a re-apply hits "secret already exists / scheduled for deletion" during the destroy→apply cycle
  - The AWS deploy was actually exercised end-to-end (not just written): `terraform apply` → CD deploy → live `/health` on the ALB → `terraform destroy`, all clean. Fixed the `anthropic_api_key` empty-string secret bug along the way (Secrets Manager rejects `secret_string = ""`, #18). Deployment screenshots in `docs/aws-deployment/`.
- Base image hardening + Python 3.13 unification done (#19, PR #20): ECR scan flagged Perl Critical/High CVEs in the Debian base layer; the 3.13 switch did **not** clear them (no upstream Debian perl patch — present in every Debian-based python image). Not on the app's runtime path → risk documented and accepted; perl-free base image is a low-priority backlog follow-up (#21).

### Phase 4 — DONE (EKS + cloud-native observability)
- **EKS platform (#22, PR #31):** modular Terraform — VPC (3 AZ, single NAT), EKS cluster + managed node group, Pod Identity agent + EBS CSI add-ons. K8s 1.36. `node_desired_size` bumped 2→3 in #27 to fit the observability stack.
- **Backend deploy (#23, PR #32):** custom Helm chart (`infra/k8s/backend`) — Deployment/Service/Ingress/ServiceAccount + SecretProviderClass. AWS Load Balancer Controller provisions an ALB from the Ingress; Secrets Store CSI driver (AWS provider) mounts the `DATABASE_URL` secret and syncs it to a native Secret consumed via `secretKeyRef`. **EKS Pod Identity throughout** (LBC role + least-priv backend secret-reader role, no IRSA). Exercised live end-to-end. Two live-only fixes baked into the chart: SecretProviderClass `usePodIdentity: "true"` + the CSI driver's `tokenRequests` audiences (`sts.amazonaws.com` + `pods.eks.amazonaws.com`) — without them the mount fails `serviceAccount.tokens not provided`.
- **CD → EKS (#24, PR #33):** `cd.yml` rewritten from ECS task-def to `aws eks update-kubeconfig` + `helm upgrade` at the `sha` tag. CD role got `eks:DescribeCluster` + an EKS access entry (`AmazonEKSClusterAdminPolicy` — no narrower managed policy covers the SecretProviderClass CRD; the security gate is the OIDC trust, `main`-only). Proven live (sha-push → auto `helm upgrade`).
- **Makefile lifecycle (#25, PR #34):** `make apply` (from nothing) / `make destroy` (ordered teardown). apply auto-approved; destroy asks `yes` (`AUTO_APPROVE=1` skips). Shared-account safe: ALB/SG queries filter by the `elbv2.k8s.aws/cluster` tag, never account-wide.
- **Prometheus + Grafana (#26, PR #35):** kube-prometheus-stack (ephemeral, Alertmanager off) + backend `/metrics` via `prometheus-fastapi-instrumentator` + a standalone ServiceMonitor + a Grafana dashboard. **Verified live to scrape-UP** (both backend pods `up=1`).
- **Loki + Promtail + Grafana alerting + docs (#27):** backend JSON logging (uvicorn `--log-config log_config.json`, `python-json-logger`); `grafana/loki` SingleBinary (ephemeral) + `grafana/promtail`; Loki datasource + logs dashboard; Grafana unified alerting rule (5xx error-rate); README + this CLAUDE.md update. **Statically verified; live verification (Loki logs queryable, alert firing) is bundled into the next cluster cycle** along with the two carry-overs below.
- **Teardown/preflight hardening (#36, PR #37):** `make destroy` now lets the LBC self-clean its SGs (bounded poll) then force-deletes any stragglers before `terraform destroy` (fixes an 18-min VPC `DependencyViolation` hang); `make apply` has a docker-daemon preflight (fail-fast before terraform). Statically done; **SG-cleanup proven live at the next teardown.**
- **Observability access:** Grafana via `kubectl port-forward` (`make grafana`), never a public ALB.
- **Carry-over live checks (next cluster cycle):** #36 SG-cleanup at teardown; #26 Grafana dashboard visual.

### Phase 5 — DONE (AI Incident Analyst + OllamaProvider + offline mode)
- **Sessions endpoint (#28, PR #46):** POST/GET/list `/sessions/` endpoints, `RacingSession` model, Pydantic schemas, 5 tests with in-memory SQLite (`aiosqlite` + `conftest.py`).
- **OllamaProvider (#39, PR #47):** Full `analyze_lap()` with retry+fallback on JSON parse failure, Docker Compose ollama service behind `ollama` profile, 5 unit tests.
- **Incident Analyst base (#41, PR #48):** `Incident`/`IncidentReport` dataclasses on `AIProvider`, `analyze_incidents()` as non-abstract method (default `NotImplementedError`), MockProvider threshold-based detection (>15% warning, >50% critical), 5 tests.
- **Incident Analyst prompts (#42, PR #49):** OllamaProvider `analyze_incidents()` with retry+fallback, ClaudeProvider with forced tool use (`report_incident_analysis`), refactored shared `_call()`/`_tool_call()` methods, 5 tests.
- **Incident Analyst endpoint + dashboard (#43, PR #50):** `POST /sessions/{id}/incidents` endpoint, `IncidentAnalysis` React component with severity badges, `useIncidentAnalysis` on-demand hook, App.tsx updated, 4 endpoint tests.
- **Offline mode (#44):** Docker Compose `OLLAMA_BASE_URL` override for backend→ollama networking, startup Ollama connectivity check (log warning, don't crash), `/health` includes `ollama_status` when provider is ollama, `.env.example` offline preset, README offline mode docs.

### Phase 6 — IN PROGRESS (live dashboard + WebSocket + frontend redesign)
- **Goal:** Transform the UUID-input test interface into a live, real-time race engineer monitor
- **WebSocket:** Backend pushes new lap data and incident alerts to connected frontends
- **Frontend redesign:** Session list sidebar (no manual UUID entry), lap timeline visualization, incident panel with color-coded alerts, dark racing theme
- **Live e2e:** Windows telemetry agent → Mac backend → browser dashboard in real-time
- **Backlog cleanup:** #29 remote Terraform state, #30 frontend deploy to EKS, #21 perl-free base image

### Still open / backlog
- #29 remote Terraform state (S3). · #30 frontend deploy to EKS. · #21 perl-free base image.
- CD is a no-op until the `AWS_DEPLOY_ROLE_ARN` repo variable is set from the `github_actions_role_arn` output.

## Reference Links

- FastAPI docs: https://fastapi.tiangolo.com
- React docs: https://react.dev
- Ollama: https://ollama.com
- Terraform AWS: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- Alembic docs: https://alembic.sqlalchemy.org