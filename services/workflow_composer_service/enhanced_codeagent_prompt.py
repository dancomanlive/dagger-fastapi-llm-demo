#!/usr/bin/env python3
"""
Enhanced CodeAgent with improved error handling and validation strategies.

This version implements the recommendations for better handling of validation errors:
1. Structured error analysis
2. Environmental vs content error distinction  
3. Alternative validation strategies
4. Sanity checks before regeneration
"""

from smolagents import CodeAgent, DuckDuckGoSearchTool, PythonInterpreterTool
from agents.tools.dynamic_yaml_generation import generate_services_yaml_from_graphql
from agents.tools.test_validation import validate_services_yaml_with_tests, check_file_exists

def create_enhanced_codeagent():
    """Create a CodeAgent with enhanced error handling capabilities."""
    
    # Enhanced system prompt with explicit error handling instructions
    enhanced_system_prompt = """
    You are an expert DevOps and workflow automation agent specializing in dynamic service discovery and YAML generation.

    Your primary task is to:
    1. Query GraphQL endpoints to discover available services and activities
    2. Generate comprehensive services.yaml files for Temporal workflows
    3. Validate the generated configurations with robust error handling

    CRITICAL ERROR HANDLING RULES:
    
    When using validate_services_yaml_with_tests and encountering failures:
    
    1. FIRST, examine the 'error_type' field in the validation response:
       - "environment_error": Do NOT regenerate YAML. Report the environment issue.
       - "system_error": Check dependencies and file paths. Do NOT regenerate YAML.
       - "yaml_content_error": Only then consider YAML improvements.
    
    2. BEFORE regenerating YAML for content errors:
       - Use check_file_exists() to verify test files and dependencies
       - Examine the specific failed_tests to understand what's missing
       - Check if the failure is due to missing reference files vs actual content issues
    
    3. AVOID infinite loops:
       - If the same validation fails 3 times with content errors, STOP and report the issue
       - Look for patterns in failures - are they consistent or environmental?
    
    4. PRIORITIZE environmental diagnosis over content regeneration:
       - Missing test files = environment issue (don't regenerate)
       - Import errors = dependency issue (don't regenerate)  
       - Comparison failures = might be missing reference data (investigate first)

    Available tools:
    - generate_services_yaml_from_graphql: Generate YAML from live service discovery
    - validate_services_yaml_with_tests: Run comprehensive validation tests
    - check_file_exists: Verify file existence before proceeding
    
    Always use structured reasoning and explain your error analysis strategy.
    """
    
    # Create the enhanced agent with additional tools
    agent = CodeAgent(
        tools=[
            generate_services_yaml_from_graphql,
            validate_services_yaml_with_tests, 
            check_file_exists,
            DuckDuckGoSearchTool(),
            PythonInterpreterTool()
        ],
        system_prompt=enhanced_system_prompt,
        max_iterations=15,
        additional_authorized_imports=["requests", "yaml", "json", "os"]
    )
    
    return agent

def test_enhanced_codeagent():
    """Test the enhanced CodeAgent with the improved workflow."""
    
    agent = create_enhanced_codeagent()
    
    task = """
    Generate a comprehensive services.yaml file for Temporal workflows by:
    
    1. Discovering available services via GraphQL query to http://localhost:8001/graphql
    2. Creating a properly structured YAML configuration
    3. Validating the generated configuration with comprehensive error analysis
    
    Use the enhanced error handling approach:
    - Distinguish between environment vs content errors
    - Use file existence checks when validation fails
    - Avoid regeneration loops for non-content issues
    - Provide detailed analysis of any validation failures
    
    The goal is a production-ready services.yaml that passes all relevant validation tests.
    """
    
    result = agent.run(task)
    return result

if __name__ == "__main__":
    print("🧠 Testing Enhanced CodeAgent with improved error handling...")
    result = test_enhanced_codeagent()
    print(f"\n🎯 Enhanced CodeAgent Result:\n{result}")
