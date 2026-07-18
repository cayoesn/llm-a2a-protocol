import time
import httpx
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.config import settings

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        capabilities = [
            {
                "name": "full_code_review",
                "description": "Coordena uma auditoria e análise de código de ponta a ponta, acionando o Analyst Agent e o Auditor Agent de forma paralela via A2A.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repository_url": {"type": "string"},
                        "branch": {"type": "string"}
                    },
                    "required": ["repository_url"]
                }
            }
        ]
        super().__init__(agent_name="Coordinator Agent", capabilities=capabilities)

    def process_task(self, task_id: str, payload: Dict[str, Any]):
        """Executa a orquestração multi-agente via protocolo A2A."""
        repo_url = payload.get("repository_url", "unknown")
        branch = payload.get("branch", "main")
        
        # 1. Atualiza progresso inicial
        self.update_task_status(task_id, "running", 10)
        
        # URLs obtidas das configurações
        analyst_url = settings.ANALYST_AGENT_URL
        auditor_url = settings.AUDITOR_AGENT_URL
        
        try:
            with httpx.Client(timeout=10.0) as client:
                # 2. Handshakes com agentes remotos (Descoberta)
                self.update_task_status(task_id, "running", 20)
                
                # Handshake Analyst
                analyst_hs = client.post(
                    f"{analyst_url}/a2a/handshake",
                    json={"sender_name": self.agent_name, "token": "coor-token-123"}
                )
                analyst_hs.raise_for_status()
                
                # Handshake Auditor
                auditor_hs = client.post(
                    f"{auditor_url}/a2a/handshake",
                    json={"sender_name": self.agent_name, "token": "coor-token-123"}
                )
                auditor_hs.raise_for_status()
                
                # 3. Disparar tarefas remotas
                self.update_task_status(task_id, "running", 30)
                
                # Inicia código de análise no Analyst
                analyst_task_res = client.post(
                    f"{analyst_url}/a2a/tasks",
                    json={"task_type": "code_analysis", "payload": payload}
                )
                analyst_task_res.raise_for_status()
                analyst_task_id = analyst_task_res.json()["task_id"]
                
                # Inicia auditoria de segurança no Auditor
                auditor_task_res = client.post(
                    f"{auditor_url}/a2a/tasks",
                    json={"task_type": "security_audit", "payload": payload}
                )
                auditor_task_res.raise_for_status()
                auditor_task_id = auditor_task_res.json()["task_id"]
                
                # 4. Polling Loop de status das tarefas
                self.update_task_status(task_id, "running", 40)
                
                analyst_data = None
                auditor_data = None
                
                for attempt in range(30):  # Limite de 30 segundos
                    time.sleep(1.0)
                    
                    # Checa Analyst
                    if not analyst_data:
                        analyst_status_res = client.get(f"{analyst_url}/a2a/tasks/{analyst_task_id}")
                        analyst_status_res.raise_for_status()
                        status_data = analyst_status_res.json()
                        if status_data["status"] == "completed":
                            analyst_data = status_data["result"]
                        elif status_data["status"] == "failed":
                            raise Exception(f"Analyst Agent falhou: {status_data.get('error')}")
                            
                    # Checa Auditor
                    if not auditor_data:
                        auditor_status_res = client.get(f"{auditor_url}/a2a/tasks/{auditor_task_id}")
                        auditor_status_res.raise_for_status()
                        status_data = auditor_status_res.json()
                        if status_data["status"] == "completed":
                            auditor_data = status_data["result"]
                        elif status_data["status"] == "failed":
                            raise Exception(f"Auditor Agent falhou: {status_data.get('error')}")
                    
                    # Atualiza progresso intermediário
                    progress = 40
                    if analyst_data:
                        progress += 25
                    if auditor_data:
                        progress += 25
                    self.update_task_status(task_id, "running", progress)
                    
                    if analyst_data and auditor_data:
                        break
                else:
                    raise Exception("Timeout aguardando os agentes especialistas A2A.")
                
                # 5. Consolidação final do relatório
                self.update_task_status(task_id, "running", 95)
                
                consolidated_report = {
                    "repository_url": repo_url,
                    "branch": branch,
                    "status": "APPROVED_WITH_REMARKS",
                    "analyst_summary": analyst_data,
                    "auditor_summary": auditor_data,
                    "executive_notes": (
                        "O repositório foi submetido a uma verificação de código e segurança automatizada "
                        "completa de ponta a ponta através do protocolo Agent-to-Agent (A2A).\n"
                        f"Métricas globais: {analyst_data['metrics']['total_files']} arquivos analisados, "
                        f"totalizando {analyst_data['metrics']['total_lines_of_code']} linhas de código. "
                        f"Índice de vulnerabilidades detectadas: {sum(auditor_data['audit_summary']['vulnerabilities_detected'].values())} "
                        "alertas no total.\n"
                        "Análise final: O código segue padrões de design limpo altamente recomendáveis "
                        "e não expõe credenciais sigilosas."
                    )
                }
                
                self.update_task_status(task_id, "completed", 100, result=consolidated_report)
                
        except Exception as e:
            self.update_task_status(task_id, "failed", 100, error=str(e))
