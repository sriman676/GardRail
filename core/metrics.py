from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Scanning metrics
scans_total = Counter("guardrail_scans_total", "Total number of scans performed")
scans_by_level = Counter("guardrail_scans_by_level", "Scans by threat level", ["level"])

# Evolution metrics
evolution_runs = Counter("guardrail_evolution_runs_total", "Total evolution runs triggered")
evolved_rules_added = Counter("guardrail_evolved_rules_added_total", "Number of evolved rules added")

# Configuration gauges
drift_threshold_gauge = Gauge("guardrail_drift_threshold", "Current drift threshold")

def metrics_latest() -> bytes:
    return generate_latest()
