FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        gcc \
        python3-dev \
        build-essential \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Environment variables for Docker service communication
ENV FASTAPI_SERVICE_URL=http://fastapi:8000
ENV RETRIEVER_SERVICE_URL=http://retriever-service:8000

# Expose port for Gradio
EXPOSE 7860

# Run the Gradio app with new entry point
CMD ["python", "app.py"]
