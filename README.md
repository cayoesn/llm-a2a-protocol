# 🌐 LLM Agent-to-Agent (A2A) Protocol (Enterprise Edition)

Protocolo de Comunicação e Coordenação Multi-Agente baseado nos padrões **FIPA ACL**, **W3C CloudEvents** e **Resilience Circuit Breaker**.

## 🌟 Arquitetura & Recursos Big-Tech
- **FIPA Contract Net Auction Protocol**: Mecanismo de leilão e negociação distribuída entre agentes para alocação de tarefas.
- **Resilience Manager (Circuit Breaker)**: Tolerância a falhas com estados `CLOSED`, `OPEN` e `HALF_OPEN` para prevenir falhas em cascata.
- **Dead Letter Queue (DLQ)**: Fila para isolamento e reprocessamento de mensagens com falha crítica.
- **Event Broker W3C CloudEvents**: Barramento de eventos assíncrono totalmente compatível com o padrão W3C CloudEvents.

## 🚀 Como Executar no Docker
```bash
docker compose up -d --build
```

## 🧪 Testes Unitários e Integração (>97% Cobertura)
```bash
docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "pip install pytest pytest-asyncio pytest-cov pydantic pydantic-settings httpx fastapi uvicorn && PYTHONPATH=. pytest"
```
