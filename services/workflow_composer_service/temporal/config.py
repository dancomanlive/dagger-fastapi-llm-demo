"""
Temporal configuration and client setup for workflow composer service.
This service connects to the temporal_service as a client.
"""
import os
from temporalio.client import Client

# Temporal connection configuration (connects to temporal_service)
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")

# This service's task queue for its activities
WORKFLOW_COMPOSER_TASK_QUEUE = os.getenv("WORKFLOW_COMPOSER_TASK_QUEUE", "workflow-composer-queue")

# Create Temporal client to connect to temporal_service
async def get_temporal_client() -> Client:
    """Get a Temporal client instance connected to temporal_service."""
    return await Client.connect(
        TEMPORAL_HOST,
        namespace=TEMPORAL_NAMESPACE,
    )

# Configuration for this service's workflows and activities
SERVICE_CONFIG = {
    "task_queue": WORKFLOW_COMPOSER_TASK_QUEUE,
    "execution_timeout": "10m",
    "task_timeout": "1m",
    "service_name": "workflow_composer_service"
}
