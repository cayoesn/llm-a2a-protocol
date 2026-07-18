import json
import uuid
from typing import Dict, Any, Optional
from app.database.redis_client import get_redis_client

class BaseAgent:
    def __init__(self, agent_name: str, capabilities: list):
        self.agent_name = agent_name
        self.capabilities = capabilities

    def create_task_record(self, task_type: str, payload: Dict[str, Any]) -> str:
        """Cria um registro inicial de tarefa no Redis."""
        task_id = str(uuid.uuid4())
        redis_client = get_redis_client()
        
        task_data = {
            "task_id": task_id,
            "task_type": task_type,
            "status": "pending",
            "progress_percent": 0,
            "result": None,
            "error": None
        }
        
        redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=3600)  # Expira em 1 hora
        return task_id

    def update_task_status(
        self, 
        task_id: str, 
        status: str, 
        progress_percent: int, 
        result: Optional[Dict[str, Any]] = None, 
        error: Optional[str] = None
    ):
        """Atualiza os detalhes e progresso de uma tarefa no Redis."""
        redis_client = get_redis_client()
        key = f"task:{task_id}"
        raw_data = redis_client.get(key)
        
        if raw_data:
            task_data = json.loads(raw_data)
        else:
            task_data = {"task_id": task_id, "task_type": "unknown"}
            
        task_data.update({
            "status": status,
            "progress_percent": progress_percent,
            "result": result,
            "error": error
        })
        
        redis_client.set(key, json.dumps(task_data), ex=3600)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Recupera os detalhes de uma tarefa do Redis."""
        redis_client = get_redis_client()
        raw_data = redis_client.get(f"task:{task_id}")
        if raw_data:
            return json.loads(raw_data)
        return None
