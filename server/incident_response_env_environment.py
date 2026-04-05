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

from random import random
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from incident_response_env.models import IncidentActionType, IncidentResponseState
from incident_response_env.server.incidents import INCIDENT_SCNEARIOS, IncidentScenario

try:
    from ..models import IncidentResponseAction, IncidentResponseObservation
except ImportError:
    from models import IncidentResponseAction, IncidentResponseObservation


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
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._reset_count = 0
        self._scenario: IncidentScenario | None = None

    def reset(self) -> IncidentResponseObservation:
        """
        Reset the environment and start a new incident.
        """
        scenario = random.choice(list(INCIDENT_SCNEARIOS.values()))
        
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
            metrics=scenario.metrics,
            logs="Logs not inspected yet",
            status=self._state.service_status,
            reward=0.0,
            done=False,
        )

    def step(self, action: IncidentResponseAction) -> IncidentResponseObservation:  # type: ignore[override]
        """
        Execute an action in the environment.
        """
        self._state.step_count += 1
        reward = 0.0
        done = False
        logs_output = "Logs not inspected yet"
        
        #process action + determine reward
        if action.action_type == IncidentActionType.inspect_logs:
            reward = 0.1
            self._state.logs_checked = True
            logs_output = self._scenario.logs if self._state.logs_checked else "Logs not inspected yet"
            
        elif action.action_type == IncidentActionType.inspect_metrics:
            reward = 0.1
            self._state.metrics_checked = True
            
        elif action.action_type == IncidentActionType.restart_service:
            if self._state.root_cause == "api_process_crashed":
                self._state.service_status = "healthy"
                self._state.resolved = True
                reward = 1.0
                done = True
            else:
                reward = -0.2
        elif action.action_type == IncidentActionType.resolve_incident:
            if self._state.resolved:
                reward = 0.5
                done = True
            else:
                reward = -0.5
        else:
            reward = -0.1
            
        logs_output = ("API process terminated unexpectedly" if self._state.logs_checked else "Logs not inspected yet")
        
        metrics_output = (self._scenario.metrics if self._state.metrics_checked else {
            "cpu": -1,
            "memory": -1,
            "error_rate": -1
        })
        
        observation = IncidentResponseObservation(
            alert="API Service incident",
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
