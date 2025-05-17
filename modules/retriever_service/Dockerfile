FROM python:3.11-slim

WORKDIR /app

# Set Hugging Face Home for model caching within the image/container
ENV HF_HOME=/app/.cache/huggingface
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Model Pre-downloading and Pre-warming ---
# This ENV var will be used by the prewarm script
ARG EMBEDDING_MODEL_ARG="sentence-transformers/all-MiniLM-L6-v2"
ENV EMBEDDING_MODEL=${EMBEDDING_MODEL_ARG}
ENV PAYLOAD_TEXT_FIELD_NAME="document"

# Create a more comprehensive pre-warming script that will:
# 1. Download the model files
# 2. Force load the model into memory to test it works
# 3. Create model embeddings for some sample text
# This runs at IMAGE BUILD TIME
RUN python -c "\
import os; \
import time; \
from fastembed.embedding import DefaultEmbedding; \
model_name = os.getenv('EMBEDDING_MODEL'); \
print(f'Build-time: Ensuring model {model_name} files are downloaded to {os.getenv(\"HF_HOME\")} via fastembed...'); \
start_time = time.time(); \
embedding_model = DefaultEmbedding(model_name=model_name); \
print(f'Build-time: Model {model_name} object created in {time.time() - start_time:.2f} seconds.'); \
# Actually generate embeddings to verify model works and warm it up fully \
sample_sentences = [ \
    'This is a sample sentence to test embedding generation.', \
    'Another sentence to ensure the model is properly loaded.', \
    'I want to make sure everything works correctly.' \
]; \
print('Build-time: Generating test embeddings to fully load model...'); \
start_time = time.time(); \
embeddings = list(embedding_model.embed(sample_sentences)); \
duration = time.time() - start_time; \
print(f'Build-time: Generated {len(embeddings)} embeddings in {duration:.2f} seconds'); \
print(f'Build-time: First embedding shape: {embeddings[0].shape}'); \
print(f'Build-time: Model {model_name} is fully tested and cached!'); \
"
# Note: Model cache files will persist in the image, but model RAM state won't
# be preserved. However, having the files cached will make startup much faster.

# Copy the service code
COPY ./main.py .
# Add other files from modules/retriever_service if any (e.g., .env if used differently)

# Expose the port the service runs on
EXPOSE 8000

# Command to run the service (QDRANT_HOST_FOR_SERVICE will be set at `docker run` time)
# EMBEDDING_MODEL and PAYLOAD_TEXT_FIELD_NAME are already set via ENV
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--lifespan", "on"]
