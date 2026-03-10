"""Prometheus metrics definitions and registry."""

from prometheus_client import Counter, Histogram, REGISTRY, generate_latest

LATENCY_BUCKETS = (5, 25, 50, 100, 250, 500, 1000, 2500, 5000)

# Define metrics once at module level (prometheus_client rejects duplicate names)
_enforcement_checks_total = Counter(
    "enforcement_checks_total",
    "Total number of enforcement checks",
    ["service"],
    registry=REGISTRY,
)
_policy_evaluations_total = Counter(
    "policy_evaluations_total",
    "Total number of policy evaluations",
    ["service"],
    registry=REGISTRY,
)
_token_issuance_total = Counter(
    "token_issuance_total",
    "Total number of tokens issued",
    ["service"],
    registry=REGISTRY,
)
_revocation_events_total = Counter(
    "revocation_events_total",
    "Total number of token revocations",
    ["service"],
    registry=REGISTRY,
)
_consent_requests_total = Counter(
    "consent_requests_total",
    "Total number of consent requests created",
    ["service"],
    registry=REGISTRY,
)
_enforcement_latency_ms = Histogram(
    "enforcement_latency_ms",
    "Latency of enforcement checks in milliseconds",
    ["service"],
    buckets=LATENCY_BUCKETS,
    registry=REGISTRY,
)
_policy_evaluation_latency_ms = Histogram(
    "policy_evaluation_latency_ms",
    "Latency of policy evaluations in milliseconds",
    ["service"],
    buckets=LATENCY_BUCKETS,
    registry=REGISTRY,
)
_http_request_duration_ms = Histogram(
    "http_request_duration_ms",
    "HTTP request duration in milliseconds",
    ["service", "method", "path", "status"],
    buckets=(5, 25, 50, 100, 250, 500, 1000, 2500, 5000),
    registry=REGISTRY,
)


def create_metrics(service_name: str):
    """Return a metrics object with inc/observe helpers bound to the given service."""
    labels = {"service": service_name}

    class Metrics:
        def inc_enforcement_checks(self):
            _enforcement_checks_total.labels(**labels).inc()

        def inc_policy_evaluations(self):
            _policy_evaluations_total.labels(**labels).inc()

        def inc_token_issuance(self):
            _token_issuance_total.labels(**labels).inc()

        def inc_revocation_events(self):
            _revocation_events_total.labels(**labels).inc()

        def inc_consent_requests(self):
            _consent_requests_total.labels(**labels).inc()

        def observe_enforcement_latency_ms(self, ms: float):
            _enforcement_latency_ms.labels(**labels).observe(ms)

        def observe_policy_evaluation_latency_ms(self, ms: float):
            _policy_evaluation_latency_ms.labels(**labels).observe(ms)

        def observe_http_request(self, method: str, path: str, status: int, duration_ms: float):
            _http_request_duration_ms.labels(
                **labels,
                method=method,
                path=path,
                status=str(status),
            ).observe(duration_ms)

    return Metrics()


def get_metrics_output():
    """Return Prometheus text format for the default registry."""
    return generate_latest(REGISTRY)
