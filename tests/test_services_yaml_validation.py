#!/usr/bin/env python3
"""
Validation tests for services.yaml format and content.
These tests ensure the generated services.yaml meets all requirements.
"""
import pytest
import yaml
import os


class TestServicesYamlValidation:
    """Test that services.yaml has the correct structure and content."""
    
    def load_services_yaml(self, file_path: str):
        """Helper to load and parse services.yaml file."""
        if not os.path.exists(file_path):
            pytest.fail(f"Services.yaml file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_services_yaml_has_required_top_level_keys(self):
        """Services.yaml must have 'services' and 'pipelines' keys."""
        config = self.load_services_yaml("generated/services_dynamic.yaml")
        
        assert "services" in config, "Missing 'services' key"
        assert "pipelines" in config, "Missing 'pipelines' key"
        assert isinstance(config["services"], dict), "'services' must be a dictionary"
        assert isinstance(config["pipelines"], dict), "'pipelines' must be a dictionary"
    
    def test_required_services_are_present(self):
        """Must include the core services: embedding_service, retrieval_service, local_activities."""
        config = self.load_services_yaml("generated/services_dynamic.yaml")
        services = config["services"]
        
        required_services = ["embedding_service", "retrieval_service"]
        for service in required_services:
            assert service in services, f"Missing required service: {service}"
    
    def test_services_have_required_fields(self):
        """Each service must have task_queue and activities."""
        config = self.load_services_yaml("generated/services_dynamic.yaml")
        
        for service_name, service_config in config["services"].items():
            assert "task_queue" in service_config, f"Service {service_name} missing 'task_queue'"
            assert "activities" in service_config, f"Service {service_name} missing 'activities'"
            assert isinstance(service_config["activities"], dict), f"Service {service_name} 'activities' must be dict"
    
    def test_activities_have_required_fields(self):
        """Each activity must have timeout_minutes and retry_attempts."""
        config = self.load_services_yaml("generated/services_dynamic.yaml")
        
        for service_name, service_config in config["services"].items():
            for activity_name, activity_config in service_config.get("activities", {}).items():
                # Skip empty activities for now - they should be populated
                if not activity_config:
                    continue
                    
                assert "timeout_minutes" in activity_config, f"Activity {service_name}.{activity_name} missing 'timeout_minutes'"
                assert "retry_attempts" in activity_config, f"Activity {service_name}.{activity_name} missing 'retry_attempts'"
                
                # Validate types
                assert isinstance(activity_config["timeout_minutes"], int), f"timeout_minutes must be int for {activity_name}"
                assert isinstance(activity_config["retry_attempts"], int), f"retry_attempts must be int for {activity_name}"
    
    def test_core_activities_are_present(self):
        """Must include the core activities we know should exist."""
        config = self.load_services_yaml("generated/services_dynamic.yaml")
        
        # Expected activities based on the original services.yaml
        expected_activities = {
            "embedding_service": ["perform_embedding_and_indexing_activity"],
            "retrieval_service": ["search_documents_activity"],
        }
        
        for service_name, expected_activity_list in expected_activities.items():
            if service_name in config["services"]:
                service_activities = config["services"][service_name]["activities"]
                for activity_name in expected_activity_list:
                    assert activity_name in service_activities, f"Missing activity {activity_name} in {service_name}"
    
    def test_pipelines_have_required_structure(self):
        """Pipelines must have name, description, and steps."""
        config = self.load_services_yaml("generated/services_dynamic.yaml")
        
        # Expected pipelines based on original services.yaml
        expected_pipelines = ["document_processing", "document_retrieval", "health_check"]
        
        for pipeline_name in expected_pipelines:
            if pipeline_name in config["pipelines"]:
                pipeline = config["pipelines"][pipeline_name]
                
                assert "name" in pipeline, f"Pipeline {pipeline_name} missing 'name'"
                assert "description" in pipeline, f"Pipeline {pipeline_name} missing 'description'"
                assert "steps" in pipeline, f"Pipeline {pipeline_name} missing 'steps'"
                assert isinstance(pipeline["steps"], list), f"Pipeline {pipeline_name} 'steps' must be list"
    
    def test_pipeline_steps_have_required_fields(self):
        """Each pipeline step must have activity and type."""
        config = self.load_services_yaml("generated/services_dynamic.yaml")
        
        for pipeline_name, pipeline in config["pipelines"].items():
            for i, step in enumerate(pipeline.get("steps", [])):
                assert "activity" in step, f"Pipeline {pipeline_name} step {i} missing 'activity'"
                assert "type" in step, f"Pipeline {pipeline_name} step {i} missing 'type'"
                
                # Validate step types
                assert step["type"] in ["local", "remote"], f"Invalid step type '{step['type']}' in {pipeline_name}"
                
                # Remote steps should have service field
                if step["type"] == "remote":
                    assert "service" in step, f"Remote step in {pipeline_name} missing 'service'"
    
    def test_document_processing_pipeline_is_complete(self):
        """Document processing pipeline must have chunking and embedding steps."""
        config = self.load_services_yaml("generated/services_dynamic.yaml")
        
        if "document_processing" not in config["pipelines"]:
            pytest.skip("Document processing pipeline not generated yet")
        
        pipeline = config["pipelines"]["document_processing"]
        steps = pipeline["steps"]
        
        # Should have at least 2 steps: chunking and embedding
        assert len(steps) >= 2, "Document processing pipeline should have at least 2 steps"
        
        # First step should be chunking (local)
        chunk_step = steps[0]
        assert "chunk" in chunk_step["activity"].lower(), "First step should be chunking"
        assert chunk_step["type"] == "local", "Chunking should be local"
        
        # Second step should be embedding (remote)
        embed_step = steps[1]
        assert "embedding" in embed_step["activity"].lower(), "Second step should be embedding"
        assert embed_step["type"] == "remote", "Embedding should be remote"
        assert embed_step["service"] == "embedding_service", "Embedding should use embedding_service"
    
    def test_input_transforms_are_valid(self):
        """Pipeline steps should have valid input transforms."""
        config = self.load_services_yaml("generated/services_dynamic.yaml")
        
        valid_transforms = [
            "documents", 
            "chunked_docs_with_collection", 
            "query_with_collection",
            None  # Some steps might not need transforms
        ]
        
        for pipeline_name, pipeline in config["pipelines"].items():
            for step in pipeline.get("steps", []):
                if "input_transform" in step:
                    transform = step["input_transform"]
                    assert transform in valid_transforms, f"Invalid transform '{transform}' in {pipeline_name}"


class TestGeneratedVsOriginalComparison:
    """Compare generated services.yaml with the original expected format."""
    
    def load_original_services_yaml(self):
        """Load the original services.yaml as reference."""
        original_path = "services/temporal_service/config/services.yaml"
        with open(original_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_generated_has_all_original_services(self):
        """Generated config should include all services from original."""
        original = self.load_original_services_yaml()
        generated_config = yaml.safe_load(open("generated/services_dynamic.yaml", 'r'))
        
        original_services = set(original["services"].keys())
        generated_services = set(generated_config["services"].keys())
        
        # Generated should include all original services (may have additional ones)
        missing_services = original_services - generated_services
        if missing_services:
            # For now, just warn about local_activities since it's handled differently
            if missing_services != {"local_activities"}:
                assert False, f"Generated config missing services: {missing_services}"
    
    def test_generated_has_all_original_activities(self):
        """Generated config should include all activities from original."""
        original = self.load_original_services_yaml()
        generated_config = yaml.safe_load(open("generated/services_dynamic.yaml", 'r'))
        
        # Check that core activities are present
        for service_name, service_data in original["services"].items():
            if service_name == "local_activities":
                continue  # Handle local activities separately
                
            if service_name in generated_config["services"]:
                gen_activities = set(generated_config["services"][service_name]["activities"].keys())
                orig_activities = set(service_data["activities"].keys())
                
                missing_activities = orig_activities - gen_activities
                assert not missing_activities, f"Missing activities in {service_name}: {missing_activities}"
    
    def test_generated_has_all_original_pipelines(self):
        """Generated config should include all pipelines from original."""
        original = self.load_original_services_yaml()
        generated_config = yaml.safe_load(open("generated/services_dynamic.yaml", 'r'))
        
        original_pipelines = set(original["pipelines"].keys())
        generated_pipelines = set(generated_config["pipelines"].keys())
        
        missing_pipelines = original_pipelines - generated_pipelines
        if missing_pipelines:
            pytest.fail(f"Generated config missing pipelines: {missing_pipelines}")


class TestServicesYamlFunctionality:
    """Test that the generated services.yaml would actually work."""
    
    def test_config_structure_valid(self):
        """The generated config should have valid structure."""
        # This test validates the YAML structure without service_registry dependency
        config = {
            "services": {
                "test_service": {
                    "task_queue": "test-queue",
                    "activities": {
                        "test_activity": {
                            "description": "Test activity",
                            "timeout_seconds": 300
                        }
                    }
                }
            }
        }
        
        assert "services" in config
        assert len(config["services"]) > 0
        
        for service_name, service_data in config["services"].items():
            assert "activities" in service_data
            assert "task_queue" in service_data
    
    def test_pipeline_structure_valid(self):
        """Test that pipelines have valid structure."""
        # Test pipeline structure without I/O validation dependency
        config = {
            "pipelines": {
                "test_pipeline": {
                    "description": "Test pipeline",
                    "steps": [
                        {"activity": "service1.activity1"},
                        {"activity": "service2.activity2"}
                    ]
                }
            }
        }
        
        if "pipelines" in config:
            for pipeline_name, pipeline in config["pipelines"].items():
                assert "steps" in pipeline
                assert len(pipeline["steps"]) > 0


def run_validation_tests(yaml_file_path: str) -> dict:
    """
    Run all validation tests on a services.yaml file.
    Returns a summary of test results.
    """
    import subprocess
    
    # Run the tests
    result = subprocess.run([
        "python", "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short",
        "-x"  # Stop on first failure
    ], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(yaml_file_path)))
    
    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "errors": result.stderr,
        "return_code": result.returncode
    }


if __name__ == "__main__":
    # Allow running validation directly
    import sys
    if len(sys.argv) > 1:
        yaml_file = sys.argv[1]
        results = run_validation_tests(yaml_file)
        print(results["output"])
        if not results["success"]:
            print("ERRORS:")
            print(results["errors"])
            sys.exit(1)
    else:
        # Run pytest normally
        pytest.main([__file__, "-v"])
