#!/usr/bin/env python3
"""
Sample script to demonstrate document processing via Temporal workflow.
This script can be used to upload and process documents through the RAG system.
"""

import asyncio
import json
import httpx
from pathlib import Path

# Sample documents for testing
SAMPLE_DOCUMENTS = [
    {
        "id": "machine_learning_intro",
        "text": """Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every task.

The core idea behind machine learning is to create algorithms that can automatically improve their performance on a specific task through experience. This is achieved by feeding large amounts of data to the algorithm, allowing it to identify patterns and relationships.

There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Supervised learning uses labeled data to train models, unsupervised learning finds patterns in unlabeled data, and reinforcement learning learns through trial and error with rewards and penalties.

Machine learning has revolutionized many industries including healthcare, finance, transportation, and entertainment. Applications range from recommendation systems and fraud detection to autonomous vehicles and medical diagnosis.""",
        "metadata": {
            "topic": "machine_learning",
            "difficulty": "beginner",
            "source": "educational_content"
        }
    },
    {
        "id": "python_programming_basics",
        "text": """Python is a high-level, interpreted programming language known for its simplicity and readability. Created by Guido van Rossum in the late 1980s, Python has become one of the most popular programming languages in the world.

Python's syntax is designed to be intuitive and similar to natural language, making it an excellent choice for beginners. The language emphasizes code readability with its use of indentation to define code blocks rather than curly braces or keywords.

Key features of Python include dynamic typing, automatic memory management, and a vast standard library. Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.

Python is widely used in web development, data science, artificial intelligence, scientific computing, and automation. Popular frameworks and libraries include Django and Flask for web development, NumPy and Pandas for data analysis, and TensorFlow and PyTorch for machine learning.""",
        "metadata": {
            "topic": "programming",
            "language": "python",
            "difficulty": "beginner",
            "source": "programming_guide"
        }
    },
    {
        "id": "data_structures_overview",
        "text": """Data structures are specialized formats for organizing, storing, and manipulating data in computer programs. They provide a way to manage and organize data so that it can be accessed and modified efficiently.

Common linear data structures include arrays, linked lists, stacks, and queues. Arrays provide constant-time access to elements by index, while linked lists allow for efficient insertion and deletion. Stacks follow the Last-In-First-Out (LIFO) principle, and queues follow the First-In-First-Out (FIFO) principle.

Non-linear data structures include trees and graphs. Trees are hierarchical structures with a root node and child nodes, commonly used in file systems and databases. Graphs consist of vertices connected by edges and are used to represent relationships between entities.

The choice of data structure significantly impacts the performance of algorithms. Understanding the time and space complexity of different operations on various data structures is crucial for writing efficient programs. Hash tables, for example, provide average-case constant-time access but may have worst-case linear time complexity.""",
        "metadata": {
            "topic": "computer_science",
            "difficulty": "intermediate",
            "source": "cs_fundamentals"
        }
    }
]

async def upload_documents_via_workflow(base_url: str = "http://localhost:8000"):
    """
    Upload documents through the Temporal workflow integration.
    
    Args:
        base_url: Base URL of the FastAPI service
    """
    
    print("🚀 Starting document upload via Temporal workflow...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Trigger the workflow via main FastAPI service
            print(f"📤 Sending {len(SAMPLE_DOCUMENTS)} documents for processing...")
            
            response = await client.post(
                f"{base_url}/workflow/process-documents",
                json=SAMPLE_DOCUMENTS
            )
            
            response.raise_for_status()
            result = response.json()
            
            workflow_id = result.get("workflow_id")
            print(f"✅ Workflow started with ID: {workflow_id}")
            
            # Monitor workflow progress
            if workflow_id:
                print("\n📊 Monitoring workflow progress...")
                await monitor_workflow_progress(client, base_url, workflow_id)
            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def monitor_workflow_progress(client: httpx.AsyncClient, base_url: str, workflow_id: str):
    """
    Monitor the progress of a workflow until completion.
    
    Args:
        client: HTTP client
        base_url: Base URL of the service
        workflow_id: ID of the workflow to monitor
    """
    
    max_attempts = 60  # 5 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        await asyncio.sleep(5)  # Check every 5 seconds
        attempt += 1
        
        try:
            response = await client.get(
                f"{base_url}/workflow/{workflow_id}/status"
            )
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                
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
            else:
                print(f"⚠️  Error checking status: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Error checking status: {e}")
    
    if attempt >= max_attempts:
        print("⏰ Timeout waiting for workflow completion")

async def upload_documents_direct(base_url: str = "http://localhost:8003"):
    """
    Upload documents directly to the Temporal API service.
    
    Args:
        base_url: Base URL of the Temporal API service
    """
    
    print("🚀 Starting direct document upload to Temporal API...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{base_url}/process-documents",
                json={"documents": SAMPLE_DOCUMENTS}
            )
            
            response.raise_for_status()
            result = response.json()
            
            workflow_id = result.get("workflow_id")
            print(f"✅ Workflow started with ID: {workflow_id}")
            
            # Monitor progress directly via Temporal API
            if workflow_id:
                print("\n📊 Monitoring workflow progress...")
                await monitor_workflow_direct(client, base_url, workflow_id)
            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def monitor_workflow_direct(client: httpx.AsyncClient, base_url: str, workflow_id: str):
    """Monitor workflow via direct Temporal API."""
    
    max_attempts = 60
    attempt = 0
    
    while attempt < max_attempts:
        await asyncio.sleep(5)
        attempt += 1
        
        try:
            response = await client.get(f"{base_url}/workflow/{workflow_id}/status")
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                
                print(f"⏱️  Attempt {attempt}: Workflow status = {status}")
                
                if status == "completed":
                    print("🎉 Workflow completed successfully!")
                    if status_data.get("result"):
                        print("\n📊 Results:")
                        print(json.dumps(status_data["result"], indent=2))
                    break
                elif status == "failed":
                    print("❌ Workflow failed!")
                    break
                elif status in ["running", "workflow_execution_status_running"]:
                    print("⚙️  Workflow is still running...")
                    
        except Exception as e:
            print(f"⚠️  Error: {e}")
    
    if attempt >= max_attempts:
        print("⏰ Timeout waiting for completion")

async def test_services():
    """Test that all services are available."""
    
    services = [
        ("http://localhost:8000/health", "Main FastAPI"),
        ("http://localhost:8003/health", "Temporal API")
    ]
    
    print("🏥 Testing service health...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url, name in services:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    print(f"✅ {name} is healthy")
                else:
                    print(f"⚠️  {name} returned {response.status_code}")
            except Exception as e:
                print(f"❌ {name} is not available: {e}")

async def main():
    """Main function."""
    
    print("📚 Temporal Document Processing Demo")
    print("=" * 40)
    
    # Test services first
    await test_services()
    print()
    
    # Ask user for upload method
    print("Choose upload method:")
    print("1. Via main FastAPI service (http://localhost:8000)")
    print("2. Direct to Temporal API service (http://localhost:8003)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            await upload_documents_via_workflow()
        elif choice == "2":
            await upload_documents_direct()
        else:
            print("Invalid choice. Using method 1 (via main FastAPI service)")
            await upload_documents_via_workflow()
            
    except KeyboardInterrupt:
        print("\n👋 Upload cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\n✨ Demo completed!")

if __name__ == "__main__":
    asyncio.run(main())
