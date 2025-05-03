🧠 Dagger + FastAPI + OpenAI Chat API

This project is a minimal demo of an AI-powered API using FastAPI, Dagger, and OpenAI. The API runs entirely in Docker and exposes a simple chat endpoint that leverages OpenAI language models.

⸻

🚀 Features
	•	✅ Docker-first deployment
	•	✅ Built-in integration with OpenAI models (GPT-4, GPT-3.5, etc.)
	•	✅ Secure handling of API keys via .env or environment variables
	•	✅ Lightweight FastAPI backend for sending prompts and receiving completions

⸻

🛠️ Setup & Usage

1. Clone the repository

git clone https://github.com/your-username/dagger-fastapi-llm-demo.git
cd dagger-fastapi-llm-demo

2. Create a .env file in the project root

# .env
OPENAI_API_KEY=your_openai_api_key_here
# Optional:
# LLM_MODEL=gpt-4o

✅ The .env file is automatically used by Docker and ignored by git.

3. Start the API using Docker

docker-compose up -d

This will start the FastAPI server inside a container. Once running, the API will be available at:

http://localhost:8000



⸻

📡 API Usage

🔹 Endpoint

POST /chat

Send a prompt to the model and receive an AI-generated response.

Request

POST http://localhost:8000/chat
Content-Type: application/json

{
  "prompt": "What is the capital of Malaysia?"
}

Response

{
  "response": "The capital of Malaysia is Kuala Lumpur."
}

📝 You can also optionally include a model field in the request body to override the default (e.g., "model": "gpt-4").

⸻

🔒 Security Notes
	•	Secrets like OPENAI_API_KEY should only be stored in .env or as environment variables.
	•	The .env file is ignored by git to prevent accidental leaks.
	•	Dagger ensures secrets are not exposed in logs or containers.

For more, see the Dagger Security Docs.

⸻

🧩 Tech Stack
	•	FastAPI – Web API framework
	•	Dagger – Secure containerized DevOps
	•	Docker – Container-based environment
	•	OpenAI API – Language model backend

⸻

🧪 Quick Test (No code)

Run this in your terminal to test the chat API:

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of Malaysia?"
}'



⸻

Let me know if you want a diagram of the architecture or Docker setup!