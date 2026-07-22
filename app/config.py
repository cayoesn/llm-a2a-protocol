import os

class Settings:
    PROJECT_NAME: str = "llm-a2a-protocol"
    AGENT_ROLE: str = os.getenv("AGENT_ROLE", "coordinator")  # coordinator, analyst, auditor
    
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # URLs de comunicação interna de agentes (usadas pelo coordenador)
    ANALYST_AGENT_URL: str = os.getenv("ANALYST_AGENT_URL", "http://localhost:8001")
    AUDITOR_AGENT_URL: str = os.getenv("AUDITOR_AGENT_URL", "http://localhost:8002")

    # Observabilidade Langfuse
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-demo")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-demo")
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

settings = Settings()

