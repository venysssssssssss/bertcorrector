# Estágio de construção
FROM python:3.10-slim as builder

# Instala dependências do sistema necessárias
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libopenblas-dev \
    gfortran \
    libhdf5-dev \
    libxml2-dev \
    libxslt-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala o Poetry
RUN pip install --no-cache-dir "poetry==1.8.2"

# Configura o ambiente do Poetry
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PATH="$POETRY_HOME/bin:$PATH"

# Diretório de trabalho
WORKDIR /app

# Copia os arquivos de dependências
COPY pyproject.toml poetry.lock ./

# Instala dependências
RUN poetry install --no-interaction --no-ansi --only main --no-root

# Estágio final
FROM nvcr.io/nvidia/pytorch:23.10-py3

# Configura variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copia as dependências instaladas
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Diretório de trabalho
WORKDIR /app

# Copia o código da aplicação
COPY ./app ./app

# Porta exposta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]