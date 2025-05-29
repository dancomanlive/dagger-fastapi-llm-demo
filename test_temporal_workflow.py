#!/usr/bin/env python3
"""
Example client for testing the Temporal document processing workflow.
"""

import asyncio
import httpx
import json

# Service URLs
TEMPORAL_API_URL = "http://localhost:8003"

async def test_document_processing():
    """Test the document processing workflow."""
    
    # Sample documents
    documents = [
        {
            "id": "doc1",
            "text": """This is the first document with multiple paragraphs for testing.

This is the second paragraph of the first document. It contains some meaningful content that should be processed separately.

And this is the third paragraph with even more content to demonstrate the chunking functionality.""",
            "metadata": {
                "source": "test_suite",
                "document_type": "sample",
                "created_by": "test_client"
            }
        },
        {
            "id": "doc2", 
            "text": """Another document for processing through the Temporal workflow.

This document also has multiple paragraphs that will be chunked and embedded.

The embedding service will process these chunks and store them in Qdrant for retrieval.""",
            "metadata": {
                "source": "test_suite",
                "document_type": "sample",
                "priority": "high"
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("🚀 Starting document processing workflow...")
            
            # Start the workflow
            response = await client.post(
                f"{TEMPORAL_API_URL}/process-documents",
                json={"documents": documents}
            )
            response.raise_for_status()
            
            result = response.json()
            workflow_id = result["workflow_id"]
            
            print(f"✅ Workflow started with ID: {workflow_id}")
            print(f"📊 Processing {len(documents)} documents")
            
            # Poll for completion
            print("\n📋 Monitoring workflow progress...")
            max_attempts = 60  # 5 minutes max
            attempt = 0
            
            while attempt < max_attempts:
                await asyncio.sleep(5)  # Check every 5 seconds
                attempt += 1
                
                # Check status
                status_response = await client.get(
                    f"{TEMPORAL_API_URL}/workflow/{workflow_id}/status"
                )
                status_response.raise_for_status()
                
                status_data = status_response.json()
                status = status_data["status"]
                
                print(f"⏱️  Attempt {attempt}: Workflow status = {status}")
                
                if status == "completed":
                    print("🎉 Workflow completed successfully!")
                    if status_data.get("result"):
                        print("\n📊 Results:")
                        print(json.dumps(status_data["result"], indent=2))
                    break
                elif status == "failed":
                    print("❌ Workflow failed!")
                    if status_data.get("error"):
                        print(f"Error: {status_data['error']}")
                    break
                elif status in ["running", "workflow_execution_status_running"]:
                    print("⚙️  Workflow is still running...")
                else:
                    print(f"❓ Unknown status: {status}")
            
            if attempt >= max_attempts:
                print("⏰ Timeout waiting for workflow completion")
                
                # Try to get the result anyway
                try:
                    result_response = await client.get(
                        f"{TEMPORAL_API_URL}/workflow/{workflow_id}/result"
                    )
                    if result_response.status_code == 200:
                        final_result = result_response.json()
                        print("\n📊 Final result:")
                        print(json.dumps(final_result, indent=2))
                except Exception as e:
                    print(f"❌ Could not get final result: {e}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_health():
    """Test the health endpoint."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{TEMPORAL_API_URL}/health")
            response.raise_for_status()
            health_data = response.json()
            print(f"🏥 Health check: {health_data}")
            return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

async def main():
    """Main test function."""
    print("🧪 Testing Temporal Document Processing Service\n")
    
    # Test health first
    print("1. Testing health endpoint...")
    if not await test_health():
        print("❌ Service is not healthy. Exiting.")
        return
    
    print("\n2. Testing document processing workflow...")
    await test_document_processing()
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
