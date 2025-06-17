"""
Intent inference tools for analyzing user natural language requests.
Part of the Pattern 2 workflow: User Message → Intent Inference → ...
"""
from typing import Dict, Any
from smolagents import tool


@tool
def infer_user_intent(user_message: str) -> Dict[str, Any]:
    """
    Infer user intent from a natural language message.
    
    Args:
        user_message: The user's request in natural language
        
    Returns:
        Dictionary with inferred intent, goals, and context
    """
    try:
        # Simple intent classification based on keywords
        message_lower = user_message.lower()
        
        intent = {
            "primary_goal": "unknown",
            "action_type": "unknown",
            "domain": "general",
            "entities": [],
            "requirements": []
        }
        
        # Classify primary goal
        if any(word in message_lower for word in ["search", "find", "lookup", "query"]):
            intent["primary_goal"] = "search"
            intent["action_type"] = "retrieval"
        elif any(word in message_lower for word in ["create", "generate", "build", "make"]):
            intent["primary_goal"] = "creation"
            intent["action_type"] = "generation"
        elif any(word in message_lower for word in ["analyze", "process", "transform", "extract"]):
            intent["primary_goal"] = "analysis"
            intent["action_type"] = "processing"
        elif any(word in message_lower for word in ["workflow", "compose", "orchestrate"]):
            intent["primary_goal"] = "workflow_composition"
            intent["action_type"] = "orchestration"
        
        # Identify domain
        if any(word in message_lower for word in ["document", "pdf", "text", "file"]):
            intent["domain"] = "document_processing"
        elif any(word in message_lower for word in ["embedding", "vector", "semantic"]):
            intent["domain"] = "embeddings"
        elif any(word in message_lower for word in ["accommodation", "hotel", "booking"]):
            intent["domain"] = "accommodation_search"
        
        # Extract requirements
        if "validate" in message_lower:
            intent["requirements"].append("validation")
        if "filter" in message_lower:
            intent["requirements"].append("filtering")
        if "rank" in message_lower:
            intent["requirements"].append("ranking")
        if "format" in message_lower:
            intent["requirements"].append("formatting")
        
        intent["original_message"] = user_message
        intent["confidence"] = 0.8 if intent["primary_goal"] != "unknown" else 0.3
        
        return intent
        
    except Exception as e:
        return {"error": f"Failed to infer intent: {str(e)}"}
