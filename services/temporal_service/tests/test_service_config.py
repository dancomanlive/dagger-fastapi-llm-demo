"""
Unit tests for the generic temporal service configuration and pipeline logic.

These tests validate the configuration loading, service discovery, and pipeline
definition parsing without requiring a running Temporal server.
"""

import pytest
import os
import tempfile
from unittest.mock import patch
from datetime import timedelta
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from service_config import ServiceConfig
from pipeline_executor import PipelineExecutor


class TestServiceConfig:
    """Test the ServiceConfig class."""
    
    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config_content = """
services:
  test_service:
    task_queue: "test-queue"
    activities:
      test_activity:
        timeout_minutes: 5
        retry_attempts: 3
        retry_initial_interval_seconds: 1
        retry_maximum_interval_seconds: 30

  local_activities:
    local_test_activity:
      timeout_minutes: 2
      retry_attempts: 2

pipelines:
  test_pipeline:
    name: "TestPipeline"
    description: "A test pipeline"
    steps:
      - activity: "local_test_activity"
        type: "local"
        input_transform: "passthrough"
      - activity: "test_activity"
        type: "remote"
        service: "test_service"
        input_transform: "documents"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            
            try:
                config = ServiceConfig(f.name)
                
                # Test service loading
                services = config.get_services()
                assert "test_service" in services
                assert "local_activities" in services
                
                # Test service config
                service_config = config.get_service_config("test_service")
                assert service_config["task_queue"] == "test-queue"
                assert "test_activity" in service_config["activities"]
                
                # Test activity config
                activity_config = config.get_activity_config("test_activity")
                assert activity_config["type"] == "remote"
                assert activity_config["service_name"] == "test_service"
                assert activity_config["task_queue"] == "test-queue"
                assert activity_config["timeout_minutes"] == 5
                
                # Test local activity config
                local_activity_config = config.get_activity_config("local_test_activity")
                assert local_activity_config["type"] == "local"
                assert local_activity_config["service_name"] == "local"
                assert local_activity_config["timeout_minutes"] == 2
                
                # Test pipeline config
                pipeline_config = config.get_pipeline_config("test_pipeline")
                assert pipeline_config["name"] == "TestPipeline"
                assert len(pipeline_config["steps"]) == 2
                assert pipeline_config["steps"][0]["activity"] == "local_test_activity"
                assert pipeline_config["steps"][1]["activity"] == "test_activity"
                
            finally:
                os.unlink(f.name)
    
    def test_missing_config_file(self):
        """Test handling of missing configuration file."""
        with pytest.raises(FileNotFoundError):
            ServiceConfig("/nonexistent/path.yaml")
    
    def test_invalid_yaml(self):
        """Test handling of invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            
            try:
                with pytest.raises(Exception):  # YAML parsing error
                    ServiceConfig(f.name)
            finally:
                os.unlink(f.name)
    
    def test_retry_policy_creation(self):
        """Test retry policy creation from config."""
        config_content = """
services:
  test_service:
    activities:
      test_activity:
        timeout_minutes: 10
        retry_attempts: 5
        retry_initial_interval_seconds: 2
        retry_maximum_interval_seconds: 60
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            
            try:
                config = ServiceConfig(f.name)
                activity_config = config.get_activity_config("test_activity")
                
                retry_policy = config.get_retry_policy(activity_config)
                assert retry_policy.initial_interval == timedelta(seconds=2)
                assert retry_policy.maximum_interval == timedelta(seconds=60)
                assert retry_policy.maximum_attempts == 5
                
                timeout = config.get_timeout(activity_config)
                assert timeout == timedelta(minutes=10)
                
            finally:
                os.unlink(f.name)
    
    def test_missing_activity(self):
        """Test behavior when activity is not found."""
        config_content = """
services:
  test_service:
    activities:
      existing_activity:
        timeout_minutes: 5
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            
            try:
                config = ServiceConfig(f.name)
                
                # Should return None for missing activity
                assert config.get_activity_config("nonexistent_activity") is None
                
            finally:
                os.unlink(f.name)


