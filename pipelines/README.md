# Pipelines

This directory contains orchestrated workflows that combine multiple tools to provide higher-level functionality.

## Available Pipelines

### RAG Pipeline (`rag_pipeline.py`)

The RAG (Retrieval-Augmented Generation) pipeline orchestrates the complete workflow for document ingestion, embedding, retrieval, and generation with citations. It combines text chunking, embedding, storage, retrieval, and response generation into a cohesive workflow.

Key functions:
- `ingest_document`: Process and store documents in the RAG system
- `query_rag`: Query the RAG system to get responses with citations

### CI Pipeline (`ci_pipeline.py`)

A continuous integration pipeline using Dagger to build and push Docker images.

## Directory Structure

The pipelines folder creates a clear separation between:
- Tools: Individual, reusable components in the `/tools` directory
- Pipelines: Orchestrated workflows that use multiple tools

## Usage

Import pipeline modules in your code:

```python
from pipelines.rag_pipeline import ingest_document, query_rag

# Use the pipeline functions
result = await ingest_document(
    client=client,
    text=document_text,
    document_id="doc-123",
    # Additional parameters...
)
```
