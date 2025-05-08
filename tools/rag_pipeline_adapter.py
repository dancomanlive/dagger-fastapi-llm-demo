"""
Backward compatibility module for legacy code that imports from tools.rag_pipeline.
This module simply re-exports functions from pipelines.rag_pipeline.
"""
from pipelines.rag_pipeline import ingest_document, query_rag

# Add any other functions that might be used externally
__all__ = ['ingest_document', 'query_rag']
