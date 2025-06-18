"""
RAG Service - Business logic layer for document retrieval and response generation.

This module handles all the core RAG functionality separate from the UI.
"""

import time
import asyncio
import openai
from typing import Dict, List, Optional, Generator, Tuple
from dataclasses import dataclass
from temporalio.client import Client
try:
    from .config import Config
except ImportError:
    # Fallback for when running tests from workspace root
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from config import Config


@dataclass
class RetrievalResult:
    """Data class for retrieval results"""
    context: str
    chunks: List[Dict]
    total_results: int
    collection_name: str
    processing_time: float
    query: str
    status: str
    error: Optional[str] = None


@dataclass
class ResponseMetrics:
    """Data class for response metrics"""
    response_time: float
    token_count: int
    collection_used: str
    retrieval_result: RetrievalResult
    error: Optional[str] = None


class TemporalService:
    """Service for interacting with Temporal workflows"""
    
    def __init__(self, config: Config, host: str = None, namespace: str = None):
        self.config = config
        self.host = host or config.temporal.host
        self.namespace = namespace or config.temporal.namespace
    
    async def retrieve_documents(self, query: str, collection: str) -> RetrievalResult:
        """
        Retrieve documents using GenericPipelineWorkflow with document_retrieval pipeline.
        
        Args:
            query: Search query
            collection: Document collection name
            
        Returns:
            RetrievalResult with context and metadata
        """
        try:
            print(f"🔧 TEMPORAL: Starting retrieval for query='{query}', collection='{collection}'")
            
            # Connect to Temporal
            client = await Client.connect(self.host, namespace=self.namespace)
            print(f"🔧 TEMPORAL: Connected to {self.host}")
            
            # Start workflow
            workflow_args = ["document_retrieval", {"query": query, "top_k": 5, "collection": collection}]
            workflow_handle = await client.start_workflow(
                self.config.temporal.workflow_name,
                args=workflow_args,
                id=f"gradio-retrieval-{int(time.time() * 1000)}",
                task_queue=self.config.temporal.task_queue
            )
            
            print(f"🔧 TEMPORAL: Workflow started, waiting for result...")
            result = await workflow_handle.result()
            
            print(f"🔧 TEMPORAL: Got result type: {type(result)}")
            return self._parse_workflow_result(result, query, collection)
            
        except Exception as e:
            print(f"❌ TEMPORAL: Error retrieving documents: {str(e)}")
            import traceback
            traceback.print_exc()
            return RetrievalResult(
                context=f"Error retrieving context: {str(e)}",
                chunks=[],
                total_results=0,
                collection_name=collection,
                processing_time=0,
                query=query,
                status="error",
                error=str(e)
            )
    
    def _parse_workflow_result(self, result, query: str, collection: str) -> RetrievalResult:
        """Parse workflow result into RetrievalResult"""
        
        # Handle different result formats
        search_data = None
        
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            # Direct list format
            search_data = result[0]
            print(f"🔧 TEMPORAL: Found direct list result format")
        elif result.get("status") == "completed" and "final_result" in result:
            # Legacy wrapper format
            search_data = result["final_result"]
            print(f"🔧 TEMPORAL: Found legacy wrapper format")
        elif result.get("status") == "success" and "retrieved_documents" in result:
            # Direct success format
            search_data = result
            print(f"🔧 TEMPORAL: Found direct success format")
        
        if not search_data or search_data.get("status") != "success":
            print(f"❌ TEMPORAL: No valid search data found")
            return RetrievalResult(
                context="No relevant context found.",
                chunks=[],
                total_results=0,
                collection_name=collection,
                processing_time=0,
                query=query,
                status="no_results"
            )
        
        # Extract documents
        retrieved_documents = search_data.get("retrieved_documents", [])
        if not retrieved_documents:
            print(f"❌ TEMPORAL: No documents in search result")
            return RetrievalResult(
                context="No relevant context found.",
                chunks=[],
                total_results=0,
                collection_name=search_data.get("collection_name", collection),
                processing_time=search_data.get("processing_time", 0),
                query=search_data.get("query", query),
                status="no_results"
            )
        
        # Format results
        contexts = []
        chunks = []
        
        for i, doc in enumerate(retrieved_documents):
            content = doc.get("text", "")
            contexts.append(f"Context {i+1}: {content}")
            chunks.append({
                "id": doc.get("id", ""),
                "score": doc.get("score", 0),
                "text": content[:200] + "..." if len(content) > 200 else content
            })
        
        formatted_context = "\n\n".join(contexts)
        
        return RetrievalResult(
            context=formatted_context,
            chunks=chunks,
            total_results=len(chunks),
            collection_name=search_data.get("collection_name", collection),
            processing_time=search_data.get("processing_time", 0),
            query=search_data.get("query", query),
            status="success"
        )


