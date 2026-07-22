from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram


REQUEST_COUNT = Counter(
    "lb_requests_total",
    "Total LB requests",
    ["method", "status"],
)

REQUEST_DURATION = Histogram(
    "lb_request_duration_seconds",
    "Request duration in seconds",
    ["method"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

BACKENDS_ACTIVE = Gauge(
    "lb_backends_active",
    "Currently active backends",
)

BACKENDS_HEALTHY = Gauge(
    "lb_backends_healthy",
    "Currently healthy backends",
)

RETRIES_TOTAL = Counter(
    "lb_retries_total",
    "Total request retries",
)
