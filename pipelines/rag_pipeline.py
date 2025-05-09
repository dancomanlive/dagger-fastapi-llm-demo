"""
RAG Pipeline using Superlinked and Qdrant.
This module provides a higher-level interface for implementing a RAG (Retrieval-Augmented Generation)
pipeline using Superlinked for semantic search and Qdrant as the vector database.
"""
import os
import dagger
from typing import Dict, Any, List, Optional, Union
import json
import logging

from tools.superlinked_qdrant_connector import initialize_qdrant, query_qdrant, create_vector_index
from tools.core import SCRIPTS_DIR, get_tool_base, run_container_and_check

logger = logging.getLogger(__name__)

class RagPipeline:
    """
    Implements a Retrieval-Augmented Generation pipeline using Superlinked and Qdrant.
    """
    
    def __init__(
        self, 
        client: dagger.Client,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        default_query_limit: int = 10,
        model: str = "gpt-4o",
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            client: Dagger client
            qdrant_url: URL to the Qdrant instance (defaults to env var QDRANT_URL)
            qdrant_api_key: API key for Qdrant (defaults to env var QDRANT_API_KEY)
            default_query_limit: Maximum number of query results to return
            model: LLM model to use for generation
        """
        self.client = client
        self.qdrant_url = qdrant_url or os.environ.get("QDRANT_URL", "http://qdrant:6333")
        self.qdrant_api_key = qdrant_api_key or os.environ.get("QDRANT_API_KEY", "")
        self.default_query_limit = default_query_limit
        self.model = model
        
    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize the RAG pipeline.
        
        Returns:
            Dict with initialization results
        """
        result = await initialize_qdrant(
            self.client,
            self.qdrant_url,
            self.qdrant_api_key,
            self.default_query_limit
        )
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"status": "error", "message": result}
    
    async def ingest_document(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """
        Ingest a document into the RAG pipeline.
        
        Args:
            text: Document text to ingest
            document_id: Unique identifier for the document
            metadata: Additional metadata for the document
            chunk_size: Size of text chunks to create
            chunk_overlap: Overlap between adjacent chunks
            
        Returns:
            Dict with ingestion results
        """
        # Set up container with Python and required packages
        container = get_tool_base(
            self.client, 
            "python:3.11-slim", 
            SCRIPTS_DIR
        )
        
        container = (
            container
            .with_exec(["pip", "install", "superlinked", "qdrant-client", "sentence-transformers"])
        )
        
        # Prepare parameters for the script
        params = {
            "qdrant_url": self.qdrant_url,
            "qdrant_api_key": self.qdrant_api_key,
            "text": text,
            "document_id": document_id,
            "metadata": metadata or {},
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap
        }
        
        # Write parameters to a file
        params_json = json.dumps(params)
        
        # Run the script to ingest the document
        result = await run_container_and_check(
            container,
            [
                "python", 
                "-c", 
                f"""
import json
from superlinked import framework as sl
from sentence_transformers import SentenceTransformer

# Load parameters
params = {params_json}

try:
    # Initialize QdrantVectorDatabase
    vector_database = sl.QdrantVectorDatabase(
        params['qdrant_url'],
        params['qdrant_api_key'],
    )
    
    # Create schema
    @sl.schema
    class Document:
        id: sl.IdField
        text: sl.String
        metadata: sl.JsonDict
    
    document_schema = Document()
    
    # Create embedding space
    text_space = sl.TextSimilaritySpace(
        text=document_schema.text,
        model_name="sentence-transformers/all-mpnet-base-v2"
    )
    
    # Create index
    index = sl.Index(
        spaces=[text_space],
        fields=[document_schema.metadata]
    )
    
    # Create a source and executor
    source = sl.InteractiveSource(document_schema)
    executor = sl.InteractiveExecutor(
        sources=[source],
        indices=[index],
        vector_database=vector_database,
    )
    
    # Create document
    doc = {{
        "id": params['document_id'],
        "text": params['text'],
        "metadata": params['metadata']
    }}
    
    # Ingest document
    executor.run().source.ingest(doc)
    
    print(json.dumps({{
        "status": "success",
        "message": "Document ingested successfully",
        "document_id": params['document_id']
    }}))
except Exception as e:
    print(json.dumps({{"status": "error", "message": str(e)}}))
                """
            ]
        )
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"status": "error", "message": result}
    
    async def query(
        self,
        query_text: str,
        index_name: str = "default",
        weights: Optional[Dict[str, float]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Query the RAG pipeline.
        
        Args:
            query_text: Text to search for
            index_name: Name of the index to query
            weights: Weights to apply to different spaces
            filters: Filters to apply to the query
            limit: Maximum number of results to return
            
        Returns:
            Dict with query results
        """
        result = await query_qdrant(
            self.client,
            self.qdrant_url,
            query_text,
            index_name,
            weights,
            filters,
            limit,
            self.qdrant_api_key
        )
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"status": "error", "message": result}
    
    async def generate_response(
        self,
        query_text: str,
        context: Union[str, List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        Generate a response using the RAG pipeline.
        
        Args:
            query_text: User query text
            context: Context for generation (string or list of document objects)
            
        Returns:
            Dict with generated response
        """
        # Prepare context
        if isinstance(context, list):
            context_text = "\n\n".join([f"Document {i+1}:\n{doc.get('text', '')}" 
                                       for i, doc in enumerate(context)])
        else:
            context_text = context
        
        # Set up container with Python and required packages
        container = get_tool_base(
            self.client, 
            "python:3.11-slim", 
            SCRIPTS_DIR
        )
        
        # Create a Dagger LLM directly
        llm = self.client.llm().with_model(self.model)
        
        # Create the prompt with context and query
        prompt = f"""
You are a knowledgeable assistant that responds to queries based on provided context.
Use only the information provided in the context to answer the question.
If the context doesn't contain relevant information, say so clearly.

Context:
{context_text}

User Question: {query_text}

Answer:
"""
        
        # Get the response using Dagger's built-in LLM client
        response = await llm.with_prompt(prompt).last_reply()
        
        return {
            "status": "success",
            "query": query_text,
            "response": response,
            "sources": context if isinstance(context, list) else []
        }
        
    async def process_query(
        self,
        query_text: str,
        index_name: str = "default",
        weights: Optional[Dict[str, float]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        use_nlq: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a query through the complete RAG pipeline:
        1. Retrieve relevant documents
        2. Use the retrieved documents to generate a response
        
        Args:
            query_text: User query text
            index_name: Name of the index to query
            weights: Weights to apply to different spaces
            filters: Filters to apply to the query
            limit: Maximum number of results to return
            use_nlq: Whether to use Natural Language Querying
            
        Returns:
            Dict with query results and generated response
        """
        # Retrieve relevant documents
        retrieval_result = await self.query(
            query_text,
            index_name,
            weights,
            filters,
            limit
        )
        
        if retrieval_result.get("status") != "success":
            return retrieval_result
        
        # Extract the retrieved documents
        documents = retrieval_result.get("results", [])
        
        # Generate a response based on the retrieved documents
        generation_result = await self.generate_response(
            query_text,
            documents
        )
        
        # Combine results
        return {
            "status": "success",
            "query": query_text,
            "response": generation_result.get("response", ""),
            "sources": documents
        }
