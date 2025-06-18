#!/usr/bin/env python3
"""
Simple test for document retrieval
"""
import asyncio
from temporalio.client import Client

async def test_retrieval():
    client = await Client.connect('localhost:7233', namespace='default')
    
    workflow_handle = await client.start_workflow(
        "GenericPipelineWorkflow",
        args=["document_retrieval", ["machine learning algorithms"]],
        id=f"test-retrieval-{int(asyncio.get_event_loop().time() * 1000)}",
        task_queue="document-processing-queue"
    )
    
    result = await workflow_handle.result()
    print(f"Retrieval result: {result}")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
