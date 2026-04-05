# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Incident Response Env Environment Implementation.

A simple test environment that echoes back messages sent to it.
Perfect for testing HTTP server infrastructure.
"""

import random
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from incident_response_env.models import IncidentActionType, IncidentResponseState
from incident_response_env.server.graders import grade_incident
from incident_response_env.server.incidents import INCIDENT_SCENARIOS, IncidentScenario
from incident_response_env.server.tasks import TASKS

try:
    from ..models import IncidentResponseAction, IncidentResponseObservation
except ImportError:
    from models import IncidentResponseAction, IncidentResponseObservation

MAX_STEPS = 10

class IncidentResponseEnvironment(Environment):
    """
    A simple echo environment that echoes back messages.

    This environment is designed for testing the HTTP server infrastructure.
    It maintains minimal state and simply echoes back whatever message it receives.

    Example:
        >>> env = IncidentResponseEnvironment()
        >>> obs = env.reset()
        >>> print(obs.echoed_message)  # "Incident Response Env environment ready!"
        >>>
        >>> obs = env.step(IncidentResponseAction(message="Hello"))
        >>> print(obs.echoed_message)  # "Hello"
        >>> print(obs.message_length)  # 5
    """

    # Enable concurrent WebSocket sessions.
    # Set to True if your environment isolates state between instances.
    # When True, multiple WebSocket clients can connect simultaneously, each
    # getting their own environment instance (when using factory mode in app.py).
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the incident_response_env environment."""
        self._state: IncidentResponseState | None = None
        self._reset_count = 0
        self._scenario: IncidentScenario | None = None
        self._task = None

    def reset(self, task_name: str | None = None) -> IncidentResponseObservation:
        """
        Reset the environment and start a new incident.
        """
        if task_name is None:
            task = random.choice(list(TASKS.values()))
        else:
            task = TASKS[task_name]
        scenario = INCIDENT_SCENARIOS[task.scenario_key]
        
        self._task = task        
        self._scenario = scenario
        self._state = IncidentResponseState(
            episode_id=str(uuid4()), 
            step_count=0,
            incident_type=scenario.incident_type,
            root_cause=scenario.root_cause,
            service_status=scenario.initial_status,
            resolved=False,
            logs_checked=False,
            metrics_checked=False,
            )
        self._reset_count += 1

        return IncidentResponseObservation(
            alert=scenario.alert,
            metrics={
                "cpu": -1.0,
                "memory": -1.0,
                "error_rate": -1.0
            },
            logs="Logs not inspected yet",
            status=self._state.service_status,
            reward=0.0,
            done=False,
        )

    def step(self, action: IncidentResponseAction) -> IncidentResponseObservation:  # type: ignore[override]
        """
        Execute an action in the environment.
        """
        assert self._scenario is not None, "Environment must be reset before calling step()"
        assert self._state is not None, "Environment must be reset before calling step()"
        reward = 0.0
        done = False
        
        if self._state.step_count >= MAX_STEPS:
            done = True
            reward = -0.2
            
        elif action.action_type == IncidentActionType.inspect_logs:
            reward = 0.1
            self._state.logs_checked = True
            
        elif action.action_type == IncidentActionType.inspect_metrics:
            reward = 0.1
            self._state.metrics_checked = True
            
        elif action.action_type == IncidentActionType.restart_service:
            if self._state.root_cause == "api_process_crashed":
                self._state.service_status = "healthy"
                self._state.resolved = True
                reward = 0.5
            elif self._state.root_cause == "memory_leak":
                self._state.service_status = "degraded"
                reward = 0.1
            else:
                reward = -0.2
        elif action.action_type == IncidentActionType.resolve_incident:
            if self._state.resolved:
                reward = grade_incident(self._state)
                done = True
            else:
                reward = -0.5
        else:
            reward = -0.1
            
        self._state.step_count += 1
        logs_output = (self._scenario.logs if self._state.logs_checked else "Logs not inspected yet")
        
        metrics_output = (self._scenario.metrics if self._state.metrics_checked else {
            "cpu": -1.0,
            "memory": -1.0,
            "error_rate": -1.0
        })
        
        observation = IncidentResponseObservation(
            alert=("Incident Resolved" if self.self._state.resolved else self._scenario.alert),
            metrics=metrics_output,
            logs=logs_output,
            status=self._state.service_status,
            reward=reward,
            done=done,
        )
        
        return observation

        # return IncidentResponseObservation(
        #     echoed_message=message,
        #     message_length=length,
        #     done=False,
        #     reward=reward,
        #     metadata={"original_message": message, "step": self._state.step_count},
        # )

    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        return self._state
