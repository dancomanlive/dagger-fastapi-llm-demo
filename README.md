# 🧠 Dagger + FastAPI + OpenAI Chat API

This project is a minimal demo of an AI-powered API using FastAPI, Dagger, and OpenAI. The API runs entirely in Docker and exposes a simple chat endpoint that leverages OpenAI language models.

## 🚀 Features

- Docker-first deployment
- Integration with OpenAI models (GPT-4, GPT-3.5, etc.)
- Secure API key management via .env or environment variables
- Lightweight FastAPI backend to send prompts and receive completions

## 🛠️ Setup & Usage

### 1. Clone the repository

    git clone https://github.com/your-username/dagger-fastapi-llm-demo.git
    cd dagger-fastapi-llm-demo

### 2. Create a .env file in the project root

    # .env
    OPENAI_API_KEY=your_openai_api_key_here
    # Optional:
    # OPENAI_MODEL=gpt-4o
    # OPENAI_BASE_URL=https://api.openai.com/v1/

(The .env file is automatically loaded by Docker and is ignored by Git.)

### 3. Start the API using Docker

    docker-compose up -d

The API will now be available at:

    http://localhost:8000

## 📡 API Usage

### POST /chat

Send a prompt to the model and get a response.

#### Example Request:

    curl -X POST http://localhost:8000/chat \
      -H "Content-Type: application/json" \
      -d '{
        "prompt": "What is the capital of Malaysia?"
      }'

#### Example Response:

    {
      "response": "The capital of Malaysia is Kuala Lumpur."
    }

You can optionally pass a specific model in the request:

    {
      "prompt": "Hello!",
      "model": "gpt-4"
    }

## 🔒 Security Notes

- Do not commit your `.env` file. It's already listed in `.gitignore`.
- Store secrets only in `.env` or secure environment variables.
- Dagger ensures secrets are never exposed in logs or Docker layer history.

Learn more at: https://docs.dagger.io/features/security

## 🧩 Tech Stack

- FastAPI – for serving the API
- Dagger – for managing containerized workflows and secret injection
- Docker – for consistent local and production environments
- OpenAI – the language model backend