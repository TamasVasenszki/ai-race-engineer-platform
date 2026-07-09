# AI Race Engineer Platform

Real-time AI race engineer that reads telemetry from the **Assetto Corsa** simulator, analyzes
driver performance with a provider-agnostic AI layer, and surfaces it on a React dashboard —
deployed to AWS EKS with a full observability stack.

The AI layer is switchable (Claude, OpenAI, Ollama, or a Mock provider) via configuration, so the
platform runs fully offline and without any API key for development.

## Architecture

```
Windows PC                         Mac (dev) / AWS
─────────────────                  ──────────────────────────────────────
Assetto Corsa                      FastAPI backend  (REST + WebSocket + /metrics)
  + Python telemetry agent    →    PostgreSQL (RDS in prod)
  (Shared Memory API)              AI adapter layer (Claude/OpenAI/Ollama/Mock)
                                   React live dashboard (dark racing theme)
                                        ↓
                                   AWS EKS  (Terraform, Helm)
                                   Prometheus + Grafana + Loki
```

## Tech stack

FastAPI + WebSocket · PostgreSQL (SQLAlchemy 2.0 async, Alembic) · React (Vite + TS) · Docker ·
GitHub Actions CI/CD · AWS EKS / RDS / ECR / Secrets Manager · Terraform · AWS Load Balancer
Controller · Secrets Store CSI driver · Prometheus / Grafana / Loki / Promtail.

## Run it

### Local (Docker Compose)

```sh
docker compose up      # db + backend + frontend, healthchecked
```
Backend on `:8000` (`/health`, `/metrics`), frontend on `:5173`. Uses the Mock AI provider by
default — no API key needed.

### Offline mode (Ollama)

Run the full stack locally without internet using a local LLM:

```sh
# 1. Set the AI provider to Ollama in .env
#    AI_PROVIDER=ollama
#    OLLAMA_MODEL=llama3.2

# 2. Start all services (db + backend + frontend + ollama)
docker compose --profile ollama up

# 3. First run only — pull the model (requires internet once)
docker exec -it <ollama-container> ollama pull llama3.2

# 4. Verify
curl http://localhost:8000/health
# → {"status":"ok","ai_provider":"ollama","ollama_status":"ok"}
```

After the model is pulled, the platform works fully offline. The `/health` endpoint reports
Ollama reachability. ~4 GB disk required for the default model.

### AWS EKS (Terraform + Helm, orchestrated by the Makefile)

```sh
make apply       # terraform apply -> kubeconfig -> image push -> LBC -> CSI -> backend chart
make monitoring  # kube-prometheus-stack + backend ServiceMonitor + dashboard + alert rules
make logging     # Loki + Promtail + Loki datasource + backend logs dashboard
make grafana     # port-forward Grafana to http://localhost:3000 (admin/prom-operator)
make destroy     # ordered teardown (asks 'yes'); reclaims everything, no orphaned ALB/SG
```

`make apply` is auto-approved; `make destroy` asks for confirmation. See
[`infra/k8s/README.md`](infra/k8s/README.md) (deploy runbook) and
[`monitoring/README.md`](monitoring/README.md) (observability) for details.

## Layout

```
backend/          FastAPI API (REST + WebSocket, AI adapter, SQLAlchemy models, Alembic)
frontend/         React live dashboard (session sidebar, lap timeline, incident panel)
telemetry-agent/  Python agent — Assetto Corsa Shared Memory reader
infra/terraform/  VPC, EKS, RDS, ECR, IAM (modular)
infra/k8s/        backend Helm chart + deploy runbook
monitoring/       Prometheus/Grafana values, Loki/Promtail, dashboards, alert rules
.github/workflows/ CI (lint/test/build) + CD (build -> ECR -> helm upgrade on EKS)
```

## Status

Phases 1–6 complete: telemetry + backend + DB, AI analysis + dashboard, Docker + CI/CD + AWS,
EKS + cloud-native observability, AI Incident Analyst + Ollama offline mode, and live real-time
dashboard with WebSocket. The frontend is a dark-themed three-panel racing monitor — session
sidebar, lap timeline with proportional time bars, and an incident panel with live alerts.
See `CLAUDE.md` for the detailed per-phase state.
