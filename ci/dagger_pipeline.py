import sys
import dagger
import os
from dotenv import load_dotenv

async def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get Docker Hub credentials from environment
    dockerhub_username = os.environ.get('DOCKERHUB_USERNAME')
    dockerhub_token = os.environ.get('DOCKERHUB_TOKEN')
    
    if not dockerhub_username or not dockerhub_token:
        raise ValueError("DOCKERHUB_USERNAME and DOCKERHUB_TOKEN environment variables are required in .env file")

    config = dagger.Config(log_output=sys.stdout)
    
    async with dagger.Connection(config) as client:
        # Get build context directory
        context_dir = client.host().directory(".")
        
        # Set up Docker authentication (token as password)
        secret_token = client.set_secret("dockerhub_token", dockerhub_token)
        container = (
            client.container()
            .with_registry_auth("docker.io", dockerhub_username, secret_token)
            .build(context=context_dir)
        )

        # Push to Docker Hub
        image_ref = f"docker.io/{dockerhub_username}/fastapi-demo:latest"
        image = await container.publish(image_ref)
        print(f"Published image: {image}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
