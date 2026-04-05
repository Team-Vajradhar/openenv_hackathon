from dataclasses import dataclass

@dataclass
class IncidentScenario:
    incident_type: str
    root_cause: str
    initial_status: str
    alert: str
    logs: str
    metrics: dict

INCIDENT_SCENARIOS = {
    "easy_api_crash": IncidentScenario(
        incident_type="service_outage",
        root_cause="api_process_crashed",
        initial_status="down",
        alert="API Service is down",
        logs="API process terminated unexpectedly",
        metrics={
            "cpu": 5.0, 
            "memory": 15.0,
            "error_rate": 1.0,
        }
    ),
    "medium_memory_leak": IncidentScenario(
        incident_type="performance_degradation",
        root_cause="memory_leak",
        initial_status="degraded",
        alert="API latency increasing",
        logs="Memory allocation growing continuously",
        metrics={
            "cpu": 40.0, 
            "memory": 95.0,
            "error_rate": 0.2,
        }
    ),
    "hard_cascading_failure": IncidentScenario(
        incident_type="cascading_failure",
        root_cause="database_unavailable",
        initial_status="down",
        alert="Multiple Services Failing",
        logs="Database connection timeout errors",
        metrics={
            "cpu": 20.0,
            "memory": 30.0,
            "error_rate": 0.9,
        }
    )
}