class OpenAIService:
    """Service for OpenAI chat completions"""
    
    def __init__(self, config: Config, api_key: str = None):
        self.config = config
        self.api_key = api_key or config.openai.api_key
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def stream_chat_completion(
        self,
        query: str,
        context: str,
        history: List[Tuple[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: str = None
    ) -> Generator[str, None, None]:
        """
        Stream chat completion from OpenAI
        
        Args:
            query: User query
            context: Retrieved context
            history: Chat history
            temperature: Response creativity
            max_tokens: Maximum response length
            model: OpenAI model to use
            
        Yields:
            String chunks of the response
        """
        
        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": f"""You are a helpful assistant that answers questions based on the provided context.

Context from documents:
{context}

Instructions:
- Answer based primarily on the provided context
- If the context doesn't contain relevant information, say so clearly
- Be concise but comprehensive
- Cite specific parts of the context when relevant
- If no context is provided, explain that no document context is available"""
            }
        ]
        
        # Add conversation history (last 5 exchanges)
        for user_msg, assistant_msg in history[-5:]:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Create streaming response
        stream = self.client.chat.completions.create(
            model=model or self.config.openai.default_model,
            messages=messages,
            stream=True,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content


class RAGService:
    """Main RAG service that orchestrates retrieval and generation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.temporal_service = TemporalService(config)
        self.openai_service = OpenAIService(config)
    
    def retrieve_documents_sync(self, query: str, collection: str) -> RetrievalResult:
        """Synchronous wrapper for document retrieval"""
        return asyncio.run(self.temporal_service.retrieve_documents(query, collection))
    
    def stream_rag_response(
        self,
        query: str,
        history: List[Tuple[str, str]],
        collection: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Generator[Tuple[str, List[Tuple[str, str]], ResponseMetrics], None, None]:
        """
        Stream RAG response with metrics
        
        Args:
            query: User query
            history: Chat history
            collection: Document collection
            temperature: Response creativity
            max_tokens: Maximum response length
            
        Yields:
            Tuple of (current_message, updated_history, metrics)
        """
        
        start_time = time.time()
        response_text = ""
        token_count = 0
        
        # Get context
        print(f"🔍 RAG: Starting retrieval for query='{query}', collection='{collection}'")
        retrieval_result = self.retrieve_documents_sync(query, collection)
        
        print(f"🔍 RAG: Retrieved {retrieval_result.total_results} chunks, status: {retrieval_result.status}")
        
        # Check if retrieval was successful
        if retrieval_result.status == "error":
            error_metrics = ResponseMetrics(
                response_time=round(time.time() - start_time, 2),
                token_count=0,
                collection_used=collection,
                retrieval_result=retrieval_result,
                error=retrieval_result.error
            )
            updated_history = history + [[query, f"Error: {retrieval_result.error}"]]
            yield "", updated_history, error_metrics
            return
        
        # Use fallback context if no results
        context = retrieval_result.context
        if retrieval_result.status == "no_results" or not context or context == "No relevant context found.":
            print("⚠️  RAG: Using fallback context")
            context = "No relevant document context available."
        
        try:
            # Stream response from OpenAI
            for content_chunk in self.openai_service.stream_chat_completion(
                query=query,
                context=context,
                history=history,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                response_text += content_chunk
                token_count += 1
                
                # Calculate metrics
                elapsed_time = time.time() - start_time
                metrics = ResponseMetrics(
                    response_time=round(elapsed_time, 2),
                    token_count=token_count,
                    collection_used=collection,
                    retrieval_result=retrieval_result
                )
                
                # Yield updated chat history
                updated_history = history + [[query, response_text]]
                yield "", updated_history, metrics
                
        except Exception as e:
            print(f"❌ RAG: OpenAI error: {str(e)}")
            error_response = f"Error generating response: {str(e)}"
            error_metrics = ResponseMetrics(
                response_time=round(time.time() - start_time, 2),
                token_count=0,
                collection_used=collection,
                retrieval_result=retrieval_result,
                error=str(e)
            )
            updated_history = history + [[query, error_response]]
            yield "", updated_history, error_metrics
    
    async def process_query(self, query: str, collection: str = "ai_documents") -> Dict:
        """
        Process a query through the complete RAG pipeline.
        
        Args:
            query: User query string
            collection: Collection to search in
            
        Returns:
            Dict with response, sources, and metadata
        """
        try:
            # Retrieve relevant documents
            retrieval_result = await self.temporal_service.retrieve_documents(query, collection)
            
            if retrieval_result.status != "success":
                return {
                    "response": f"Search failed: {retrieval_result.error}",
                    "sources": [],
                    "metadata": {
                        "status": "error",
                        "error": retrieval_result.error
                    }
                }
            
            # Generate response using OpenAI
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Use the provided context to answer questions accurately."},
                {"role": "user", "content": f"Context: {retrieval_result.context}\n\nQuestion: {query}"}
            ]
            
            response_text = ""
            for chunk in self.openai_service.stream_chat_completion(messages):
                response_text += chunk
            
            return {
                "response": response_text,
                "sources": retrieval_result.chunks,
                "metadata": {
                    "status": "success",
                    "collection": collection,
                    "num_sources": len(retrieval_result.chunks)
                }
            }
            
        except Exception as e:
            return {
                "response": f"An error occurred: {str(e)}",
                "sources": [],
                "metadata": {
                    "status": "error",
                    "error": str(e)
                }
            }


class SystemStatusService:
    """Service for checking system status"""
    
    def __init__(self, config: Config):
        self.config = config
        self.temporal_service = TemporalService(config)
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        status = {}
        
        # OpenAI API Key
        if self.config.openai.api_key:
            status["OpenAI"] = "✅ API Key Set"
        else:
            status["OpenAI"] = "❌ No API Key"
        
        # Temporal configuration
        status["Temporal Host"] = f"✅ Configured: {self.temporal_service.host}"
        status["Temporal Namespace"] = f"✅ {self.temporal_service.namespace}"
        status["System"] = "✅ Temporal-based Architecture"
        
        return status
    
    def get_architecture_info(self) -> Dict:
        """Get architecture information"""
        return {
            "Architecture": "✅ Pure Temporal Workflows",
            "Chat Interface": "✅ Gradio + Temporal Client",
            "Orchestration": "✅ GenericPipelineWorkflow",
            "Activities": "✅ Embedding + Retriever Services",
            "Database": "✅ Qdrant Vector Store",
            "Monitoring": "✅ Temporal UI (port 8081)"
        }
    
    async def test_temporal_connection(self) -> Dict:
        """Test connectivity to Temporal server"""
        try:
            await Client.connect(self.temporal_service.host, namespace=self.temporal_service.namespace)
            return {
                "status": "✅ Connected",
                "host": self.temporal_service.host,
                "namespace": self.temporal_service.namespace
            }
        except Exception as e:
            return {
                "status": f"❌ {str(e)}",
                "host": self.temporal_service.host,
                "namespace": self.temporal_service.namespace
            }
    
    def test_temporal_connection_sync(self) -> Dict:
        """Synchronous wrapper for Temporal connection test"""
        try:
            return asyncio.run(self.test_temporal_connection())
        except Exception as e:
            return {
                "status": f"❌ {str(e)}",
                "host": self.temporal_service.host,
                "namespace": self.temporal_service.namespace
            }
