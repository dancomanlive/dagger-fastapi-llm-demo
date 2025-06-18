"""
Test the dynamic activity loading capability.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service_config import ServiceConfig
from pipeline_executor import PipelineExecutor


class TestDynamicActivityLoading:
    """Test dynamic activity loading in PipelineExecutor."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config_content = """
services:
  local_activities:
    test_local_activity:
      timeout_minutes: 5
      retry_attempts: 3
      retry_initial_interval_seconds: 1
      retry_maximum_interval_seconds: 30
    
    another_local_activity:
      timeout_minutes: 2
      retry_attempts: 2

  remote_service:
    task_queue: "remote-queue"
    activities:
      test_remote_activity:
        timeout_minutes: 10
        retry_attempts: 3

pipelines:
  test_pipeline:
    name: "TestPipeline"
    steps:
      - activity: "test_local_activity"
        type: "local"
      - activity: "test_remote_activity"
        type: "remote"
        service: "remote_service"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            
            yield ServiceConfig(f.name)
            
            os.unlink(f.name)
    
    def test_local_activity_config_detection(self, mock_config):
        """Test that local activities are properly detected from config."""
        # Test that local activities are identified correctly
        test_activity_config = mock_config.get_activity_config("test_local_activity")
        assert test_activity_config is not None
        assert test_activity_config["type"] == "local"
        assert test_activity_config["service_name"] == "local"
        assert test_activity_config["timeout_minutes"] == 5
        
        another_activity_config = mock_config.get_activity_config("another_local_activity")
        assert another_activity_config is not None
        assert another_activity_config["type"] == "local"
        assert another_activity_config["timeout_minutes"] == 2
        
        # Test remote activity for comparison
        remote_activity_config = mock_config.get_activity_config("test_remote_activity")
        assert remote_activity_config is not None
        assert remote_activity_config["type"] == "remote"
        assert remote_activity_config["task_queue"] == "remote-queue"
    
    def test_all_configured_local_activities_detected(self):
        """Test that all local activities from real config are detected."""
        # Test with the real config file
        test_dir = os.path.dirname(__file__)
        service_dir = os.path.dirname(test_dir)
        config_path = os.path.join(service_dir, "config", "services.yaml")
        
        if os.path.exists(config_path):
            config = ServiceConfig(config_path)
            
            # Get all local activities from config
            local_activities = config.get_service_config("local_activities")
            assert local_activities is not None
            
            # Test each local activity is properly configured
            for activity_name in local_activities:
                if activity_name == "task_queue":  # Skip non-activity keys
                    continue
                    
                activity_config = config.get_activity_config(activity_name)
                assert activity_config is not None, f"Activity {activity_name} should be found"
                assert activity_config["type"] == "local", f"Activity {activity_name} should be local"
                assert "timeout_minutes" in activity_config, f"Activity {activity_name} should have timeout"
                assert "retry_attempts" in activity_config, f"Activity {activity_name} should have retry config"
        else:
            pytest.skip("Real config file not found")
    
    def test_dynamic_activity_name_resolution(self, mock_config):
        """Test that activity names can be resolved dynamically from configuration."""
        with patch('service_config._service_config', mock_config):
            executor = PipelineExecutor()
            
            # Test that we can get config for various activity types
            local_config = executor.config.get_activity_config("test_local_activity")
            assert local_config["type"] == "local"
            
            remote_config = executor.config.get_activity_config("test_remote_activity")
            assert remote_config["type"] == "remote"
            assert remote_config["task_queue"] == "remote-queue"
            
            # Test nonexistent activity
            missing_config = executor.config.get_activity_config("nonexistent_activity")
            assert missing_config is None
    
    def test_input_transform_with_configured_activities(self, mock_config):
        """Test input transformation works with configured activities."""
        with patch('service_config._service_config', mock_config):
            executor = PipelineExecutor()
            
            # Test various transforms still work
            test_data = {"test": "data"}
            
            result = executor.transform_input("passthrough", test_data)
            assert result == [test_data]
            
            documents = [{"id": "1", "text": "test"}]
            result = executor.transform_input("documents", documents)
            # After normalization, documents transform returns the normalized list directly
            assert result == documents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
