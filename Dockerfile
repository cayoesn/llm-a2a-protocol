FROM python:3.12-slim

WORKDIR /app

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos de definição de dependência
COPY pyproject.toml ./

# Copia o código da aplicação
COPY app/ ./app/

# Instala dependências via pip localmente
RUN pip install --no-cache-dir fastapi uvicorn pydantic redis httpx

# Porta padrão exposta pelo container
EXPOSE 8000

# Comando padrão de inicialização (pode ser sobrescrito)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
