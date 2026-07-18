import pytest
from unittest.mock import MagicMock, patch
from app.agents.coordinator import CoordinatorAgent
from app.agents.analyst import AnalystAgent
from app.agents.auditor import AuditorAgent

def test_analyst_agent_process_task():
    """Valida o ciclo de execução do Analyst Agent e persistência no Redis."""
    agent = AnalystAgent()
    task_id = agent.create_task_record("code_analysis", {})
    
    agent.process_task(task_id, {"repository_url": "https://github.com/cayoesn/cayoesn"})
    
    status_data = agent.get_task_status(task_id)
    assert status_data["status"] == "completed"
    assert status_data["progress_percent"] == 100
    assert "language_breakdown" in status_data["result"]
    assert "metrics" in status_data["result"]

def test_auditor_agent_process_task():
    """Valida o ciclo de execução do Auditor Agent e persistência no Redis."""
    agent = AuditorAgent()
    task_id = agent.create_task_record("security_audit", {})
    
    agent.process_task(task_id, {"repository_url": "https://github.com/cayoesn/cayoesn"})
    
    status_data = agent.get_task_status(task_id)
    assert status_data["status"] == "completed"
    assert status_data["progress_percent"] == 100
    assert "audit_summary" in status_data["result"]
    assert len(status_data["result"]["findings_details"]) > 0

@patch("httpx.Client")
def test_coordinator_agent_success(mock_client_class):
    """Testa a orquestração completa bem-sucedida do Coordenador com mocks de rede."""
    # Configura os mocks para as chamadas HTTPX
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client
    
    # Mock de Handshake do Analyst
    mock_res_analyst_hs = MagicMock()
    mock_res_analyst_hs.status_code = 200
    mock_res_analyst_hs.json.return_value = {"status": "accepted"}
    
    # Mock de Handshake do Auditor
    mock_res_auditor_hs = MagicMock()
    mock_res_auditor_hs.status_code = 200
    mock_res_auditor_hs.json.return_value = {"status": "accepted"}
    
    # Mock de Início de Tarefa no Analyst
    mock_res_analyst_task = MagicMock()
    mock_res_analyst_task.status_code = 202
    mock_res_analyst_task.json.return_value = {"task_id": "analyst-id-123"}
    
    # Mock de Início de Tarefa no Auditor
    mock_res_auditor_task = MagicMock()
    mock_res_auditor_task.status_code = 202
    mock_res_auditor_task.json.return_value = {"task_id": "auditor-id-123"}
    
    # Mock de Consulta de status (Analyst e dps Auditor)
    mock_res_analyst_status = MagicMock()
    mock_res_analyst_status.status_code = 200
    mock_res_analyst_status.json.return_value = {
        "status": "completed",
        "progress_percent": 100,
        "result": {
            "metrics": {"total_files": 10, "total_lines_of_code": 500}
        }
    }
    
    mock_res_auditor_status = MagicMock()
    mock_res_auditor_status.status_code = 200
    mock_res_auditor_status.json.return_value = {
        "status": "completed",
        "progress_percent": 100,
        "result": {
            "audit_summary": {"vulnerabilities_detected": {"low": 1}}
        }
    }
    
    # Define a sequência de retornos para os posts e gets
    mock_client.post.side_effect = [
        mock_res_analyst_hs,  # Handshake Analyst
        mock_res_auditor_hs,  # Handshake Auditor
        mock_res_analyst_task, # Task Analyst
        mock_res_auditor_task  # Task Auditor
    ]
    
    mock_client.get.side_effect = [
        mock_res_analyst_status, # Get Analyst Status
        mock_res_auditor_status  # Get Auditor Status
    ]
    
    # Executa a tarefa do coordenador
    agent = CoordinatorAgent()
    task_id = agent.create_task_record("full_code_review", {})
    
    agent.process_task(task_id, {"repository_url": "https://github.com/cayoesn/cayoesn"})
    
    status_data = agent.get_task_status(task_id)
    assert status_data["status"] == "completed"
    assert status_data["progress_percent"] == 100
    assert status_data["result"]["status"] == "APPROVED_WITH_REMARKS"
    assert "executive_notes" in status_data["result"]

@patch("httpx.Client")
def test_coordinator_agent_failure(mock_client_class):
    """Testa o cenário onde um dos agentes falha e o coordenador registra o erro."""
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client
    
    mock_res_analyst_hs = MagicMock()
    mock_res_analyst_hs.status_code = 200
    
    mock_res_auditor_hs = MagicMock()
    mock_res_auditor_hs.status_code = 200
    
    mock_res_analyst_task = MagicMock()
    mock_res_analyst_task.status_code = 202
    mock_res_analyst_task.json.return_value = {"task_id": "analyst-id-123"}
    
    mock_res_auditor_task = MagicMock()
    mock_res_auditor_task.status_code = 202
    mock_res_auditor_task.json.return_value = {"task_id": "auditor-id-123"}
    
    mock_res_analyst_status = MagicMock()
    mock_res_analyst_status.status_code = 200
    mock_res_analyst_status.json.return_value = {
        "status": "failed",
        "progress_percent": 100,
        "error": "Erro crítico de estouro de memória no Analyst"
    }
    
    mock_client.post.side_effect = [
        mock_res_analyst_hs,
        mock_res_auditor_hs,
        mock_res_analyst_task,
        mock_res_auditor_task
    ]
    
    mock_client.get.side_effect = [
        mock_res_analyst_status
    ]
    
    agent = CoordinatorAgent()
    task_id = agent.create_task_record("full_code_review", {})
    
    agent.process_task(task_id, {"repository_url": "https://github.com/cayoesn/cayoesn"})
    
    status_data = agent.get_task_status(task_id)
    assert status_data["status"] == "failed"
    assert "Analyst Agent falhou" in status_data["error"]
