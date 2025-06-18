#!/usr/bin/env python3
"""
End-to-End Temporal Workflow Test Script

This script tests the complete document processing pipeline using GenericPipelineWorkflow:
1. document_processing pipeline - processes and embeds documents
2. document_retrieval pipeline - searches for relevant documents
3. Validates the complete workflow chain

Usage:
    python tests/test_temporal_e2e.py
"""

import asyncio
import time
import os
import sys
from typing import Dict, Any
from temporalio.client import Client

# Temporal Configuration
TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
COLLECTION_NAME = os.environ.get("TEST_DOCUMENT_COLLECTION_NAME", "test-document-chunks")

# Test document
TEST_DOCUMENT = {
    "id": "e2e-test-doc",
    "text": "This is an automated end-to-end test document about machine learning algorithms and neural networks. Deep learning has transformed computer vision and natural language processing. Artificial intelligence and machine learning are revolutionizing technology.",
    "metadata": {"source": "e2e_test", "type": "test_document"}
}

TEST_QUERY = "machine learning algorithms"

print(f"🔧 DEBUG: Using collection name: {COLLECTION_NAME}")

async def test_document_processing_pipeline(client: Client) -> str:
    """Test the document_processing pipeline using GenericPipelineWorkflow"""
    print("🔄 Testing document_processing pipeline...")
    
    workflow_id = f"e2e-doc-processing-{int(time.time() * 1000)}"
    
    try:
        # Start GenericPipelineWorkflow with document_processing pipeline
        workflow_handle = await client.start_workflow(
            "GenericPipelineWorkflow",
            args=["document_processing", {"documents": [TEST_DOCUMENT], "collection": COLLECTION_NAME}],  # Pipeline name and documents with collection
            id=workflow_id,
            task_queue="document-processing-queue"
        )
        
        print(f"   Started workflow: {workflow_id}")
        
        # Wait for completion
        result = await workflow_handle.result()
        
        print("   ✅ Document processing pipeline completed successfully!")
        print(f"   📊 Result: {result}")
        
        return workflow_id
        
    except Exception as e:
        print(f"   ❌ Document processing pipeline failed: {str(e)}")
        print(f"   🔍 Exception type: {type(e).__name__}")
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"   🔍 Root cause: {e.__cause__}")
        import traceback
        print("   🔍 Full traceback:")
        traceback.print_exc()
        raise

async def test_retrieval_pipeline(client: Client) -> Dict[str, Any]:
    """Test the document_retrieval pipeline using GenericPipelineWorkflow"""
    print("🔍 Testing document_retrieval pipeline...")
    
    workflow_id = f"e2e-retrieval-{int(time.time() * 1000)}"
    
    try:
        # Start GenericPipelineWorkflow with document_retrieval pipeline
        workflow_handle = await client.start_workflow(
            "GenericPipelineWorkflow",
            args=["document_retrieval", {"query": TEST_QUERY, "top_k": 3, "collection": COLLECTION_NAME}],  # Pipeline name and input
            id=workflow_id,
            task_queue="document-processing-queue"
        )
        
        print(f"   Started workflow: {workflow_id}")
        
        # Wait for completion
        result = await workflow_handle.result()
        
        print("   ✅ Document retrieval pipeline completed successfully!")
        print(f"   📊 Found {len(result.get('final_result', {}).get('retrieved_documents', []))} results")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Document retrieval pipeline failed: {str(e)}")
        raise

async def test_health_check_pipeline(client: Client) -> str:
    """Test the health_check pipeline using GenericPipelineWorkflow"""
    print("🏥 Testing health_check pipeline...")
    
    workflow_id = f"e2e-health-{int(time.time() * 1000)}"
    
    try:
        # Start GenericPipelineWorkflow with health_check pipeline
        workflow_handle = await client.start_workflow(
            "GenericPipelineWorkflow",
            args=["health_check", None],  # Pipeline name and input (None for health check)
            id=workflow_id,
            task_queue="document-processing-queue"
        )
        
        print(f"   Started workflow: {workflow_id}")
        
        # Wait for completion
        result = await workflow_handle.result()
        
        print("   ✅ Health check pipeline completed successfully!")
        print(f"   📊 Health status: {result}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Health check pipeline failed: {str(e)}")
        raise

async def validate_retrieval_results(retrieval_result: Dict[str, Any]) -> bool:
    """Validate that retrieval results contain relevant content"""
    print("🔬 Validating retrieval results...")
    
    final_result = retrieval_result.get("final_result", {})
    retrieved_documents = final_result.get("retrieved_documents", [])
    
    if not retrieved_documents:
        print("   ❌ No retrieved documents found")
        print(f"   🔍 Final result keys: {list(final_result.keys()) if final_result else 'None'}")
        print(f"   🔍 Full result structure: {retrieval_result}")
        return False
    
    # Check if any result contains relevant keywords
    relevant_keywords = ["machine learning", "neural network", "artificial intelligence", "deep learning"]
    found_relevant = False
    
    for i, result in enumerate(retrieved_documents):
        text = result.get("text", "").lower()
        score = result.get("score", 0)
        print(f"   📄 Result {i+1}: score={score:.3f}, text_length={len(text)}")
        
        for keyword in relevant_keywords:
            if keyword in text:
                print(f"      ✅ Found relevant keyword: '{keyword}'")
                found_relevant = True
                break
    
    if found_relevant:
        print("   ✅ Retrieval results contain relevant content!")
        return True
    else:
        print("   ⚠️ No relevant content found in retrieval results")
        return False

async def main():
    """Main test execution"""
    print("🚀 Starting End-to-End Temporal Workflow Test")
    print(f"   Temporal Host: {TEMPORAL_HOST}")
    print(f"   Namespace: {TEMPORAL_NAMESPACE}")
    print(f"   Collection: {COLLECTION_NAME}")
    print("")
    
    try:
        # Connect to Temporal
        print("🔌 Connecting to Temporal...")
        client = await Client.connect(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
        print("   ✅ Connected to Temporal successfully!")
        print("")
        
        # Test 1: Health Check
        await test_health_check_pipeline(client)
        print("")
        
        # Test 2: Document Processing
        await test_document_processing_pipeline(client)
        print("")
        
        # Wait a moment for indexing to complete
        print("⏳ Waiting 10 seconds for document indexing to complete...")
        await asyncio.sleep(10)
        print("")
        
        # Test 3: Document Retrieval
        retrieval_result = await test_retrieval_pipeline(client)
        print("")
        
        # Test 4: Validate Results
        validation_passed = await validate_retrieval_results(retrieval_result)
        print("")
        
        # Final Summary
        if validation_passed:
            print("🎉 END-TO-END TEST PASSED!")
            print("✅ All Temporal workflows executed successfully")
            print("✅ Document processing and retrieval pipeline working correctly")
            print("✅ Pure Temporal architecture validated")
            return 0
        else:
            print("⚠️ END-TO-END TEST COMPLETED WITH WARNINGS")
            print("✅ All workflows executed successfully")
            print("⚠️ Retrieval validation had issues - check content relevance")
            return 1
            
    except Exception as e:
        print(f"❌ END-TO-END TEST FAILED: {str(e)}")
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
