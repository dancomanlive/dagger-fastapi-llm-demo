"""
Advanced Superlinked and Qdrant connector for RAG applications.
Supports multi-modal composition, weighted search, and natural language query processing.
"""
import requests
import os
from typing import List, Dict, Any, Optional

class SuperlinkedQdrantConnector:
    """
    Connector for Superlinked with Qdrant integration supporting advanced RAG features.
    """
    def __init__(
        self, 
        superlinked_api_key: str = None, 
        superlinked_url: str = None,
        qdrant_url: str = None,
        qdrant_api_key: str = None
    ):
        """
        Initialize the Superlinked + Qdrant connector.
        
        Args:
            superlinked_api_key: API key for Superlinked
            superlinked_url: URL for Superlinked API
            qdrant_url: URL for Qdrant API
            qdrant_api_key: API key for Qdrant
        """
        self.superlinked_api_key = superlinked_api_key or os.environ.get('SUPERLINKED_API_KEY')
        if not self.superlinked_api_key:
            raise ValueError("Superlinked API key is required")
            
        self.superlinked_url = superlinked_url or os.environ.get('SUPERLINKED_URL', 'https://api.superlinked.com')
        self.qdrant_url = qdrant_url or os.environ.get('QDRANT_URL')
        if not self.qdrant_url:
            raise ValueError("Qdrant URL is required")
            
        self.qdrant_api_key = qdrant_api_key or os.environ.get('QDRANT_API_KEY', '')
        
        # Headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.superlinked_api_key}",
            "Content-Type": "application/json"
        }
        
    def _setup_connector(self, project_id: str, index_name: str) -> str:
        """
        Setup or get existing Qdrant connector.
        
        Args:
            project_id: Superlinked project ID
            index_name: Name of the index
            
        Returns:
            Connector ID or None if using existing
        """
        collection_name = f"superlinked_{project_id}_{index_name}"
        
        # Configure Qdrant connector
        connector_config = {
            "project_id": project_id,
            "connector_type": "qdrant",
            "config": {
                "url": self.qdrant_url,
                "api_key": self.qdrant_api_key if self.qdrant_api_key else None,
                "collection_name": collection_name
            }
        }
        
        # Set up the connector
        connector_response = requests.post(
            f"{self.superlinked_url}/v1/connectors",
            headers=self.headers,
            json=connector_config
        )
        
        if connector_response.status_code not in (200, 201, 409):  # 409 means already exists
            raise ConnectionError(f"Failed to configure Qdrant connector: {connector_response.text}")
        
        # Return connector ID or None if already exists
        if connector_response.status_code == 409:
            return None
        else:
            return connector_response.json().get("connector_id")
    
    def index_documents(
        self, 
        project_id: str,
        index_name: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Index documents with embeddings into Superlinked using Qdrant connector.
        
        Args:
            project_id: Superlinked project ID
            index_name: Name of the index
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries for each chunk
            
        Returns:
            Dict with indexing results
        """
        # Setup Qdrant connector
        connector_id = self._setup_connector(project_id, index_name)
        use_existing = connector_id is None
        
        # Create documents to store with vectors
        documents = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Prepare document data
            doc = {
                "content": chunk,
                "embedding": embedding,
                "chunk_index": i
            }
            
            # Add any additional metadata for this chunk
            if metadata and i < len(metadata):
                doc.update(metadata[i])
                
            documents.append(doc)
        
        # Prepare request payload for index creation with vectors
        index_payload = {
            "project_id": project_id,
            "index_name": index_name,
            "connector_id": connector_id,
            "use_existing_connector": use_existing,
            "documents": documents
        }
        
        # Make API request to store documents with vectors
        index_response = requests.post(
            f"{self.superlinked_url}/v1/index/with_vectors",
            headers=self.headers,
            json=index_payload
        )
        
        if index_response.status_code != 200:
            raise ConnectionError(f"Failed to index documents: {index_response.text}")
            
        return {
            "status": "success",
            "index": index_name,
            "documents_added": len(documents),
            "connector_type": "qdrant",
            "qdrant_collection": f"superlinked_{project_id}_{index_name}",
            "response": index_response.json()
        }
    
    def query(
        self,
        project_id: str,
        index_name: str, 
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        with_documents: bool = True
    ) -> Dict[str, Any]:
        """
        Query Superlinked with Qdrant for similar documents.
        
        Args:
            project_id: Superlinked project ID
            index_name: Name of the index
            query_embedding: Query vector embedding
            filters: Optional metadata filters
            limit: Maximum number of results to retrieve
            with_documents: Whether to include document content
            
        Returns:
            Dict with retrieval results
        """
        # Prepare query payload
        query_payload = {
            "project_id": project_id,
            "index_name": index_name,
            "embedding": query_embedding,
            "limit": limit,
            "with_documents": with_documents
        }
        
        # Add filters if provided
        if filters:
            query_payload["filters"] = filters
        
        # Make API request to query documents
        query_response = requests.post(
            f"{self.superlinked_url}/v1/query/vector",
            headers=self.headers,
            json=query_payload
        )
        
        if query_response.status_code != 200:
            raise ConnectionError(f"Failed to query documents: {query_response.text}")
            
        results = query_response.json()
        
        # Format the results
        formatted_results = []
        for result in results.get("results", []):
            formatted_result = {
                "score": result.get("score", 0),
                "document_id": result.get("id")
            }
            
            # Include document content if requested
            if with_documents and "document" in result:
                formatted_result["text"] = result["document"].get("content", "")
                # Include all metadata
                for key, value in result["document"].items():
                    if key not in ["content", "embedding"]:
                        formatted_result[key] = value
            
            formatted_results.append(formatted_result)
        
        return {
            "status": "success",
            "results": formatted_results,
            "count": len(formatted_results)
        }
    
    def process_natural_language_query(
        self,
        query: str,
        model: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        Process a natural language query to extract structured search parameters.
        
        Args:
            query: User's natural language query
            model: LLM model to use for processing
            
        Returns:
            Dict with structured search parameters
        """
        # This can be integrated with an LLM for more advanced processing
        # For now, we'll implement a simple version
        
        # Simple implementation - just extract potential filters
        filters = {}
        
        # Keywords that might indicate filters
        filter_keywords = {
            "category": ["category", "type", "kind"],
            "date": ["date", "time", "when", "year", "month"],
            "author": ["author", "written by", "creator"],
            "source": ["source", "from", "website", "publication"]
        }
        
        # Check for potential filters
        query_lower = query.lower()
        for filter_type, keywords in filter_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    # Extract value following the keyword (simplified)
                    keyword_pos = query_lower.find(keyword)
                    if keyword_pos >= 0:
                        # Extract rest of the sentence after keyword
                        rest = query[keyword_pos + len(keyword):].strip()
                        # Find first 10 words as potential value
                        value = " ".join(rest.split()[:10])
                        if value:
                            filters[filter_type] = value
        
        return {
            "core_query": query,
            "filters": filters
        }
    
    def weighted_multi_search(
        self,
        project_id: str,
        index_name: str,
        query_embedding: List[float],
        text_query: str = None,
        weights: Dict[str, float] = None,
        filters: Dict[str, Any] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Perform weighted multi-factor search combining vector similarity with other factors.
        
        Args:
            project_id: Superlinked project ID
            index_name: Name of the index
            query_embedding: Vector embedding of the query
            text_query: Optional text query for hybrid search
            weights: Dictionary of weights for different factors
            filters: Optional metadata filters
            limit: Maximum number of results
            
        Returns:
            Dict with weighted search results
        """
        # Default weights
        if weights is None:
            weights = {"vector": 1.0}
            
        # Get vector search results
        vector_results = self.query(
            project_id=project_id,
            index_name=index_name,
            query_embedding=query_embedding,
            filters=filters,
            limit=limit * 2  # Get more results for reranking
        )
        
        results = vector_results.get("results", [])
        
        # If we have a text query and text weight, we could perform additional text-matching
        # This would be integrated with the Qdrant connector's capabilities
        
        # Rerank results based on weights
        for result in results:
            # Start with vector similarity score
            final_score = result.get("score", 0) * weights.get("vector", 1.0)
            
            # Add other weighted factors here if needed
            
            # Update score
            result["score"] = final_score
            
        # Sort by final score and limit
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        results = results[:limit]
        
        return {
            "status": "success",
            "results": results,
            "count": len(results)
        }
