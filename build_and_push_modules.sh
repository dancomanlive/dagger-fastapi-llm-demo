#!/bin/bash

# How to use this script:
# bash build_and_push_modules.sh v1.0.0 myusername

VERSION=$1
DOCKERHUB_USERNAME=$2

if [ -z "$VERSION" ] || [ -z "$DOCKERHUB_USERNAME" ]; then
    echo "Usage: $0 <version> <dockerhub-username>"
    exit 1
fi

# Load the DOCKERHUB_TOKEN from the .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$DOCKERHUB_TOKEN" ]; then
    echo "DOCKERHUB_TOKEN is not set. Please add it to the .env file."
    exit 1
fi

# Check if already logged in
if ! docker info | grep -q "Username: ${DOCKERHUB_USERNAME}"; then
    echo "Logging in to Docker Hub using token..."
    echo "$DOCKERHUB_TOKEN" | docker login -u "${DOCKERHUB_USERNAME}" --password-stdin
    if [ $? -ne 0 ]; then
        echo "Docker login failed. Exiting."
        exit 1
    fi
else
    echo "Already logged in as ${DOCKERHUB_USERNAME}"
fi

# Iterate over all subdirectories in the modules folder
for MODULE_DIR in ./modules/*; do
    if [ -d "$MODULE_DIR" ]; then
        MODULE_NAME=$(basename "$MODULE_DIR")
        echo "Building and pushing module: $MODULE_NAME"

        # Ensure images are always built, even if they already exist
        echo "Building module: $MODULE_NAME"

        # Check if the image already exists on Docker Hub
        IMAGE_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" https://hub.docker.com/v2/repositories/${DOCKERHUB_USERNAME}/${MODULE_NAME}/tags/${VERSION}/)

        while [ "$IMAGE_EXISTS" -eq 200 ]; do
            echo "Image ${MODULE_NAME}:${VERSION} already exists. Incrementing version..."
            VERSION=$(echo $VERSION | awk -F. -v OFS=. '{$NF++; print}')
            IMAGE_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" https://hub.docker.com/v2/repositories/${DOCKERHUB_USERNAME}/${MODULE_NAME}/tags/${VERSION}/)
        done

        # Use the same version for all modules
        TAG="$VERSION"
        echo "Using tag ${TAG} for module ${MODULE_NAME}"

        # Build the image without checking for existing images
        # docker build --no-cache -t ${MODULE_NAME}:${VERSION} "$MODULE_DIR"

        # Uncomment the following line if you want to rebuild the image
        # Force rebuild for the retrieve module
        if [ "$MODULE_NAME" = "retrieve" ]; then
            echo "Forcing rebuild for retrieve module"
            docker build --no-cache -t ${MODULE_NAME}:${TAG} "$MODULE_DIR"
        else
            docker build -t ${MODULE_NAME}:${TAG} "$MODULE_DIR"
        fi

        # Tag the image for Docker Hub
        docker tag ${MODULE_NAME}:${VERSION} ${DOCKERHUB_USERNAME}/${MODULE_NAME}:${TAG}

        # Push the image to Docker Hub
        docker push ${DOCKERHUB_USERNAME}/${MODULE_NAME}:${TAG}

        if [ $? -ne 0 ]; then
            echo "Failed to build or push $MODULE_NAME. Exiting."
            exit 1
        fi
    fi
done

echo "All modules built and pushed successfully!"