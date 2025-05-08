"""
RAG pipeline orchestrator using Superlinked + Qdrant.
"""
import json
import dagger
from tools.text_embedder import embed_text
from tools.text_chunker_advanced import chunk_text
from tools.superlinked_qdrant_connector import (
    superlinked_qdrant_store,
    process_natural_language_query,
    weighted_multi_search
)
from tools.rag_generator import generate_rag_response_with_citations
from pipelines.document_schema import DocumentSchema
import warnings

async def ingest_document(
    client: dagger.Client,
    text: str,
    document_id: str,
    project_id: str,
    index_name: str = "default_index",
    chunk_size: int = 1000,
    overlap: int = 200,
    respect_sections: bool = True,
    metadata: dict = None
) -> dict:
    """
    Ingest a document into the RAG system.
    
    Args:
        client: Dagger client
        text: Document text
        document_id: Unique identifier for the document
        project_id: Superlinked project ID
        index_name: Superlinked index name
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        respect_sections: Whether to respect section boundaries
        metadata: Additional metadata for the document
        
    Returns:
        Dict with ingestion results
    """
    # Add document_id to metadata
    doc_metadata = {"document_id": document_id}
    if metadata:
        doc_metadata.update(metadata)
    
    # Validate document against schema
    document = DocumentSchema(
        document_id=document_id,
        text=text,
        embeddings=[],  # Placeholder, will be populated after embedding generation
        metadata=metadata or {}
    )

    # Use the validated document's metadata
    doc_metadata = document.metadata
    doc_metadata["document_id"] = document.document_id

    # Ensure large datasets are chunked efficiently
    if len(text) > chunk_size * 10:  # Example threshold
        warnings.warn("Large document detected. Consider increasing chunk size or reducing overlap.")
    
    # Step 1: Chunk the text
    chunking_result = await chunk_text(
        client, 
        text, 
        chunk_size, 
        overlap, 
        respect_sections,
        doc_metadata
    )
    chunking_data = json.loads(chunking_result)
    
    chunks = chunking_data.get("chunks", [])
    chunk_metadata = chunking_data.get("metadata", [])
    
    if not chunks:
        return {"status": "error", "message": "No chunks generated"}
    
    # Step 2: Generate embeddings for chunks
    embedding_result = await embed_text(client, chunks)
    embedding_data = json.loads(embedding_result)
    
    embeddings = embedding_data.get("embeddings", [])
    if not embeddings:
        return {"status": "error", "message": "No embeddings generated"}
    
    # Step 3: Store in Superlinked using advanced Qdrant connector
    storage_result = await superlinked_qdrant_store(
        client, 
        chunks, 
        embeddings, 
        project_id, 
        index_name, 
        chunk_metadata
    )
    storage_data = json.loads(storage_result)
    
    # Return results
    return {
        "status": "success",
        "document_id": document_id,
        "chunks": len(chunks),
        "storage_result": storage_data
    }

async def query_rag(
    client: dagger.Client,
    query: str,
    project_id: str,
    index_name: str,
    use_nlq: bool = True,
    weights: dict = None,
    filters: dict = None,
    limit: int = 5,
    model: str = "gpt-4o-mini"
) -> dict:
    """
    Query the RAG system with advanced capabilities.
    
    Args:
        client: Dagger client
        query: User query
        project_id: Superlinked project ID
        index_name: Superlinked index name
        use_nlq: Whether to use natural language query processing
        weights: Weights for different search factors
        filters: Metadata filters for search
        limit: Maximum number of results
        model: LLM model to use
        
    Returns:
        Dict with query results, generated response, and citations
    """
    # Process natural language query if enabled
    nlq_filters = None
    if use_nlq:
        # Define a system prompt for NLQ processing
        system_prompt = (
            "Extract structured search parameters from the user query. "
            "Ensure the output includes core query, filters, and weights."
        )

        # Pass the system prompt to the NLQ processing function
        nlq_result = await process_natural_language_query(client, query, model, system_prompt=system_prompt)
        nlq_data = json.loads(nlq_result)
        
        # Extract core query and filters
        core_query = nlq_data.get("core_query", query)
        nlq_filters = nlq_data.get("filters", {})
        
        # Combine with provided filters
        if filters and nlq_filters:
            combined_filters = {**filters, **nlq_filters}
        elif nlq_filters:
            combined_filters = nlq_filters
        else:
            combined_filters = filters
    else:
        core_query = query
        combined_filters = filters
    
    # Generate embedding for the query
    embedding_result = await embed_text(client, [core_query])
    embedding_data = json.loads(embedding_result)
    
    query_embedding = embedding_data.get("embeddings", [[]])[0]
    if not query_embedding:
        return {"status": "error", "message": "Failed to generate query embedding"}
    
    # Retrieve relevant chunks using weighted multi-search
    retrieval_result = await weighted_multi_search(
        client,
        query_embedding,
        project_id,
        index_name,
        text_query=core_query,
        weights=weights,
        filters=combined_filters,
        limit=limit
    )
    retrieval_data = json.loads(retrieval_result)
    
    # Check if retrieval was successful
    if retrieval_data.get("status") != "success":
        return {"status": "error", "message": "Failed to retrieve documents", "details": retrieval_data}
    
    # Extract text chunks and metadata from retrieval results
    context_chunks = []
    chunk_metadata = []
    
    for result in retrieval_data.get("results", []):
        if "text" in result:
            context_chunks.append(result["text"])
            
            # Extract metadata
            metadata = {k: v for k, v in result.items() 
                       if k not in ["text", "score", "document_id"]}
            chunk_metadata.append(metadata)
    
    if not context_chunks:
        return {"status": "error", "message": "No relevant context found"}
    
    # Generate response using RAG with citations
    generation_result = await generate_rag_response_with_citations(
        client, query, context_chunks, chunk_metadata, model
    )
    generation_data = json.loads(generation_result)
    
    # Return combined results with citations
    return {
        "status": "success",
        "query": query,
        "processed_query": core_query if use_nlq else query,
        "extracted_filters": nlq_filters if use_nlq else None,
        "response": generation_data.get("response", ""),
        "context_chunks": context_chunks,
        "citations": generation_data.get("citations", []),
        "retrieval_data": retrieval_data
    }