class TestPipelineExecutor:
    """Test the PipelineExecutor class."""
    
    def test_input_transforms(self):
        """Test input transformation methods."""
        executor = PipelineExecutor()
        
        # Test documents transform
        documents = [{"id": "1", "text": "test"}]
        result = executor.transform_input("documents", documents)
        assert result == documents  # Now returns flat list, not nested
        
        # Test chunked_docs_with_collection transform
        chunks = [{"id": "chunk1", "text": "test chunk"}]
        result = executor.transform_input("chunked_docs_with_collection", chunks)
        # Use the actual collection name from environment or default
        expected_collection = executor.document_collection_name
        assert result == [chunks, expected_collection]
        
        # Test query_with_collection transform
        query_data = {"query": "test query", "top_k": 5}
        result = executor.transform_input("query_with_collection", query_data)
        assert result == ["test query", expected_collection, 5]
        
        # Test passthrough transform
        data = {"some": "data"}
        result = executor.transform_input("passthrough", data)
        assert result == [data]
        
        # Test default transform
        data = "simple string"
        result = executor.transform_input("unknown_transform", data)
        assert result == [data]
    
    def test_input_transforms_with_env_var(self):
        """Test input transforms with custom collection name."""
        with patch.dict(os.environ, {"DOCUMENT_COLLECTION_NAME": "custom_collection"}):
            executor = PipelineExecutor()
            
            chunks = [{"id": "chunk1"}]
            result = executor.transform_input("chunked_docs_with_collection", chunks)
            assert result == [chunks, "custom_collection"]
            
            query_data = {"query": "test", "top_k": 3}
            result = executor.transform_input("query_with_collection", query_data)
            assert result == ["test", "custom_collection", 3]
    
    def test_query_transform_with_string_input(self):
        """Test query transform with plain string input."""
        executor = PipelineExecutor()
        
        # Test with plain string
        result = executor.transform_input("query_with_collection", "simple query")
        expected_collection = executor.document_collection_name
        assert result == ["simple query", expected_collection, 10]  # Default top_k
    
    def test_query_transform_edge_cases(self):
        """Test query transform with edge cases."""
        executor = PipelineExecutor()
        expected_collection = executor.document_collection_name
        
        # Test with missing top_k
        query_data = {"query": "test query"}
        result = executor.transform_input("query_with_collection", query_data)
        assert result == ["test query", expected_collection, 10]  # Default top_k
        
        # Test with empty query
        query_data = {"query": "", "top_k": 15}
        result = executor.transform_input("query_with_collection", query_data)
        assert result == ["", expected_collection, 15]


class TestConfigIntegration:
    """Test integration between ServiceConfig and PipelineExecutor."""
    
    def test_real_config_loading(self):
        """Test loading the actual services.yaml config file."""
        # This tests with the real config file
        test_dir = os.path.dirname(__file__)
        service_dir = os.path.dirname(test_dir)
        config_path = os.path.join(service_dir, "config", "services.yaml")
        
        if os.path.exists(config_path):
            config = ServiceConfig(config_path)
            
            # Test that expected services exist
            services = config.get_services()
            assert "embedding_service" in services
            assert "retrieval_service" in services
            assert "local_activities" in services
            
            # Test that expected activities exist
            assert config.get_activity_config("perform_embedding_and_indexing_activity") is not None
            assert config.get_activity_config("search_documents_activity") is not None
            assert config.get_activity_config("chunk_documents_activity") is not None
            assert config.get_activity_config("health_check_activity") is not None
            
            # Test that expected pipelines exist
            pipelines = config.get_pipelines()
            assert "document_processing" in pipelines
            assert "document_retrieval" in pipelines
            assert "health_check" in pipelines
            
            # Test pipeline structure
            doc_pipeline = config.get_pipeline_config("document_processing")
            assert "steps" in doc_pipeline
            assert len(doc_pipeline["steps"]) >= 2  # At least chunking and embedding
        else:
            pytest.skip(f"Real config file not found at {config_path}, skipping integration test")


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
