FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create config directory if it doesn't exist
RUN mkdir -p config/workflows

# Expose port for the API
EXPOSE 8000

# Command to run the service
CMD ["python", "main.py"]
