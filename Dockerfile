FROM nvcr.io/nvidia/pytorch:23.10-py3

# Configura variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Diretório de trabalho
WORKDIR /app

# Instala dependências diretamente
RUN pip install --no-cache-dir \
    "numpy==1.24.4" \
    fastapi==0.110.0 \
    uvicorn[standard]==0.29.0 \
    transformers==4.40.0 \
    scipy==1.13.0 \
    python-multipart==0.0.9 \
    requests==2.31.0

# Copia o código da aplicação
COPY . .


# Porta exposta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]