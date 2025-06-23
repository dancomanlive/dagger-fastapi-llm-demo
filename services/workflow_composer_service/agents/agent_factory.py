"""
Agent factory for creating SmolAgents CodeAgent with workflow composition capabilities.
"""
from smolagents import CodeAgent
from smolagents.models import OpenAIServerModel

# Import approved modular tools for YAML generation workflow
from .tools import (
    discover_services_complete,
    generate_services_yaml_from_graphql,
    save_generated_services_yaml,
    validate_services_yaml_with_tests
)


def create_workflow_composer_agent():
    """
    Create a SmolAgents CodeAgent focused on services.yaml generation and validation.
    
    This agent follows a ReAct (Reasoning + Acting) loop pattern for generating
    and validating services.yaml configurations:
    1. Uses GraphQL API introspection to discover services
    2. Generates services.yaml based on GraphQL data
    3. Validates the generated configuration using unit tests
    4. Iterates until all tests pass
    
    Only essential tools for YAML generation workflow are included.
    """
    # Define the approved tools available to the agent - YAML generation workflow
    tools = [
        # Core discovery tool (optimized single-call GraphQL query)
        discover_services_complete,
        # Dynamic YAML generation tools (GraphQL-based only)
        generate_services_yaml_from_graphql,
        save_generated_services_yaml,
        # Test validation tool for ReAct loop
        validate_services_yaml_with_tests
    ]
    
    # Create OpenAI model
    model = OpenAIServerModel(model_id="gpt-4o-mini")
    
    # Create the agent with the model and tools
    agent = CodeAgent(
        tools=tools,
        model=model,
        additional_authorized_imports=["json", "requests", "os"],
        max_steps=15  # Limit steps to prevent infinite loops but allow for code generation
    )
    
    return agent
