import sys
import dagger
import os

async def main():
    
    # Get Docker Hub credentials from environment
    dockerhub_username = os.environ.get('DOCKERHUB_USERNAME')
    dockerhub_token = os.environ.get('DOCKERHUB_TOKEN')
    
    if not dockerhub_username or not dockerhub_token:
        raise ValueError("DOCKERHUB_USERNAME and DOCKERHUB_TOKEN environment variables are required in .env file")

    config = dagger.Config(log_output=sys.stdout)

    SERVICES = [
        "embedding_service",
        "retriever_service",
        "fastapi_service",
        "gradio_service",
        "temporal_service",
    ]

    # Use git commit hash as the image version
    import subprocess
    try:
        version = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').strip()
    except Exception:
        version = 'latest'

    async with dagger.Connection(config) as client:
        # Set up Docker authentication (token as password)
        secret_token = client.set_secret("dockerhub_token", dockerhub_token)

        for service in SERVICES:
            service_dir = f"./services/{service}"
            dockerfile_path = f"{service_dir}/Dockerfile"
            context_dir = client.host().directory(service_dir)
            image_name = f"docker.io/{dockerhub_username}/smartagent-x7-{service}:{version}"

            print(f"Building and publishing {image_name}...")

            container = (
                client.container()
                .with_registry_auth("docker.io", dockerhub_username, secret_token)
                .build(context=context_dir, dockerfile=dockerfile_path)
            )

            await container.publish(image_name)
            print(f"Image published: {image_name}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
