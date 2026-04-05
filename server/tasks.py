
from dataclasses import dataclass


@dataclass
class IncidentTask:
    name: str
    description: str
    scenario_key: str
    difficulty: str

TASKS = {
    "easy_api_crash": IncidentTask(
        name="easy_api_crash",
        description="Resolve an API service outage caused by a crashed process.",
        scenario_key="easy_api_crash",
        difficulty="easy",
    ),

    "medium_memory_leak": IncidentTask(
        name="medium_memory_leak",
        description="Investigate and resolve a performance degradation caused by a memory leak.",
        scenario_key="medium_memory_leak",
        difficulty="medium",
    ),

    "hard_dependency_failure": IncidentTask(
        name="hard_dependency_failure",
        description="Resolve cascading service failures caused by a database outage.",
        scenario_key="hard_dependency_failure",
        difficulty="hard",
    ),
}