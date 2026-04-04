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

from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from incident_response_env.models import IncidentActionType, IncidentResponseState

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

    def reset(self) -> IncidentResponseObservation:
        """
        Reset the environment and start a new incident.
        """
        self._state = IncidentResponseState(
            episode_id=str(uuid4()), 
            step_count=0,
            incident_type="service_outage",
            root_cause="api_process_crashed",
            service_status="down",
            resolved=False,
            )
        self._reset_count += 1

        return IncidentResponseObservation(
            alert="API Service is down",
            metrics={
                "cpu": 5.0,
                "memory": 15.0,
                "error_rate": 1.0
            },
            logs="API Process terminated unexpectedly",
            status="down",
        )

    def step(self, action: IncidentResponseAction) -> IncidentResponseObservation:  # type: ignore[override]
        """
        Execute an action in the environment.
        """
        self._state.step_count += 1
        reward = 0.0
        done = False
        
        #process action + determine reward
        if action.action_type == IncidentActionType.inspect_logs:
            reward = 0.1
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
        
        observation = IncidentResponseObservation(
            alert="API Service incident",
            metrics={
            "cpu": 10.0,
            "memory": 20.0,
            "error_rate": 0.0 if self._state.resolved else 1.0
            },
            logs="Service logs inspected",
            status=self._state.service_status,
        )
        
        return observation, done, reward, {}

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
