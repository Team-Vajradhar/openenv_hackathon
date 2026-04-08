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
from openenv.core.env_client import EnvClient

from models import IncidentActionType, IncidentResponseState
from server.graders import grade_incident
from server.incidents import INCIDENT_SCENARIOS, IncidentScenario
from server.tasks import TASKS

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

    def reset(self) -> IncidentResponseObservation:
        """Reset the environment and start a new incident."""

        scenario = self._select_scenario()

        self._state = IncidentResponseState(
            episode_id=str(uuid4()),
            incident_type=scenario.incident_type,
            root_cause=scenario.root_cause,
            service_status=scenario.initial_status,
            resolved=False,
            logs_checked=False,
            metrics_checked=False,
            step_count=0
        )

        return IncidentResponseObservation(
            alert=scenario.alert,
            metrics=scenario.metrics,
            logs=scenario.logs,
            status=self._state.service_status,
            reward=0.0,
            done=False,
        )

    def step(self, action: IncidentResponseAction) -> IncidentResponseObservation:
        """Execute an action in the environment."""

        self._state.step_count += 1

        reward = 0.0
        done = False

        if self._state.step_count >= MAX_STEPS:
            reward = -0.2
            done = True

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

            elif (
                self._state.root_cause == "memory_leak"
                and self._state.logs_checked
                and self._state.metrics_checked
            ):
                self._state.service_status = "healthy"
                self._state.resolved = True
                reward = 0.4

            elif self._state.root_cause == "memory_leak":
                self._state.service_status = "degraded"
                reward = 0.1

            else:
                reward = -0.2

        elif action.action_type == IncidentActionType.scale_service:

            if self._state.root_cause == "database_unavailable":
                self._state.service_status = "degraded"
                reward = 0.2
            else:
                reward = -0.1

        elif action.action_type == IncidentActionType.rollback_deployment:

            if self._state.root_cause == "deployment_bug":
                self._state.service_status = "healthy"
                self._state.resolved = True
                reward = 0.6
            else:
                reward = -0.1

        elif action.action_type == IncidentActionType.resolve_incident:

            if self._state.resolved:
                reward = grade_incident(self._state)
                done = True
            else:
                reward = -0.5

        observation = IncidentResponseObservation(
            alert="API Service incident",
            metrics={
                "cpu": 10.0,
                "memory": 20.0,
                "error_rate": 0.0 if self._state.resolved else 1.0
            },
            logs="Logs inspected" if self._state.logs_checked else "No logs checked yet",
            status=self._state.service_status,
            reward=reward,
            done=done,
        )

        return observation
    
    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        return self._state

        # @classmethod
        # async def from_docker_image(cls, image_name: str):
        #     from openenv.core.docker_env_runner import run_env_from_docker_image
            
        #     env = await run_env_from_docker_image(image_name)
        #     return env
