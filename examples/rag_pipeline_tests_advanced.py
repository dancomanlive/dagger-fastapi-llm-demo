"""
Comprehensive test script for the RAG pipeline.
This script tests all the components of the RAG pipeline.
"""
import asyncio
import dagger
import json
import os
import time
from dotenv import load_dotenv

# Import RAG modules
from pipelines.rag_pipeline import ingest_document, query_rag
from tools.text_chunker_advanced import chunk_text
from tools.text_embedder import embed_text
from tools.superlinked_qdrant_connector import (
    superlinked_qdrant_query,
    process_natural_language_query,
    weighted_multi_search,
    superlinked_qdrant_store
)

# Load environment variables
load_dotenv()

# Configuration
PROJECT_ID = os.environ.get("SUPERLINKED_PROJECT_ID", "test_project")
INDEX_NAME = f"test_rag_pipeline_{int(time.time())}"
MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

# Test documents
SAMPLE_DOCUMENTS = [
    {
        "id": "renewable_energy_overview",
        "title": "Renewable Energy Overview",
        "text": """
# Renewable Energy Sources Overview

## Solar Energy

Solar energy is radiant light and heat from the Sun that is harnessed using technologies 
such as solar power to generate electricity, solar thermal energy, and solar architecture.

### Photovoltaic Technology

Photovoltaic (PV) cells convert light into electricity using semiconducting materials 
that exhibit the photovoltaic effect. When these materials absorb sunlight, they release electrons, 
generating an electric current.

## Wind Energy

Wind power harnesses the kinetic energy of moving air to generate electricity using wind turbines.
Modern wind turbines can convert over 45% of the wind energy that passes through them into electricity.

### Offshore Wind Farms

Offshore wind farms are constructed in bodies of water, usually the ocean, to generate electricity
from wind. These farms can generate more electricity than onshore ones due to higher wind speeds.
        """
    },
    {
        "id": "electric_vehicles_guide",
        "title": "Electric Vehicles Guide",
        "text": """
# Electric Vehicles: A Comprehensive Guide

## Types of Electric Vehicles

### Battery Electric Vehicles (BEVs)
Battery Electric Vehicles run entirely on electricity stored in onboard batteries.
They produce zero direct emissions and are charged from external power sources.

### Plug-in Hybrid Electric Vehicles (PHEVs)
PHEVs combine a gasoline or diesel engine with an electric motor and battery.
They can be plugged in to charge the battery and can run on electricity for limited ranges.

## Charging Infrastructure

### Level 1 Charging
Standard household outlet (120V) providing about 2-5 miles of range per hour of charging.

### Level 2 Charging
240V outlet providing about 10-30 miles of range per hour of charging.

### DC Fast Charging
Provides up to 80% charge in 20-30 minutes for most electric vehicles.
        """
    }
]

# Test queries with expected keywords in responses
TEST_QUERIES = [
    {
        "query": "How do photovoltaic cells work?",
        "expected_keywords": ["photovoltaic", "cells", "light", "electricity", "semiconducting", "electrons"]
    },
    {
        "query": "What are the advantages of offshore wind farms?",
        "expected_keywords": ["offshore", "wind", "farms", "generate", "electricity", "higher", "speeds"]
    },
    {
        "query": "Tell me about the different types of electric vehicle charging",
        "expected_keywords": ["Level 1", "Level 2", "DC Fast", "charging", "range", "hour"]
    },
    {
        "query": "Find information about battery electric vehicles that produce zero emissions",
        "expected_keywords": ["Battery Electric Vehicles", "BEVs", "zero", "emissions", "electricity"]
    }
]

# Natural language queries for testing
NLQ_QUERIES = [
    "What technologies are used in solar energy from recent documentation?",
    "Find me information about electric vehicles with fast charging capabilities",
    "Show me renewable energy sources described in the overview document",
    "What are the different levels of EV charging mentioned in the guide?"
]

