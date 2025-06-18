FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model at build time
ARG EMBEDDING_MODEL_ARG="BAAI/bge-small-en-v1.5"
ENV EMBEDDING_MODEL=${EMBEDDING_MODEL_ARG}

RUN python -c "from fastembed.embedding import DefaultEmbedding; DefaultEmbedding(model_name='${EMBEDDING_MODEL_ARG}')"

# Copy the service code
COPY . .

# Command to run the Temporal worker
CMD ["python", "worker.py"]
