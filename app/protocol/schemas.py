from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class HandshakeRequest(BaseModel):
    sender_name: str
    token: str

class CapabilityItem(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class HandshakeResponse(BaseModel):
    status: str = "accepted"
    agent_name: str
    capabilities: List[CapabilityItem]

class TaskCreateRequest(BaseModel):
    task_type: str
    payload: Dict[str, Any]
    callback_url: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    estimated_duration_seconds: int

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress_percent: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
