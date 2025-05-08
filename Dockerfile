FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc python3-dev build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, and wheel
RUN python3 -m pip install --upgrade pip setuptools wheel

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your FastAPI app
COPY . .

# Set environment variables for Dagger Engine connection
ENV DAGGER_HOST=unix:///run/dagger/engine.sock
ENV _EXPERIMENTAL_DAGGER_RUNNER_HOST=unix:///run/dagger/engine.sock
ENV PYTHONPATH=/app

# .env file will be used automatically for LLM API keys
EXPOSE 8000

# Run FastAPI app with the new Superlinked integrated version
CMD ["uvicorn", "main_superlinked_integrated:app", "--host", "0.0.0.0", "--port", "8000"]
