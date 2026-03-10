# alloist-logging

Structured JSON logging for Alloist backend services. Compatible with Datadog, ELK, and OpenTelemetry collectors.

## Usage

```python
from alloist_logging import get_logger, log_event, logging_middleware

# In main.py - add middleware first (before CORS)
app.add_middleware(logging_middleware("token_service"))

# In routes
logger = get_logger("token_service")
log_event(logger, action="token_created", result="success", org_id=str(ctx.org_id), user_id=str(ctx.user_id), token_id=str(token_id))
```

## Install

```bash
pip install -e ../../packages/structured_logging
```
