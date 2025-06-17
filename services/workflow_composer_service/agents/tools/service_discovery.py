"""
Service discovery tools using GraphQL introspection for activity registry.
Part of the Pattern 2 workflow: ... → GraphQL Introspection → Discover Activities → ...
"""
import requests
from typing import Dict, Any
from smolagents import tool

# Configuration
WORKFLOW_SERVICE_URL = "http://localhost:8001"


@tool
def discover_services() -> Dict[str, Any]:
    """
    Discover all available services and their activities.
    Returns detailed information about what services are available and what they can do.
    """
    try:
        response = requests.get(f"{WORKFLOW_SERVICE_URL}/services")
        services_data = response.json()
        
        # Format for better readability
        summary = {
            "total_services": len(services_data["services"]),
            "services": {}
        }
        
        for service_name, service_info in services_data["services"].items():
            activities = service_info["activities"]
            summary["services"][service_name] = {
                "activity_count": len(activities),
                "activities": {
                    name: {
                        "description": info["description"],
                        "parameters": [p["name"] for p in info.get("parameters", [])]
                    }
                    for name, info in activities.items()
                }
            }
        
        return summary
    except Exception as e:
        return {"error": f"Failed to discover services: {str(e)}"}


@tool
def get_activity_details(activity_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific activity.
    
    Args:
        activity_id: The ID of the activity (e.g., "utility_service.validate_inputs_activity")
    
    Returns:
        Detailed information about the activity including parameters and return types.
    """
    try:
        response = requests.get(f"{WORKFLOW_SERVICE_URL}/activities/{activity_id}")
        return response.json()
    except Exception as e:
        return {"error": f"Failed to get activity details: {str(e)}"}


@tool
def query_graphql(query: str) -> Dict[str, Any]:
    """
    Execute a GraphQL query against the activity registry for introspection.
    
    Args:
        query: GraphQL query string
        
    Returns:
        GraphQL query results
    """
    try:
        response = requests.post(
            f"{WORKFLOW_SERVICE_URL}/graphql",
            json={"query": query},
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    except Exception as e:
        return {"error": f"GraphQL query failed: {str(e)}"}
