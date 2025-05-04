import sys
import dagger

async def main():
    config = dagger.Config(log_output=sys.stdout)
    
    async with dagger.Connection(config) as client:
        # Build using Dockerfile
        container = (
            client.container()
            .build(context=".")
        )

        # Push to Docker Hub
        # The format is: docker.io/<username>/<repository>:<tag>
        image_ref = f"docker.io/${{{{ secrets.DOCKERHUB_USERNAME }}}}/fastapi-demo:latest"
        image = await container.publish(image_ref)
        print(f"Published image: {image}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
