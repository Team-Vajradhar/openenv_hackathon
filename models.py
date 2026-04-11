# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Incident Response Env Environment.
"""

from enum import Enum
from typing import Dict,Optional

from openenv.core.env_server.types import Action, BaseModel, Observation, State
from pydantic import Field

class IncidentActionType(str, Enum):
    """Allowed actions in the Incident Response environment."""
    
    inspect_logs="inspect_logs"
    inspect_metrics="inspect_metrics"
    restart_service="restart_service"
    scale_service="scale_service"
    rollback_deployment="rollback_deployment"
    resolve_incident="resolve_incident"
    
class IncidentResponseAction(Action):
    """Action for the Incident Response Env environment"""

    # message: str = Field(..., description="Message to echo back")
    action_type: IncidentActionType = Field(...,description="Action to perform: inspect_logs, inspect_metrics, restart_service, scale_service, rollback_deployment, resolve_incident")
    target_service: Optional[str] = Field(default=None, description="The service or component to target with the action")
    


class IncidentResponseObservation(Observation):
    """Observation from the Incident Response Env environment"""

    # echoed_message: str = Field(default="", description="The echoed message")
    # message_length: int = Field(default=0, description="Length of the echoed message")
    alert: str = Field(description="Alert message describing the incident")
    metrics: Dict[str, float] = Field(description="System metrics like CPU, memory, error rate")
    logs: str = Field(description="Relevant log snippet")
    status: str = Field(description="Current service status: healthy, degraded, down")
    reward: Optional[float] = Field(default=0.01, description="Reward assigned for the previous action")
    done: bool = Field(description="Whether the episode has finished")
    

class IncidentResponseState(State):
    """Internal State of Environment, not visible to the agent"""

    episode_id: str = Field(...,description="Stores the unique Id of the current episode")
    incident_type: str = Field(description="Type of incident, e.g., 'DDoS', 'Data Breach', 'Service Outage' occuring in the system")
    root_cause: str = Field(description="Underlying cause of the incident, e.g., 'Misconfiguration', 'Vulnerability Exploitation', 'Hardware Failure'")
    service_status: str = Field(default="degraded",description="Current status of the affected service, e.g., 'healthy', 'degraded', 'down'")
    resolved: bool = Field(default=False, description="Whether the incident has been resolved")
    logs_checked: bool = Field(default=False, description="Whether logs have been inspected")
    metrics_checked: bool = Field(default=False, description="Whether metrics have been checked")
    scale_level: int = Field(default=1, description="Number of service replicas")
    step_count: int = Field(default=0, description="Number of actions taken in the episode")
    
