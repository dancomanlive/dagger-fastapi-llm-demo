"""
Test validation tool for CodeAgent to verify generated services.yaml.
This tool enables the ReAct loop by providing test feedback.
"""
import subprocess
import os
import yaml
from typing import Dict, Any
from smolagents import tool


@tool
def check_file_exists(file_path: str) -> Dict[str, Any]:
    """
    Check if a file exists at the given path.
    
    Args:
        file_path: Path to check for file existence
        
    Returns:
        Dictionary with existence status and details
    """
    exists = os.path.exists(file_path)
    abs_path = os.path.abspath(file_path)
    
    return {
        "exists": exists,
        "path": file_path,
        "absolute_path": abs_path,
        "message": f"File {'exists' if exists else 'does not exist'} at {abs_path}"
    }


@tool
def validate_services_yaml_with_tests(yaml_file_path: str = "generated/services_dynamic.yaml") -> Dict[str, Any]:
    """
    Run comprehensive validation tests on a generated services.yaml file.
    This tool is used by CodeAgent in the ReAct loop to verify the quality of generated configurations.
    
    Args:
        yaml_file_path: Path to the services.yaml file to validate
        
    Returns:
        Dictionary with validation results including success status, failed tests, and suggestions
    """
    try:
        # Ensure the file exists
        if not os.path.exists(yaml_file_path):
            return {
                "success": False,
                "error": f"File not found: {yaml_file_path}",
                "failed_tests": [],
                "suggestions": ["Generate the services.yaml file first using generate_services_yaml_from_graphql"]
            }
        
        # Run the validation tests
        test_file = "tests/test_services_yaml_validation.py"
        
        # First check if the test file exists
        if not os.path.exists(test_file):
            # Try alternative locations
            alternative_locations = [
                "/Users/dan.coman/Workspace/smartagent-x7/tests/test_services_yaml_validation.py",
                "../../tests/test_services_yaml_validation.py"
            ]
            
            test_file_found = None
            for alt_path in alternative_locations:
                if os.path.exists(alt_path):
                    test_file_found = alt_path
                    break
            
            if not test_file_found:
                return {
                    "success": False,
                    "error_type": "environment_error",
                    "error": f"Test file not found: {test_file}",
                    "message": "The validation test script could not be found",
                    "details": f"Searched for '{test_file}' and alternatives but none exist",
                    "failed_tests": [],
                    "suggestions": [
                        "Check that the test files are present in the repository",
                        "Ensure you're running from the correct directory"
                    ]
                }
            else:
                test_file = test_file_found
        
        result = subprocess.run([
            "python", "-m", "pytest", 
            test_file,
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True, cwd=".")
        
        # Check for environmental errors first
        if result.returncode != 0 and ("No module named" in result.stderr or "ImportError" in result.stderr):
            return {
                "success": False,
                "error_type": "environment_error", 
                "error": "Missing Python dependencies",
                "message": "Required Python modules are not installed",
                "details": result.stderr,
                "failed_tests": [],
                "suggestions": [
                    "Install missing dependencies with: pip install -r requirements.txt",
                    "Check that all required packages are available"
                ]
            }
        
        if result.returncode != 0 and ("ModuleNotFoundError" in result.stderr or "command not found" in result.stderr):
            return {
                "success": False,
                "error_type": "environment_error",
                "error": "System command or module not found", 
                "message": "The test command failed due to missing system components",
                "details": result.stderr,
                "failed_tests": [],
                "suggestions": [
                    "Ensure pytest is installed: pip install pytest",
                    "Check that Python is properly configured"
                ]
            }
        
        # Parse the results
        output_lines = result.stdout.split('\n')
        failed_tests = []
        passed_tests = []
        
        for line in output_lines:
            if "PASSED" in line:
                test_name = line.split('::')[-1].split()[0]
                passed_tests.append(test_name)
            elif "FAILED" in line:
                test_name = line.split('::')[-1].split()[0]
                failed_tests.append(test_name)
        
        # Analyze failures and provide suggestions
        suggestions = []
        error_type = "yaml_content_error" if failed_tests else "success"
        
        if failed_tests:
            suggestions = analyze_test_failures(failed_tests, yaml_file_path)
        
        return {
            "success": result.returncode == 0,
            "error_type": error_type,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_passed": len(passed_tests),
            "total_failed": len(failed_tests),
            "test_output": result.stdout,
            "error_output": result.stderr,
            "suggestions": suggestions
        }
        
    except Exception as e:
        return {
            "success": False,
            "error_type": "system_error",
            "error": f"Validation failed with exception: {str(e)}",
            "message": "An unexpected error occurred during validation",
            "details": str(e),
            "failed_tests": [],
            "suggestions": [
                "Check that pytest is installed and test files are accessible",
                "Verify the working directory and file paths are correct",
                "Ensure all required dependencies are installed"
            ]
        }


def analyze_test_failures(failed_tests: list, yaml_file_path: str) -> list:
    """Analyze failed tests and provide specific suggestions for improvement."""
    suggestions = []
    
    # Load the YAML to analyze specific issues
    try:
        with open(yaml_file_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception:
        return ["Fix YAML syntax errors in the generated file"]
    
    for test_name in failed_tests:
        if "required_top_level_keys" in test_name:
            suggestions.append("Ensure the YAML has 'services' and 'pipelines' top-level keys")
            
        elif "required_services_are_present" in test_name:
            suggestions.append("Include embedding_service and retrieval_service in the services section")
            
        elif "services_have_required_fields" in test_name:
            suggestions.append("Each service needs 'task_queue' and 'activities' fields")
            
        elif "activities_have_required_fields" in test_name:
            suggestions.append("Activities need 'timeout_minutes' and 'retry_attempts' fields with proper types")
            
        elif "core_activities_are_present" in test_name:
            missing_activities = find_missing_core_activities(config)
            if missing_activities:
                suggestions.append(f"Add missing core activities: {', '.join(missing_activities)}")
            
        elif "pipelines_have_required_structure" in test_name:
            suggestions.append("Pipelines need 'name', 'description', and 'steps' fields")
            
        elif "pipeline_steps_have_required_fields" in test_name:
            suggestions.append("Pipeline steps need 'activity' and 'type' fields. Remote steps need 'service' field")
            
        elif "document_processing_pipeline_is_complete" in test_name:
            suggestions.append("Create document_processing pipeline with chunking (local) and embedding (remote) steps")
            
        elif "input_transforms_are_valid" in test_name:
            suggestions.append("Use valid input transforms: 'documents', 'chunked_docs_with_collection', 'query_with_collection'")
            
        elif "generated_has_all_original" in test_name:
            suggestions.append("Ensure all services, activities, and pipelines from original are included")
            
        elif "production_discovery" in test_name:
            suggestions.append("Fix production discovery integration with Temporal and metadata endpoints")
            
        elif "pipeline_io_compatibility" in test_name:
            suggestions.append("Ensure pipeline steps have compatible input/output types")
    
    # Add general suggestions if no specific ones found
    if not suggestions:
        suggestions.append("Review the generated YAML structure and compare with the original services.yaml")
        suggestions.append("Ensure all required fields are present and properly typed")
    
    return suggestions


def find_missing_core_activities(config: dict) -> list:
    """Find which core activities are missing from the configuration."""
    expected_activities = {
        "embedding_service": ["perform_embedding_and_indexing_activity"],
        "retrieval_service": ["search_documents_activity"],
    }
    
    missing = []
    
    for service_name, expected_activity_list in expected_activities.items():
        if service_name in config.get("services", {}):
            service_activities = config["services"][service_name].get("activities", {})
            for activity_name in expected_activity_list:
                if activity_name not in service_activities:
                    missing.append(f"{service_name}.{activity_name}")
    
    return missing
