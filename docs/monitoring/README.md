# Alloist Monitoring (Prometheus + Grafana)

## Endpoints

| Service        | Port | Endpoints                                      |
|----------------|------|------------------------------------------------|
| Token Service  | 8000 | `GET /metrics`, `GET /health`, `GET /ready`    |
| Policy Service | 8001 | `GET /metrics`, `GET /health`, `GET /ready`   |

- **`/metrics`** – Prometheus exposition format (text/plain)
- **`/health`** – Liveness probe (always 200)
- **`/ready`** – Readiness probe (200 if DB is reachable, 503 otherwise)

## Prometheus Scrape Config

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "alloist-token-service"
    static_configs:
      - targets: ["localhost:8000"]
    metrics_path: /metrics

  - job_name: "alloist-policy-service"
    static_configs:
      - targets: ["localhost:8001"]
    metrics_path: /metrics
```

## Metrics

| Metric                         | Type    | Labels   | Description                              |
|--------------------------------|---------|----------|------------------------------------------|
| `enforcement_checks_total`     | Counter | service  | Enforcement checks (X-Request-Type)       |
| `policy_evaluations_total`     | Counter | service  | Policy evaluations                        |
| `token_issuance_total`         | Counter | service  | Tokens minted                             |
| `revocation_events_total`      | Counter | service  | Tokens revoked                            |
| `consent_requests_total`       | Counter | service  | Consent requests created                  |
| `enforcement_latency_ms`       | Histogram | service | Latency of enforcement checks (ms)      |
| `policy_evaluation_latency_ms` | Histogram | service | Latency of policy evaluations (ms)     |
| `http_request_duration_ms`     | Histogram | service, method, path, status | HTTP request latency (ms) |

## Grafana

1. Add Prometheus as a data source (URL: `http://localhost:9090` or your Prometheus URL).
2. Create dashboards using the metrics above.

### Example queries

- **Token issuance rate**: `rate(token_issuance_total[5m])`
- **Policy evaluation p95 (ms)**: `histogram_quantile(0.95, rate(policy_evaluation_latency_ms_bucket[5m]))`
- **HTTP request p95 by path**: `histogram_quantile(0.95, sum(rate(http_request_duration_ms_bucket[5m])) by (le, path))`
