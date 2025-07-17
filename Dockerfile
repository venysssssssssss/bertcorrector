# Estágio de construção
FROM python:3.10-slim as builder

# 1. Instala dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    git \
    libopenblas-dev \
    gfortran \
    libhdf5-dev \
    libxml2-dev \
    libxslt-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Instala o Poetry corretamente
RUN pip install --no-cache-dir poetry

# 3. Configura ambiente
ENV POETRY_VIRTUALENVS_CREATE=false \
    PATH="/root/.local/bin:$PATH"

# 4. Diretório de trabalho
WORKDIR /app

# 5. Copia APENAS os arquivos de dependências
COPY pyproject.toml .

# 6. Instala dependências sem lockfile
RUN poetry install --no-interaction --no-ansi --only main

# Estágio final
FROM nvcr.io/nvidia/pytorch:23.10-py3

# 1. Configura ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 2. Copia dependências instaladas
COPY --from=builder /root/.cache/pypoetry/virtualenvs /root/.cache/pypoetry/virtualenvs
COPY --from=builder /root/.local /root/.local
ENV PATH="/root/.local/bin:$PATH"

# 3. Diretório de trabalho
WORKDIR /app

# 4. Copia aplicação
COPY ./app ./app

# 5. Porta exposta
EXPOSE 8000

# 6. Comando de inicialização
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]