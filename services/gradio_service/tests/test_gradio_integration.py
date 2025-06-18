"""
Integration tests for Gradio Service

Tests the integration between Gradio UI components, RAG service,
and external dependencies to ensure the complete user flow works correctly.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules for testing
from config import Config
from rag_service import RAGService
from gradio_ui import GradioInterface


class TestGradioServiceIntegration:
    """Integration tests for the complete Gradio service flow"""
    
    def test_gradio_config_integration(self):
        """Test that Gradio configuration integrates properly with all components"""
        config = Config()
        
        # Verify config has all required attributes for integration
        assert hasattr(config, 'ui')
        assert hasattr(config, 'temporal')
        assert hasattr(config, 'openai')
        assert hasattr(config.ui, 'title')
        assert hasattr(config.ui, 'description')
        
        # Verify configuration can be used by other components
        rag_service = RAGService(config)
        assert rag_service.config == config
    
    @pytest.mark.asyncio
    @patch('rag_service.Client')
    async def test_rag_service_full_pipeline_integration(self, mock_client_class):
        """Test the complete RAG pipeline integration"""
        # Setup mocks for Temporal workflow
        mock_client = MagicMock()
        mock_client_class.connect = AsyncMock(return_value=mock_client)
        
        # Mock workflow execution
        mock_workflow_handle = MagicMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_workflow_handle)
        
        # Mock workflow result (document retrieval)
        mock_workflow_result = {
            "status": "success",
            "retrieved_documents": [
                {
                    "id": "doc1_chunk1", 
                    "text": "This is a relevant document chunk about AI",
                    "score": 0.95,
                    "metadata": {"source": "doc1"}
                }
            ]
        }
        mock_workflow_handle.result = AsyncMock(return_value=mock_workflow_result)
        
        # Test the RAG service
        config = Config()
        rag_service = RAGService(config)
        
        # Mock OpenAI streaming response
        with patch.object(rag_service.openai_service, 'stream_chat_completion') as mock_openai:
            mock_openai.return_value = ["This ", "is ", "a ", "test ", "response."]
            
            # Test query processing
            test_query = "What is artificial intelligence?"
            result = await rag_service.process_query(test_query)
        
        # Verify the complete pipeline worked
        assert isinstance(result, dict)
        assert "response" in result
        assert "sources" in result
        assert "metadata" in result
        assert result["metadata"]["status"] == "success"
        assert len(result["sources"]) > 0
        assert "test response" in result["response"]
        
        # Verify Temporal workflow was called
        mock_client.start_workflow.assert_called_once()
        mock_workflow_handle.result.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('rag_service.Client')
    async def test_error_handling_integration(self, mock_client_class):
        """Test error handling across the integrated system"""
        # Setup mock for Temporal workflow failure
        mock_client = MagicMock()
        mock_client_class.connect = AsyncMock(return_value=mock_client)
        
        # Mock workflow execution that fails
        mock_workflow_handle = MagicMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_workflow_handle)
        mock_workflow_handle.result = AsyncMock(side_effect=Exception("Temporal workflow failed"))
        
        config = Config()
        rag_service = RAGService(config)
        
        # Test that errors are handled gracefully
        result = await rag_service.process_query("test query")
        
        # Should return error response instead of raising exception
        assert isinstance(result, dict)
        assert "error" in result or "response" in result
        
        # If error is in response text, that's also acceptable
        if "response" in result:
            response_lower = result["response"].lower()
            assert any(keyword in response_lower for keyword in ["error", "unavailable", "failed"])
    
    @patch('gradio_ui.gr')
    def test_gradio_interface_integration(self, mock_gradio):
        """Test Gradio interface integration with RAG service"""
        # Mock Gradio components
        mock_interface = MagicMock()
        mock_gradio.Blocks.return_value = mock_interface
        mock_gradio.Textbox.return_value = MagicMock()
        mock_gradio.HTML.return_value = MagicMock()
        mock_gradio.Button.return_value = MagicMock()
        mock_gradio.Row.return_value.__enter__.return_value = MagicMock()
        mock_gradio.Row.return_value.__exit__.return_value = None
        mock_gradio.Column.return_value.__enter__.return_value = MagicMock()
        mock_gradio.Column.return_value.__exit__.return_value = None
        mock_gradio.Tab.return_value.__enter__.return_value = MagicMock()
        mock_gradio.Tab.return_value.__exit__.return_value = None
        
        config = Config()
        rag_service = RAGService(config)
        gradio_interface = GradioInterface(rag_service, config)
        
        # Verify interface was created
        assert gradio_interface.rag_service == rag_service
        assert gradio_interface.config == config
        
        # Test that we can create the app
        app = gradio_interface.create_app()
        assert app is not None
        
        # Verify Gradio components were used
        mock_gradio.Blocks.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('rag_service.Client')
    @patch('gradio_ui.gr')
    async def test_end_to_end_user_flow(self, mock_gradio, mock_client_class):
        """Test the complete end-to-end user flow"""
        # Setup mocks for Temporal workflow
        mock_client = MagicMock()
        mock_client_class.connect = AsyncMock(return_value=mock_client)
        
        # Mock workflow execution
        mock_workflow_handle = MagicMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_workflow_handle)
        
        # Mock successful workflow result
        mock_workflow_result = {
            "status": "success",
            "retrieved_documents": [
                {
                    "id": "doc1_chunk1",
                    "text": "Artificial intelligence (AI) is the simulation of human intelligence in machines.",
                    "score": 0.92,
                    "metadata": {"source": "ai_textbook.pdf", "page": 1}
                }
            ]
        }
        mock_workflow_handle.result = AsyncMock(return_value=mock_workflow_result)
        
        # Mock Gradio interface
        mock_interface = MagicMock()
        mock_gradio.Blocks.return_value = mock_interface
        mock_gradio.Textbox.return_value = MagicMock()
        mock_gradio.HTML.return_value = MagicMock()
        mock_gradio.Button.return_value = MagicMock()
        mock_gradio.Row.return_value.__enter__.return_value = MagicMock()
        mock_gradio.Row.return_value.__exit__.return_value = None
        
        # Create the complete system
        config = Config()
        rag_service = RAGService(config)
        gradio_interface = GradioInterface(rag_service, config)
        
        # Mock OpenAI streaming response
        with patch.object(rag_service.openai_service, 'stream_chat_completion') as mock_openai:
            mock_openai.return_value = ["Artificial ", "intelligence ", "is ", "the ", "simulation ", "of ", "human ", "intelligence."]
            
            # Simulate user input
            user_query = "What is artificial intelligence?"
            
            # Process the query through the RAG service
            result = await rag_service.process_query(user_query)
        
        # Verify the complete flow worked
        assert isinstance(result, dict)
        assert "response" in result
        assert "sources" in result
        assert "metadata" in result
        assert result["metadata"]["status"] == "success"
        
        # Verify the response contains relevant information
        response_text = result["response"]
        assert len(response_text) > 0
        assert "intelligence" in response_text
        
        # Verify sources are properly formatted
        sources = result["sources"]
        assert isinstance(sources, list)
        assert len(sources) > 0
        for source in sources:
            assert isinstance(source, dict)
            assert "id" in source or "text" in source
    
    def test_configuration_validation_integration(self):
        """Test that configuration validation works across all components"""
        config = Config()
        
        # Test that configuration is valid for all components
        rag_service = RAGService(config)
        gradio_interface = GradioInterface(rag_service, config)
        
        # Verify all components can access configuration
        assert rag_service.config.temporal.host is not None
        assert rag_service.config.temporal.namespace is not None
        assert gradio_interface.config.ui.title is not None
        assert gradio_interface.config.ui.description is not None
    
    @pytest.mark.asyncio
    @patch('rag_service.Client')
    async def test_service_timeout_handling(self, mock_client_class):
        """Test timeout handling in service integration"""
        # Setup mock for Temporal workflow timeout
        mock_client = MagicMock()
        mock_client_class.connect = AsyncMock(return_value=mock_client)
        
        # Mock workflow execution that times out
        mock_workflow_handle = MagicMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_workflow_handle)
        
        # Simulate timeout exception
        import asyncio
        mock_workflow_handle.result = AsyncMock(side_effect=asyncio.TimeoutError("Workflow timed out"))
        
        config = Config()
        rag_service = RAGService(config)
        
        # Test that timeouts are handled gracefully
        result = await rag_service.process_query("test query")
        
        # Should return a graceful error response
        assert isinstance(result, dict)
        assert "response" in result
        # Response should indicate the issue without crashing
        assert len(result["response"]) > 0


class TestGradioServicePerformance:
    """Performance and load testing for Gradio service integration"""
    
    @pytest.mark.asyncio
    @patch('rag_service.Client')
    async def test_concurrent_query_handling(self, mock_client_class):
        """Test handling of concurrent queries"""
        # Setup fast mock responses
        mock_client = MagicMock()
        mock_client_class.connect = AsyncMock(return_value=mock_client)
        
        # Mock workflow execution
        mock_workflow_handle = MagicMock()
        mock_client.start_workflow = AsyncMock(return_value=mock_workflow_handle)
        
        # Mock fast workflow result
        mock_workflow_result = {
            "status": "success",
            "retrieved_documents": [
                {"id": "test", "text": "Test result", "score": 0.8}
            ]
        }
        mock_workflow_handle.result = AsyncMock(return_value=mock_workflow_result)
        
        config = Config()
        rag_service = RAGService(config)
        
        # Mock OpenAI for fast responses
        with patch.object(rag_service.openai_service, 'stream_chat_completion') as mock_openai:
            mock_openai.return_value = ["Fast ", "response."]
            
            # Test multiple concurrent queries
            import asyncio
            queries = [f"Test query {i}" for i in range(5)]
            
            # Run queries concurrently
            tasks = [rag_service.process_query(query) for query in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all queries completed successfully
        assert len(results) == 5
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, dict)
            assert "response" in result
    
    @pytest.mark.asyncio
    @patch('rag_service.Client')
    async def test_large_response_handling(self, mock_client_class):
        """Test handling of large responses from services"""
        # Setup mock with large response
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create a large response with many results
        large_results = [
            {
                "id": f"doc{i}_chunk{j}",
                "text": f"This is chunk {j} from document {i} " * 20,  # Make text longer
                "score": 0.8 - (i * 0.01),
                "metadata": {"source": f"doc{i}.pdf", "chunk": j}
            }
            for i in range(10) for j in range(5)  # 50 results total
        ]
        
        large_response = MagicMock()
        large_response.status_code = 200
        large_response.json.return_value = {
            "results": large_results,
            "total_results": len(large_results),
            "query_time": 0.234
        }
        
        mock_client.post = AsyncMock(return_value=large_response)
        
        config = Config()
        rag_service = RAGService(config)
        
        # Test query with large response
        result = await rag_service.process_query("test query")
        
        # Verify the system handles large responses
        assert isinstance(result, dict)
        assert "response" in result
        assert "sources" in result
        
        # Response should be generated even with many sources
        assert len(result["response"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
