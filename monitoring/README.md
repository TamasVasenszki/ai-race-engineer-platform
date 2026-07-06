# Monitoring — Prometheus + Grafana (#26)

Observability for the EKS backend: the **kube-prometheus-stack** community chart (Prometheus +
Grafana + node-exporter + kube-state-metrics) scrapes the backend's `/metrics` endpoint and a
Grafana dashboard shows request rate, latency, error rate, and pod CPU/memory.

Assumes the cluster + backend are already up (`make apply`). Installed separately from the
standard bring-up because the stack is heavy — opt in with `make monitoring`.

## Install

```sh
make monitoring
```

Which does:
1. `helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack`
   into the `monitoring` namespace with [`kube-prometheus-stack-values.yaml`](./kube-prometheus-stack-values.yaml)
   (Alertmanager off, ephemeral storage, scrape all ServiceMonitors).
2. `kubectl apply -f` [`backend-servicemonitor.yaml`](./backend-servicemonitor.yaml) — Prometheus
   scrapes the backend Service's `http` port at `/metrics`.
3. Creates the Grafana dashboard ConfigMap from [`dashboards/backend.json`](./dashboards/backend.json),
   labeled `grafana_dashboard=1` so the Grafana sidecar auto-imports it.

The backend image must be the instrumented one (`/metrics` present) — rebuild/redeploy via
`make push` + `make deploy` (or a CD run) if the running image predates #26.

## Access Grafana

Grafana is **not** exposed publicly (no ALB) — reach it via port-forward:

```sh
make grafana   # kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80
```

Then open http://localhost:3000. Default login is `admin` / `prom-operator` (the chart default;
acceptable because access is port-forward-only). No password is stored in this repo — override at
install with `helm ... --set grafana.adminPassword=...` if a custom one is ever needed. The
dashboard is **AI Race Engineer — Backend**.

## Notes

- Chart version is unpinned in the Makefile default — pin at install if reproducibility matters.
- Metric names come from `prometheus-fastapi-instrumentator` (`http_requests_total`,
  `http_request_duration_seconds_*`); if a panel is empty, confirm the exact names via
  `curl http://<alb>/metrics` and adjust the queries in `dashboards/backend.json`.
- Alerting (Alertmanager) and log aggregation (Loki/Promtail) come in #27.
- Monitoring is ephemeral and provisions no ALB/PVC, so `make destroy` needs no extra teardown —
  `terraform destroy` of the cluster reclaims everything.
