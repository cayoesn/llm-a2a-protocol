import json
import time
import uuid
from typing import Any
from pydantic import BaseModel, Field


class AgentEventMessage(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_agent_id: str
    target_agent_id: str
    performative: str  # CFP, PROPOSE, ACCEPT_PROPOSAL, INFORM, etc.
    payload: dict[str, Any]
    traceparent: str = Field(default_factory=lambda: f"00-{uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-01")
    timestamp: float = Field(default_factory=time.time)


class AgentEventBroker:
    """Enterprise Event-Driven Broker para o Protocolo Agent-to-Agent.
    
    Gerencia canais de eventos assíncronos desacoplados com propagação de
    cabeçalhos de rastreamento distribuído OpenTelemetry (W3C Trace Context).
    """

    def __init__(self) -> None:
        self.channels: dict[str, list[AgentEventMessage]] = {}

    def publish_event(self, channel_name: str, event: AgentEventMessage) -> None:
        if channel_name not in self.channels:
            self.channels[channel_name] = []
        self.channels[channel_name].append(event)

    def consume_events(self, channel_name: str) -> list[AgentEventMessage]:
        events = self.channels.get(channel_name, [])
        self.channels[channel_name] = []
        return events


# Instância Singleton do Event Broker
event_broker = AgentEventBroker()
