# FastAPI Dagger Cloud Deployment Guide

This guide walks you through building a Docker image for your FastAPI app and pushing it to Docker Hub using a Dagger pipeline, with monitoring in Dagger Cloud. Let's make deployment simple, automated, and reliable!

---

## Why Build and Push a Docker Image to Docker Hub?

Creating a Docker image and uploading it to Docker Hub offers several benefits:

- **Portability & Consistency**

  - Your app, with all its dependencies, is packaged into a single image.

  - It runs the same way everywhere---locally, on a teammate's machine, or in the cloud.

- **Cloud-Ready**

  - Platforms like AWS ECS, Google Cloud Run, and DigitalOcean can pull your image directly from Docker Hub.

  - No need to send code or setup instructions---just point to your image.

- **CI/CD Automation**

  - Automate building and publishing your app with every code change.

  - Always have a fresh, ready-to-deploy image.

- **Versioning & Rollbacks**

  - Tag images (e.g., `v1.0.0`, `latest`) to track versions or revert to older ones if needed.

- **Team Collaboration**

  - Share the same image with your team for testing or deployment.

**In Short:** This pipeline creates a Docker image, pushes it to Docker Hub, and sets you up for fast, repeatable cloud deployments.

---

## Prerequisites

Before you start, ensure you have:

- A [Docker Hub account](https://hub.docker.com/signup) (to store your images).

- A [Dagger Cloud account](https://dagger.io/cloud) (to monitor your pipeline).

- A GitHub repository (for CI/CD automation).

---

## Step 1: Create a Docker Hub Access Token

You'll need a token to let the pipeline push images to Docker Hub.

1\. Log in to [Docker Hub](https://hub.docker.com).

2\. Go to **Settings** → **Security** (or [this link](https://hub.docker.com/settings/security)).

3\. Click **New Access Token**.

4\. Give it a name (e.g., `dagger-pipeline`).

5\. Choose **Read & Write** permissions (required to push images).

6\. Click **Generate**, then **copy the token immediately**.

   - **Warning:** You won't see it again, so save it somewhere safe (e.g., a password manager).

---

## Step 2: Set Up Environment Variables

The pipeline needs credentials for Docker Hub and Dagger Cloud. You'll set these up differently depending on whether you're running it **locally** or via **GitHub Actions**.

### Option A: Local Testing (Using a `.env` File)

For running the pipeline manually on your machine:

1\. Create a file named `.env` in your project's root directory.

2\. Add these lines, replacing the placeholders with your values:

   ```

   DOCKERHUB_USERNAME=your-dockerhub-username

   DOCKERHUB_TOKEN=your-access-token-from-step-1

   DAGGER_CLOUD_TOKEN=your-dagger-cloud-token

   OPENAI_API_KEY=your-openai-key (optional)

   LLM_MODEL=gpt-4o (optional)

   ```

3\. Save the file.

- **Notes:**

  - The `DOCKERHUB_TOKEN` must have **Read & Write** permissions.

  - Your Docker Hub repository (e.g., `username/fastapi-demo`) must already exist---create it on Docker Hub if it doesn't.

  - **Keep this file secure:** Don't commit it to Git (add `.env` to your `.gitignore`).

**When to Use:** Testing or running the pipeline locally with Docker.

---

### Option B: GitHub Actions (Using Repository Secrets)

For automated CI/CD runs on GitHub:

1\. Go to your GitHub repository.

2\. Navigate to **Settings** → **Secrets and variables** → **Actions**.

3\. Add these secrets by clicking **New repository secret** for each:

   - `DOCKERHUB_USERNAME`: Your Docker Hub username.

   - `DOCKERHUB_TOKEN`: Your access token from Step 1.

   - `DAGGER_CLOUD_TOKEN`: Your Dagger Cloud token.

   - `OPENAI_API_KEY`: Your OpenAI key (if used).

   - `LLM_MODEL`: Model name, e.g., `gpt-4o` (if used).

4\. Update your GitHub Actions workflow file (e.g., `.github/workflows/deploy.yml`) to use these secrets:

   ```yaml

   name: Deploy FastAPI App

   on: [push]

   jobs:

     build-and-push:

       runs-on: ubuntu-latest

       steps:

         - name: Checkout code

           uses: actions/checkout@v3

         - name: Run Dagger Pipeline

           env:

             DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}

             DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}

             DAGGER_CLOUD_TOKEN: ${{ secrets.DAGGER_CLOUD_TOKEN }}

             OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

             LLM_MODEL: ${{ secrets.LLM_MODEL }}

           run: |

             docker run --rm

               -v ${PWD}:/app

               -v /var/run/docker.sock:/var/run/docker.sock

               -w /app

               -e DOCKERHUB_USERNAME

               -e DOCKERHUB_TOKEN

               -e DOCKERHUB_TOKEN

               -e DAGGER_CLOUD_TOKEN

               -e OPENAI_API_KEY

               -e LLM_MODEL

               python:3.11-slim

               sh -c "apt-get update && apt-get install -y docker.io && pip install dagger-io python-dotenv && python ci/dagger_pipeline.py"

   ```

**When to Use:** Automating the pipeline on GitHub with every commit or pull request.

---

## Step 3: Run the Pipeline Locally (Optional)

To test the pipeline on your machine using Docker:

1\. Open a terminal in your project directory (where your `.env` file and `Dockerfile` are).

2\. Run this command:

   ```bash

   docker run --rm

     -v ${PWD}:/app

     -v /var/run/docker.sock:/var/run/docker.sock

     -w /app

     --env-file .env

     python:3.11-slim

     sh -c "apt-get update && apt-get install -y docker.io && pip install dagger-io python-dotenv && python ci/dagger_pipeline.py"

   ```

### What This Does:

- Uses your `.env` file for credentials.

- Builds your FastAPI app into a Docker image (based on your `Dockerfile`).

- Pushes the image to Docker Hub.

- Lets Dagger Cloud track the process.

**Requirements:** Docker must be installed and running on your machine.

---

## Step 4: What the Pipeline Does

When you run it (locally or via GitHub Actions):

1\. **Builds the Image:** Uses your `Dockerfile` to package your FastAPI app.

2\. **Logs into Docker Hub:** Authenticates with your username and token.

3\. **Pushes the Image:** Uploads it to your Docker Hub repository (e.g., `username/fastapi-demo`).

4\. **Monitors in Dagger Cloud:** Tracks the pipeline's progress at [dagger.cloud](https://dagger.cloud).

---

## Next Steps

Once your image is on Docker Hub:

- **Deploy it:** Use a cloud service like AWS ECS, Google Cloud Run, or DigitalOcean.

- **Automate Deployment:** Add a deployment step to your GitHub Actions workflow.

- **Monitor:** Check pipeline runs and performance in [Dagger Cloud](https://dagger.cloud).