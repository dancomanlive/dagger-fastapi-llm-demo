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
def discover_services_complete() -> Dict[str, Any]:
    """
    Perform complete service discovery using the optimized GraphQL query.
    This is much more efficient than schema introspection as it uses a pre-optimized query
    to get all service details, activities, parameters, and system status in one call.
    
    Returns:
        Complete service information including activities, I/O parameters, timeouts, and system status
    """
    try:
        # The optimized GraphQL query that gets everything we need in one call
        optimized_query = '''
        {
            services {
                name
                taskQueue
                temporalStatus
                health
                activities {
                    name
                    description
                    parameters {
                        name
                        type
                        description
                        required
                    }
                    returns {
                        type
                        description
                    }
                    timeoutSeconds
                    retryAttempts
                }
            }
            discoveryInfo {
                temporalConnected
            }
        }
        '''
        
        response = requests.post(
            f"{WORKFLOW_SERVICE_URL}/graphql",
            headers={"Content-Type": "application/json"},
            json={"query": optimized_query}
        )
        
        if response.status_code == 200:
            result = response.json()
            if "errors" in result:
                return {"error": f"GraphQL errors: {result['errors']}"}
            return result["data"]
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": f"Failed to discover services: {str(e)}"}
