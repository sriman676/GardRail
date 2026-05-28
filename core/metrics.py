"""Enhanced metrics system with comprehensive observability."""
from prometheus_client import (
    Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
)

# Scanning metrics
scans_total = Counter(
    "guardrail_scans_total",
    "Total number of scans performed"
)
scans_by_level = Counter(
    "guardrail_scans_by_level",
    "Scans by threat level",
    ["level"]
)
scan_latency = Histogram(
    "guardrail_scan_latency_seconds",
    "Scan operation latency in seconds",
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0)
)

# API request metrics
requests_total = Counter(
    "guardrail_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
request_latency = Histogram(
    "guardrail_request_latency_seconds",
    "HTTP request latency in seconds",
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0)
)
request_errors = Counter(
    "guardrail_request_errors_total",
    "Total request errors",
    ["endpoint", "error_type"]
)

# Drift detection metrics
drift_checks_total = Counter(
    "guardrail_drift_checks_total",
    "Total drift checks performed"
)
drift_violations = Counter(
    "guardrail_drift_violations_total",
    "Total drift violations detected",
    ["drift_type"]
)

# Evolution metrics
evolution_runs = Counter(
    "guardrail_evolution_runs_total",
    "Total evolution runs triggered"
)
evolved_rules_added = Counter(
    "guardrail_evolved_rules_added_total",
    "Number of evolved rules added"
)
evolution_latency = Histogram(
    "guardrail_evolution_latency_seconds",
    "Evolution operation latency in seconds",
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0)
)

# LLM provider metrics
llm_calls_total = Counter(
    "guardrail_llm_calls_total",
    "Total LLM API calls",
    ["provider", "model", "status"]
)
llm_tokens = Counter(
    "guardrail_llm_tokens_total",
    "Total LLM tokens used (approximate)",
    ["provider", "type"]
)
llm_latency = Histogram(
    "guardrail_llm_latency_seconds",
    "LLM API call latency in seconds",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

# Database metrics
db_queries_total = Counter(
    "guardrail_db_queries_total",
    "Total database queries",
    ["operation", "table"]
)
db_query_latency = Histogram(
    "guardrail_db_query_latency_seconds",
    "Database query latency in seconds",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5)
)
db_connection_pool_size = Gauge(
    "guardrail_db_connection_pool_size",
    "Current database connection pool size"
)

# Alert metrics
alerts_total = Counter(
    "guardrail_alerts_total",
    "Total alerts triggered",
    ["threat_level"]
)
alert_decisions = Counter(
    "guardrail_alert_decisions_total",
    "Alert decisions made",
    ["decision_type"]
)
alert_response_time = Histogram(
    "guardrail_alert_response_time_seconds",
    "Time from alert to human decision in seconds",
    buckets=(1, 5, 10, 30, 60, 300, 600)
)

# Rate limiting metrics
rate_limit_violations = Counter(
    "guardrail_rate_limit_violations_total",
    "Rate limit violations",
    ["tenant_id"]
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    "guardrail_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)"
)
circuit_breaker_failures = Counter(
    "guardrail_circuit_breaker_failures_total",
    "Circuit breaker failure events"
)

# Configuration gauges
drift_threshold_gauge = Gauge(
    "guardrail_drift_threshold",
    "Current drift threshold"
)
active_rules_count = Gauge(
    "guardrail_active_rules_count",
    "Number of active injection rules"
)
staged_rules_count = Gauge(
    "guardrail_staged_rules_count",
    "Number of staged injection rules"
)

def metrics_latest() -> bytes:
    """Generate Prometheus format metrics."""
    return generate_latest()
