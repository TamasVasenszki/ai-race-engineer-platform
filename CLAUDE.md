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

### API Endpoints
- GET /health → {"status":"ok","ai_provider":"mock"}
- POST /laps/ → LapResponse (id, session_id, lap_time_ms, ai_summary, ai_recommendations, created_at)
- GET /laps/{id} → LapResponse

### Key Decisions
- .env at project root (not inside backend/)
- Docker postgres port: 5433 (5432 occupied by local postgres)
- Python 3.14 + hatchling>=1.27.0 in pyproject.toml
- schemas/ as a separate folder for Pydantic models (not models/)

### Phase 2 — IN PROGRESS
- React dashboard MVP (feat/react-dashboard)

## Reference Links

- FastAPI docs: https://fastapi.tiangolo.com
- React docs: https://react.dev
- Ollama: https://ollama.com
- Terraform AWS: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- Alembic docs: https://alembic.sqlalchemy.org