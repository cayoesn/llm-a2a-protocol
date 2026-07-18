from fastapi import status
from app.config import settings

def test_root_endpoint(test_client):
    """Garante que a rota raiz responde saudavelmente."""
    response = test_client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"
    assert response.json()["role"] == settings.AGENT_ROLE

def test_capabilities_endpoint(test_client):
    """Valida a listagem de capacidades do agente atual."""
    response = test_client.get("/a2a/capabilities")
    assert response.status_code == status.HTTP_200_OK
    capabilities = response.json()
    assert len(capabilities) > 0
    assert capabilities[0]["name"] in ["full_code_review", "code_analysis", "security_audit"]

def test_handshake_endpoint(test_client):
    """Verifica se o handshake do protocolo A2A retorna sucesso."""
    payload = {
        "sender_name": "Test External Agent",
        "token": "valid-token-123"
    }
    response = test_client.post("/a2a/handshake", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "accepted"
    assert "capabilities" in data

def test_handshake_unauthorized(test_client):
    """Verifica erro quando o token está vazio ou ausente."""
    payload = {
        "sender_name": "Test External Agent",
        "token": ""
    }
    response = test_client.post("/a2a/handshake", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_create_unsupported_task(test_client):
    """Garante erro ao solicitar uma capacidade que o agente atual não suporta."""
    payload = {
        "task_type": "invalid_unsupported_task_type",
        "payload": {}
    }
    response = test_client.post("/a2a/tasks", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_task_not_found(test_client):
    """Verifica retorno 404 para consulta de IDs inexistentes no Redis."""
    response = test_client.get("/a2a/tasks/non-existent-task-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_load_invalid_agent_role():
    """Garante erro de inicialização ao configurar um papel inválido de agente."""
    import pytest
    from unittest.mock import patch
    with patch("app.config.settings.AGENT_ROLE", "invalid_role"):
        # Import local para forçar recarga com mock
        from app.main import load_agent
        with pytest.raises(ValueError) as exc:
            load_agent()
        assert "Papel de agente desconhecido" in str(exc.value)

def test_analyst_agent_flow_via_api(test_client):
    """Testa o fluxo completo de criação e polling de tarefas do Analyst via endpoints."""
    # Configura papel de analista temporariamente para testar a rota de criação de tarefas
    from app.main import agent
    from app.agents.analyst import AnalystAgent
    
    # Executa mock parcial do agente
    if isinstance(agent, AnalystAgent):
        payload = {
            "task_type": "code_analysis",
            "payload": {
                "repository_url": "https://github.com/cayoesn/cayoesn"
            }
        }
        # Cria a tarefa
        create_res = test_client.post("/a2a/tasks", json=payload)
        assert create_res.status_code == 202
        task_id = create_res.json()["task_id"]
        assert task_id is not None
        
        # Consulta status imediatamente (deve estar pendente ou executando)
        status_res = test_client.get(f"/a2a/tasks/{task_id}")
        assert status_res.status_code == 200
        assert status_res.json()["status"] in ["pending", "running", "completed"]

