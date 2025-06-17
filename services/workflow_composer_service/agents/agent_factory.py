"""
Agent factory for creating SmolAgents CodeAgent with workflow composition capabilities.
"""
import os
from smolagents import CodeAgent
from smolagents.models import OpenAIServerModel

# Import new modular tools (Pattern 2 implementation)
from .tools import (
    infer_user_intent,
    discover_services,
    get_activity_details,
    query_graphql,
    plan_activity_sequence,
    execute_planned_workflow,
    smart_workflow_assistant
)


def create_workflow_composer_agent():
    """
    Create a SmolAgents CodeAgent with workflow composition capabilities.
    """
    # Define the tools available to the agent - focusing on Pattern 2 core functionality
    tools = [
        # Core Pattern 2 tools (new modular implementation)
        infer_user_intent,
        discover_services,
        get_activity_details,
        query_graphql,
        plan_activity_sequence,
        execute_planned_workflow,
        smart_workflow_assistant
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
