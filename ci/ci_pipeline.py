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
        image_name = f"docker.io/{dockerhub_username}/smartagent-x7:latest"
        await container.publish(image_name)
        
        print(f"Image published: {image_name}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
