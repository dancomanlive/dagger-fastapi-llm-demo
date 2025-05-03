FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install necessary packages for Dagger
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy your FastAPI app
COPY . .

# Set environment variables for Dagger Engine connection
ENV DAGGER_HOST=unix:///run/dagger/engine.sock
ENV _EXPERIMENTAL_DAGGER_RUNNER_HOST=unix:///run/dagger/engine.sock

# .env file will be used automatically for LLM API keys
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]