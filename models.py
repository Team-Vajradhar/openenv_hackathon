# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Incident Response Env Environment.

The incident_response_env environment is a simple test environment that echoes back messages.
"""

from typing import Dict,Optional

from openenv.core.env_server.types import Action, BaseModel, Observation
from pydantic import Field


class IncidentResponseAction(Action):
    """Action for the Incident Response Env environment"""

    # message: str = Field(..., description="Message to echo back")
    action_type: str = Field(..., description="Type of action to perform, e.g., 'investigate', 'mitigate', 'escalate'")
    target_service: Optional[str] = Field(default=None, description="The service or component to target with the action")
    


class IncidentResponseObservation(Observation):
    """Observation from the Incident Response Env environment"""

    # echoed_message: str = Field(default="", description="The echoed message")
    # message_length: int = Field(default=0, description="Length of the echoed message")
    alert: str = Field(description="Alert message describing the incident")
    metrics: Dict[str, float] = Field(description="System metrics like CPU, memory, error rate")
    logs: str = Field(description="Relevant log snippet")
    status: str = Field(description="Current service status: healthy, degraded, down")
    

class IncidentResponseState(BaseModel):
    """Internal State of Environment, not visible to the agent"""

    incident_type: str = Field(description="Type of incident, e.g., 'DDoS', 'Data Breach', 'Service Outage' occuring in the system")
    root_cause: str = Field(description="Underlying cause of the incident, e.g., 'Misconfiguration', 'Vulnerability Exploitation', 'Hardware Failure'")
    service_status: str = Field(default="degraded",description="Current status of the affected service, e.g., 'healthy', 'degraded', 'down'")
    resolved: bool = Field(default=False, description="Whether the incident has been resolved")
    step_count: int = Field(default=0, description="Number of actions taken in the episode")
    
