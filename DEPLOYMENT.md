# FastAPI Dagger Cloud Deployment Guide

## Prerequisites
- Docker Hub account
- Dagger Cloud account
- GitHub repository (for CI/CD)

## 1. Docker Hub Access Token
- Go to [Docker Hub Security Settings](https://hub.docker.com/settings/security)
- Click **New Access Token**
- Name it (e.g., `dagger-pipeline`)
- **Select `Read & Write` permissions**
- Copy the token (you will not see it again!)

## 2. .env File Setup
Create a `.env` file in your project root:

```
DOCKERHUB_USERNAME=your-dockerhub-username
DOCKERHUB_TOKEN=your-dockerhub-access-token
DAGGER_CLOUD_TOKEN=your-dagger-cloud-token
OPENAI_API_KEY=your-openai-key
LLM_MODEL=gpt-4o
```

- The Docker Hub token **must** have `Read & Write` permissions.
- The repository (e.g., `dancoman/fastapi-demo`) must exist on Docker Hub.

## 3. Running the Pipeline in Docker

```sh
docker run --rm \
  -v ${PWD}:/app \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -w /app \
  --env-file .env \
  python:3.11-slim \
  sh -c "apt-get update && \
         apt-get install -y docker.io && \
         pip install dagger-io python-dotenv && \
         python ci/dagger_pipeline.py"
```

## 4. What Happens
- The pipeline builds your Docker image using your Dockerfile
- Authenticates to Docker Hub using your username and access token
- Pushes the image to your Docker Hub repository
- You can monitor the build in [Dagger Cloud](https://dagger.cloud)

## 5. Troubleshooting
- **401 Unauthorized:**
  - Ensure your Docker Hub token has `Read & Write` permissions
  - Ensure the repository exists on Docker Hub
  - Ensure your `.env` file is correct and passed to Docker
- **docker login works but pipeline fails:**
  - Double-check the token permissions and repository existence

---

For more, see the comments in `ci/dagger_pipeline.py` and your workflow YAML.
