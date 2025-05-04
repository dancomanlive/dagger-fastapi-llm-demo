Here’s the complete updated README in a single text block:

# 🧠 Dagger(Cloud) + FastAPI + OpenAI Chat API

This project is a minimal demo of an AI-powered API using FastAPI, Dagger, and OpenAI. The API runs entirely in Docker and exposes a simple chat endpoint that leverages OpenAI language models.

## 🚀 Features

- Docker-first deployment
- Integration with OpenAI models (GPT-4, GPT-3.5, etc.)
- Secure API key and token management via `.env`
- Lightweight FastAPI backend to send prompts and receive completions
- 🔗 **Integrated with Dagger Cloud** for observability, sharing, and secure agentic workflows

---

## 🛠️ Setup & Usage

### 1. Clone the repository

```bash
git clone https://github.com/your-username/dagger-fastapi-llm-demo.git
cd dagger-fastapi-llm-demo

2. Create a .env file in the project root

# .env
OPENAI_API_KEY=your_openai_api_key_here
DAGGER_CLOUD_TOKEN=your_dagger_cloud_token_here  # 🔐 Required for Dagger Cloud
# Optional:
# OPENAI_MODEL=gpt-4o
# OPENAI_BASE_URL=https://api.openai.com/v1/

The .env file is automatically loaded and is ignored by Git.

⸻

3. Start the API using Docker

docker-compose up -d

The API will now be available at:

http://localhost:8000



⸻

📡 API Usage

POST /chat

Send a prompt to the model and get a response.

Example Request:

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of Malaysia?"}'

Example Response:

{
  "response": "The capital of Malaysia is Kuala Lumpur."
}

You can optionally pass a specific model:

{
  "prompt": "Hello!",
  "model": "gpt-4"
}



⸻

🔒 Security Notes
	•	.env is in .gitignore; never commit your secrets.
	•	Store sensitive credentials like OPENAI_API_KEY and DAGGER_CLOUD_TOKEN in environment variables or .env.
	•	Dagger secures secret values and prevents them from leaking in logs or layers.

⸻

☁️ Dagger Cloud Integration

This project integrates with Dagger Cloud to enable:
	•	Run insights and logs directly in the cloud
	•	Collaborate on workflows and infrastructure
	•	Secure secret management and CI/CD observability

To enable:
	1.	Create a Dagger Cloud token
	2.	Add it to your .env file as DAGGER_CLOUD_TOKEN
	3.	Run docker-compose up — Dagger will connect to the cloud automatically

⸻

🧩 Tech Stack
	•	FastAPI – for serving the API
	•	Dagger – for managing containerized workflows
	•	Dagger Cloud – for observability and secure CI/CD
	•	Docker – for local and production consistency
	•	OpenAI – LLM backend
