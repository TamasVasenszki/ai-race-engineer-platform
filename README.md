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
Assetto Corsa                      FastAPI backend  (REST + /metrics)
  + Python telemetry agent    →    PostgreSQL (RDS in prod)
  (Shared Memory API)              AI adapter layer (Claude/OpenAI/Ollama/Mock)
                                   React dashboard
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
backend/          FastAPI API (routers, AI adapter, SQLAlchemy models, Alembic)
frontend/         React (Vite) dashboard
telemetry-agent/  Python agent — Assetto Corsa Shared Memory reader
infra/terraform/  VPC, EKS, RDS, ECR, IAM (modular)
infra/k8s/        backend Helm chart + deploy runbook
monitoring/       Prometheus/Grafana values, Loki/Promtail, dashboards, alert rules
.github/workflows/ CI (lint/test/build) + CD (build -> ECR -> helm upgrade on EKS)
```

## Status

Phases 1–4 complete: telemetry + backend + DB, AI analysis + dashboard, Docker + CI/CD + AWS,
and EKS + cloud-native observability (metrics, logs, alerting). See `CLAUDE.md` for the detailed
per-phase state.
