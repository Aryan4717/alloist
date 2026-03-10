# alloist-metrics

Prometheus metrics and health endpoints for Alloist backend services.

## Usage

```python
from alloist_metrics import create_metrics, get_metrics_output, metrics_middleware, health_router

# In main.py
app.add_middleware(metrics_middleware("token_service"))

# Mount /metrics
@app.get("/metrics")
def metrics():
    from fastapi.responses import Response
    return Response(content=get_metrics_output(), media_type="text/plain; version=0.0.4")

# Mount /health and /ready
app.include_router(health_router(check_ready=db_ping), include_in_schema=False)

# In routes
metrics = create_metrics("token_service")
metrics.inc_token_issuance()
```

## Install

```bash
pip install -e ../../packages/backend_metrics
```
