from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from app.config import settings
from app.protocol.schemas import (
    HandshakeRequest, 
    HandshakeResponse, 
    TaskCreateRequest, 
    TaskResponse, 
    TaskStatusResponse,
    CapabilityItem
)
from app.agents.coordinator import CoordinatorAgent
from app.agents.analyst import AnalystAgent
from app.agents.auditor import AuditorAgent

# Inicialização do FastAPI
app = FastAPI(
    title=f"A2A Agent Service - {settings.AGENT_ROLE.capitalize()}",
    version="1.0.0",
    description=f"Microsserviço de Agente rodando sob o papel de {settings.AGENT_ROLE} em conformidade com o protocolo A2A."
)

# Instanciação dinâmica do agente com base no papel configurado
def load_agent():
    role = settings.AGENT_ROLE.lower()
    if role == "coordinator":
        return CoordinatorAgent()
    elif role == "analyst":
        return AnalystAgent()
    elif role == "auditor":
        return AuditorAgent()
    else:
        raise ValueError(f"Papel de agente desconhecido ou inválido: {role}")

agent = load_agent()

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "agent_name": agent.agent_name,
        "role": settings.AGENT_ROLE,
        "version": "1.0.0"
    }

@app.get("/a2a/capabilities", response_model=list[CapabilityItem])
def get_capabilities():
    """Retorna a lista de capacidades do agente atual."""
    return agent.capabilities

@app.post("/a2a/handshake", response_model=HandshakeResponse)
def handshake(request: HandshakeRequest):
    """Realiza o handshake e valida o protocolo de comunicação entre agentes."""
    if not request.token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token de handshake ausente ou inválido."
        )
    return HandshakeResponse(
        status="accepted",
        agent_name=agent.agent_name,
        capabilities=agent.capabilities
    )

@app.post("/a2a/tasks", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
def create_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):
    """Cria uma nova tarefa de processamento em background."""
    # Valida se a capacidade solicitada é suportada pelo agente atual
    supported_capabilities = [cap["name"] for cap in agent.capabilities]
    if request.task_type not in supported_capabilities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Capacidade '{request.task_type}' não suportada por este agente. Suportadas: {supported_capabilities}"
        )
        
    # Inicializa o registro da tarefa no Redis
    task_id = agent.create_task_record(request.task_type, request.payload)
    
    # Envia a tarefa para execução assíncrona no background loop
    background_tasks.add_task(agent.process_task, task_id, request.payload)
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        estimated_duration_seconds=5
    )

@app.get("/a2a/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    """Consulta o progresso e o resultado de uma tarefa pelo ID."""
    task_data = agent.get_task_status(task_id)
    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {task_id} não encontrada."
        )
    return TaskStatusResponse(
        task_id=task_id,
        status=task_data["status"],
        progress_percent=task_data["progress_percent"],
        result=task_data.get("result"),
        error=task_data.get("error")
    )