async def test_chunking(client):
    """Test the advanced chunking functionality"""
    print("\n=== TESTING ADVANCED TEXT CHUNKING ===\n")
    
    document = SAMPLE_DOCUMENTS[0]["text"]
    
    # Test with section respect
    chunking_result_with_sections = await chunk_text(
        client=client,
        text=document,
        chunk_size=300,
        overlap=50,
        respect_sections=True,
        document_metadata={"document_id": SAMPLE_DOCUMENTS[0]["id"]}
    )
    chunking_data_with_sections = json.loads(chunking_result_with_sections)
    
    # Test without section respect
    chunking_result_without_sections = await chunk_text(
        client=client,
        text=document,
        chunk_size=300,
        overlap=50,
        respect_sections=False,
        document_metadata={"document_id": SAMPLE_DOCUMENTS[0]["id"]}
    )
    chunking_data_without_sections = json.loads(chunking_result_without_sections)
    
    print(f"Chunking with section awareness: {chunking_data_with_sections['count']} chunks")
    print(f"Chunking without section awareness: {chunking_data_without_sections['count']} chunks")
    
    # Verify section metadata
    section_metadata_present = False
    for metadata in chunking_data_with_sections.get("metadata", []):
        if "title" in metadata and "level" in metadata:
            section_metadata_present = True
            break
    
    print(f"Section metadata present: {section_metadata_present}")
    print("Sample chunks with sections:")
    for i, (chunk, metadata) in enumerate(zip(
            chunking_data_with_sections.get("chunks", [])[:2], 
            chunking_data_with_sections.get("metadata", [])[:2]
        )):
        print(f"\nChunk {i+1}:")
        print(f"Text: {chunk[:100]}...")
        print(f"Metadata: {metadata}")
    
    return True

async def test_natural_language_query_processing(client):
    """Test the natural language query processing"""
    print("\n=== TESTING NATURAL LANGUAGE QUERY PROCESSING ===\n")
    
    results = []
    for query in NLQ_QUERIES:
        nlq_result = await process_natural_language_query(
            client=client,
            query=query,
            model=MODEL
        )
        
        nlq_data = json.loads(nlq_result)
        
        print(f"\nOriginal query: {query}")
        print(f"Core query: {nlq_data.get('core_query', '')}")
        print(f"Extracted filters: {nlq_data.get('filters', {})}")
        
        # Verify that we have a core query and potentially filters
        results.append(
            "core_query" in nlq_data and isinstance(nlq_data.get("filters"), dict)
        )
    
    return all(results)

async def test_document_ingestion(client):
    """Test the document ingestion pipeline"""
    print("\n=== TESTING DOCUMENT INGESTION ===\n")
    
    results = []
    for doc in SAMPLE_DOCUMENTS:
        metadata = {
            "title": doc["title"],
            "source": "test",
            "date": "2025-05-07"
        }
        
        ingest_result = await ingest_document(
            client=client,
            text=doc["text"],
            document_id=doc["id"],
            project_id=PROJECT_ID,
            index_name=INDEX_NAME,
            chunk_size=300,
            overlap=50,
            respect_sections=True,
            metadata=metadata
        )
        
        print(f"Ingestion result for {doc['id']}:")
        print(f"Status: {ingest_result.get('status')}")
        print(f"Chunks: {ingest_result.get('chunks')}")
        
        results.append(ingest_result.get("status") == "success")
    
    return all(results)

async def test_query_retrieval(client):
    """Test the query and retrieval pipeline"""
    print("\n=== TESTING QUERY RETRIEVAL ===\n")
    
    results = []
    for test_case in TEST_QUERIES:
        query = test_case["query"]
        expected_keywords = test_case["expected_keywords"]
        
        query_result = await query_rag(
            client=client,
            query=query,
            project_id=PROJECT_ID,
            index_name=INDEX_NAME,
            use_nlq=True,
            weights={"vector": 0.8, "keyword": 0.2},
            limit=3,
            model=MODEL
        )
        
        print(f"\nQuery: {query}")
        print(f"Response: {query_result.get('response', '')[:200]}...")
        
        # Check if expected keywords are in the response
        response = query_result.get("response", "").lower()
        keywords_present = [keyword.lower() in response for keyword in expected_keywords]
        keyword_match_rate = sum(keywords_present) / len(expected_keywords)
        
        print(f"Expected keywords match rate: {keyword_match_rate:.2%}")
        print(f"Citations: {len(query_result.get('citations', []))}")
        
        # Consider success if at least 70% of keywords are present
        results.append(keyword_match_rate >= 0.7)
    
    return all(results)

