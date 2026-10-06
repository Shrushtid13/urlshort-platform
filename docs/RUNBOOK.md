# Runbook

| Symptom | Check | Fix |
|---|---|---|
| Pods not Ready | `kubectl -n urlshort describe pod`, `/readyz` | Usually Postgres unreachable: check `statefulset/postgres`, secret values |
| High latency | Grafana p95 panel, cache hit ratio | Low hit ratio: check Redis pod; scale app via HPA |
| 5xx spike | `kubectl -n urlshort logs -l app=urlshort` | Roll back: `kubectl -n urlshort rollout undo deploy/urlshort` |
| Bad deploy | `kubectl rollout status` | `rollout undo`, then fix forward via PR |
