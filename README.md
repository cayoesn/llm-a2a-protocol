# Agent-to-Agent Protocol Engine (llm-a2a-protocol) 🌐

![Status](https://img.shields.io/badge/Status-Under_Development-orange?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

> Uma engine avançada de cooperação e comunicação multi-agente baseada no protocolo descentralizado de código aberto **Agent-to-Agent (A2A)** da Linux Foundation.

Este repositório é uma implementação de ponta a ponta que simula a cooperação descentralizada e assíncrona entre agentes inteligentes de propósitos distintos, mantendo a privacidade de prompts, histórico e ferramentas internas de forma totalmente opaca (Opaque Execution).

---

## 📚 Sumário

- [🧭 Visão Geral](#-visão-geral)
- [🏗️ Arquitetura e Tecnologias](#-arquitetura-e-tecnologias)
- [📁 Estrutura do Repositório](#-estrutura-do-repositório)
- [🚀 O Protocolo A2A](#-o-protocolo-a2a)
- [🛠️ Instalação e Setup](#-instalação-e-setup)
- [🧪 Como Usar (Endpoints)](#-como-usar-endpoints)
- [📊 Observabilidade e Logs](#-observabilidade-e-logs)
- [✅ Testes e Coverage](#-testes-e-coverage)

---

## 🧭 Visão Geral

O **Agent-to-Agent (A2A) Protocol Engine** resolve um dos maiores desafios em sistemas de agentes compostos (*composite agents*): **Interoperabilidade Segura**.

Quando múltiplos agentes de diferentes proprietários (ou com diferentes bases de conhecimento corporativas e prompts de sistema) precisam colaborar, compartilhar recursos diretamente ou expor instruções inteiras de sistema cria graves problemas de segurança, acoplamento e vazamento de informações.

### Soluções Introduzidas:
- **Descoberta Dinâmica de Capacidades:** Agentes anunciam o que sabem fazer de forma padronizada.
- **Isolamento de Memória & Contexto:** O agente especialista nunca acessa os segredos do agente coordenador.
- **Delegação Assíncrona de Tarefas:** Tarefas complexas são fatiadas, rastreadas e agregadas via canais de mensagens assíncronos.
- **Garantia de Estado Comum:** Transição de estados de ciclo de vida de tarefas rigorosamente auditada.

---

## 🏗️ Arquitetura e Tecnologias

A arquitetura do projeto simula um ecossistema de microsserviços onde cada agente roda em seu próprio container e expõe uma API REST em conformidade com as regras do protocolo A2A:

```mermaid
graph TB

    subgraph Client_Layer["Client Layer"]
        User(["Usuário / Integração Externa"])
    end

    subgraph Coordinator_Service["Coordenador Agent Service (Port 8000)"]
        Endpoints_Coord["A2A Endpoints (Coordenador)"]
        Coord_Logic["Coordination Engine (Fatiamento de Tarefas)"]
    end

    subgraph Analyst_Service["Analista Agent Service (Port 8001)"]
        Endpoints_Analyst["A2A Endpoints (Analista)"]
        Analyst_Logic["Code Analysis Agent (Gemini/Ollama)"]
    end

    subgraph Auditor_Service["Auditor Agent Service (Port 8002)"]
        Endpoints_Auditor["A2A Endpoints (Auditor)"]
        Auditor_Logic["Security Auditing Agent (Gemini/Ollama)"]
    end

    subgraph Storage_Layer["Storage & Message Layer"]
        Redis[("Redis - Fila de Mensagens / Cache de Estados")]
    end

    %% Fluxo de Trabalho
    User -->|Submete Tarefa Complexa| Endpoints_Coord
    Coord_Logic -->|1. Handshake & Capabilities| Endpoints_Analyst
    Coord_Logic -->|2. Handshake & Capabilities| Endpoints_Auditor
    
    Coord_Logic -->|3. Delegar Análise (Task Payload)| Endpoints_Analyst
    Coord_Logic -->|4. Delegar Auditoria (Task Payload)| Endpoints_Auditor

    Analyst_Logic -->|Retorna Resultados Analíticos| Endpoints_Coord
    Auditor_Logic -->|Retorna Relatório de Segurança| Endpoints_Coord
    
    Coord_Logic -->|Grava Estados de Tarefas| Redis
    Coord_Logic -->|Consolida Relatório Final| User
```

### Tecnologias Utilizadas:
*   **FastAPI / Python 3.12:** Para endpoints de alta performance e manipulação assíncrona.
*   **a2a-python (Linux Foundation SDK):** Biblioteca oficial para manipulação de envelopes, payloads e handshakes A2A.
*   **Redis:** Armazenamento central de transições de estados de tarefas distribuídas e filas de jobs.
*   **Docker & Docker Compose:** Encapsulamento completo de cada microsserviço de agente.

---

## 📁 Estrutura do Repositório

```text
llm-a2a-protocol/
├── app/
│   ├── __init__.py
│   ├── config.py             # Configurações globais e chaves
│   ├── main.py               # Ponto de entrada FastAPI (Coordenador/Multi-mode)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py           # Abstração de agente A2A
│   │   ├── coordinator.py    # Lógica de fatiamento e agregação de tarefas
│   │   ├── analyst.py        # Agente especialista em análise de código
│   │   └── auditor.py        # Agente especialista em auditoria de segurança
│   ├── protocol/
│   │   ├── __init__.py
│   │   ├── handshake.py      # Lógica de handshakes e contratos
│   │   ├── capabilities.py   # Registro e validação de capacidades do protocolo
│   │   └── tasks.py          # Gerenciamento de tarefas (Tasks, Status, Results)
│   └── database/
│       ├── __init__.py
│       └── redis_client.py   # Conexão com o Redis
├── tests/
│   ├── __init__.py
│   ├── test_handshake.py     # Testes de handshake e conexão
│   ├── test_capabilities.py  # Testes de schemas de capacidades
│   └── test_tasks.py         # Testes de fluxos de delegação de tarefas
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml            # Dependências e metadados (Poetry)
└── README.md
```

---

## 🚀 O Protocolo A2A

O protocolo Agent-to-Agent segue três etapas fundamentais de comunicação de ponta a ponta:

### 1. Descoberta & Handshake
O agente de origem faz uma requisição HTTP de handshake enviando suas próprias credenciais e solicita as capacidades do receptor. O receptor valida o contrato e retorna o objeto `Capabilities` que lista o que ele pode realizar e quais esquemas de JSON de entrada ele aceita.

### 2. Criação de Tarefa (Task Creation)
O remetente envia um payload correspondente à capacidade solicitada. O receptor valida as restrições, cria um `Task ID` único no Redis com status `PENDING`, e retorna imediatamente o ID de rastreamento de forma assíncrona.

### 3. Execução & Retorno (Poll/Callback)
Enquanto o receptor processa a tarefa em segundo plano, o remetente pode monitorar o estado (`PENDING` -> `RUNNING` -> `COMPLETED`) via chamadas HTTP GET ou aguardar uma notificação de Webhook de retorno de chamada (`Callback URL`) contendo o payload de resultado estruturado.

---

## 🛠️ Instalação e Setup

### Pré-requisitos
*   Docker e Docker Compose instalados.
*   Python 3.12+ (caso queira rodar localmente).

### Rodando o Ambiente Isolado (Docker Compose)
Para iniciar os três microsserviços de agentes (Coordenador, Analista, Auditor) e a infraestrutura de suporte (Redis):

```bash
docker compose up --build
```

Os serviços subirão nos seguintes endereços locais:
*   **Coordenador Agent API:** `http://localhost:8000`
*   **Analista Agent API:** `http://localhost:8001`
*   **Auditor Agent API:** `http://localhost:8002`

---

## 🧪 Como Usar (Endpoints)

### 1. Obter Capacidades de um Agente
```bash
curl -X GET http://localhost:8001/a2a/capabilities
```

### 2. Iniciar Tarefa Coordenada
Submeta uma tarefa complexa de análise de código para o Coordenador. Ele irá orquestrar o processo delegando para os especialistas remotamente:
```bash
curl -X POST http://localhost:8000/a2a/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "full_code_review",
    "payload": {
      "repository_url": "https://github.com/example/project",
      "branch": "main"
    }
  }'
```

---

## ✅ Testes e Coverage

O projeto segue as mais rígidas exigências de engenharia de software com cobertura de testes unitários superior a **85%**.

Para rodar os testes unitários localmente:
```bash
poetry run pytest --cov=app tests/
```