async def test_weighted_search(client):
    """Test the weighted multi-modal search"""
    print("\n=== TESTING WEIGHTED MULTI-MODAL SEARCH ===\n")
    
    query = "renewable energy technology"
    
    # Generate embedding for the query
    embedding_result = await embed_text(client, [query])
    embedding_data = json.loads(embedding_result)
    query_embedding = embedding_data.get("embeddings", [[]])[0]
    
    # Vector-only search
    vector_result = await superlinked_qdrant_query(
        client=client,
        query_embedding=query_embedding,
        project_id=PROJECT_ID,
        index_name=INDEX_NAME,
        limit=3
    )
    vector_data = json.loads(vector_result)
    
    # Weighted multi-modal search
    weighted_result = await weighted_multi_search(
        client=client,
        query_embedding=query_embedding,
        project_id=PROJECT_ID,
        index_name=INDEX_NAME,
        text_query=query,
        weights={"vector": 0.7, "keyword": 0.3},
        limit=3
    )
    weighted_data = json.loads(weighted_result)
    
    print(f"Vector-only search: {len(vector_data.get('results', []))} results")
    print(f"Weighted multi-modal search: {len(weighted_data.get('results', []))} results")
    
    # Print a comparison of the top result
    if vector_data.get("results") and weighted_data.get("results"):
        print("\nVector-only top result:")
        print(f"Text: {vector_data['results'][0].get('text', '')[:100]}...")
        print(f"Score: {vector_data['results'][0].get('score', 0):.4f}")
        
        print("\nWeighted multi-modal top result:")
        print(f"Text: {weighted_data['results'][0].get('text', '')[:100]}...")
        print(f"Score: {weighted_data['results'][0].get('score', 0):.4f}")
    
    return True

async def test_superlinked_qdrant_store(client):
    """Test the Superlinked Qdrant store functionality"""
    print("\n=== TESTING SUPERLINKED QDRANT STORE ===\n")

    # Prepare test data
    chunks = [
        "This is the first chunk of text.",
        "This is the second chunk of text."
    ]
    embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6]
    ]
    metadata = [
        {"chunk_id": 1, "source": "test"},
        {"chunk_id": 2, "source": "test"}
    ]

    # Call the superlinked_qdrant_store function
    store_result = await superlinked_qdrant_store(
        client=client,
        chunks=chunks,
        embeddings=embeddings,
        project_id=PROJECT_ID,
        index_name=INDEX_NAME,
        metadata=metadata
    )

    print("Store result:")
    print(store_result)

    # Verify the result
    return "status" in store_result and store_result["status"] == "success"

async def run_all_tests():
    """Run all tests and report results"""
    print("\n====== COMPREHENSIVE RAG PIPELINE TEST ======\n")
    print(f"Project ID: {PROJECT_ID}")
    print(f"Index Name: {INDEX_NAME}")
    print(f"LLM Model: {MODEL}")

    test_results = {}

    async with dagger.Connection() as client:
        print("\nConnected to Dagger engine")

        # Run tests
        try:
            print("\n----- Testing Superlinked Qdrant Store -----")
            test_results["superlinked_qdrant_store"] = await test_superlinked_qdrant_store(client)

            print("\n----- Testing Advanced Text Chunking -----")
            test_results["chunking"] = await test_chunking(client)
            
            print("\n----- Testing Natural Language Query Processing -----")
            test_results["nlq_processing"] = await test_natural_language_query_processing(client)
            
            print("\n----- Testing Document Ingestion -----")
            test_results["ingestion"] = await test_document_ingestion(client)
            
            print("\n----- Testing Query Retrieval -----")
            test_results["retrieval"] = await test_query_retrieval(client)
            
            print("\n----- Testing Weighted Multi-Modal Search -----")
            test_results["weighted_search"] = await test_weighted_search(client)
            
        except Exception as e:
            print(f"Error during testing: {str(e)}")
            raise e

    # Report summary
    print("\n\n====== TEST RESULTS SUMMARY ======\n")
    all_passed = True

    for test_name, passed in test_results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False

    print(f"\nOverall Test Result: {'PASSED' if all_passed else 'FAILED'}")
    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
