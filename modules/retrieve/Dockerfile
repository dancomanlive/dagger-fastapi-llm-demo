FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Add Python buffers optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy only the requirements file first to leverage Docker's layer caching
COPY requirements.txt .

# Install dependencies with pip optimization
RUN pip install --no-cache-dir -r requirements.txt

# Make cache directory with proper permissions
RUN mkdir -p /app/.cache/torch/sentence_transformers
RUN chmod -R 777 /app/.cache

# Set the cache location for HuggingFace
ENV TRANSFORMERS_CACHE="/app/.cache/torch"
ENV HF_HOME="/app/.cache"

# Pre-download and save the model to prevent downloads at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2'); model.save('/app/model')"

# Copy the rest of the application code
COPY . .

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Run the module
ENTRYPOINT ["python", "main.py"]
