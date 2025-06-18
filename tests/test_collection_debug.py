#!/usr/bin/env python3
"""Test script to debug collection name passing to Temporal workflow"""

import asyncio
import time
from temporalio.client import Client


async def test_workflow():
    """Test calling the workflow directly with collection name"""
    
    # Connect to Temporal
    client = await Client.connect("localhost:7233", namespace="default")
    print(f"Connected to Temporal")
    
    # Test data - this simulates what Gradio sends
    workflow_args = [
        "document_retrieval", 
        {
            "query": "What is artificial intelligence?", 
            "top_k": 5, 
            "collection": "test-document-chunks"
        }
    ]
    
    print(f"Starting workflow with args: {workflow_args}")
    
    # Start workflow
    workflow_handle = await client.start_workflow(
        "GenericPipelineWorkflow",
        args=workflow_args,
        id=f"debug-test-{int(time.time() * 1000)}",
        task_queue="document-processing-queue"
    )
    
    print(f"Workflow started, waiting for result...")
    result = await workflow_handle.result()
    
    print(f"Result: {result}")
    return result


if __name__ == "__main__":
    asyncio.run(test_workflow())
