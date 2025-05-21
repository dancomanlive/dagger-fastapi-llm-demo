FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies including Docker CLI and curl
RUN apt-get update && \
    apt-get install -y \
        gcc \
        python3-dev \
        build-essential \
        ca-certificates \
        curl \
        gnupg \
        lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli docker-buildx-plugin docker-compose-plugin && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your FastAPI app
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV DOCKER_HOST=unix:///var/run/docker.sock

# Expose port for FastAPI
EXPOSE 8000

# Run the RAG app using the containerized approach
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
