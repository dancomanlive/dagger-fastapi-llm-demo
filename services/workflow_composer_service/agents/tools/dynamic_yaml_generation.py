"""
Dynamic services.yaml generation tool for CodeAgent.
Uses ONLY GraphQL API introspection to build configuration - NO file system access.
"""
import yaml
import requests
from typing import Dict, Any, List, Optional
from smolagents import tool

# GraphQL endpoint for service discovery
GRAPHQL_ENDPOINT = "http://localhost:8001/graphql"


@tool
def generate_services_yaml_from_graphql() -> Dict[str, Any]:
    """
    Dynamically generate services.yaml by querying the GraphQL API.
    This uses pure API introspection without any file system access.
    
    Returns:
        Complete services.yaml structure based on GraphQL API discovery
    """
    try:
        print("🔍 Querying GraphQL API for service discovery...")
        
        # Query all services and activities via GraphQL
        services_query = """
        query {
            services {
                name
                activityCount
                activities {
                    id
                    name
                    description
                    taskQueue
                    timeoutSeconds
                    retryAttempts
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
                    testCoverage {
                        hasTests
                        testCount
                    }
                }
            }
        }
        """
        
        response = requests.post(
            GRAPHQL_ENDPOINT,
            json={"query": services_query},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            return {"error": f"GraphQL query failed with status {response.status_code}: {response.text}"}
        
        data = response.json()
        if "errors" in data:
            return {"error": f"GraphQL errors: {data['errors']}"}
        
        services_data = data["data"]["services"]
        
        # Convert GraphQL response to services.yaml format
        result = build_services_yaml_from_graphql(services_data)
        
        print(f"✅ GraphQL Discovery complete:")
        print(f"   Services: {result['discovery_metadata']['services_discovered']}")
        print(f"   Activities: {result['discovery_metadata']['activities_discovered']}")
        print(f"   Pipelines: {result['discovery_metadata']['pipelines_inferred']}")
        
        return result
        
    except Exception as e:
        return {"error": f"Failed to generate services.yaml from GraphQL: {str(e)}"}


def build_services_yaml_from_graphql(services_data: List[Dict]) -> Dict[str, Any]:
    """Convert GraphQL services data to services.yaml format."""
    
    result = {
        "services": {},
        "pipelines": {},
        "discovery_metadata": {
            "discovery_method": "graphql_api_introspection",
            "services_discovered": 0,
            "activities_discovered": 0,
            "pipelines_inferred": 0
        }
    }
    
    # Process each service from GraphQL
    for service in services_data:
        service_name = service["name"]
        
        service_config = {
            "task_queue": f"{service_name.replace('_service', '')}-task-queue",
            "activities": {}
        }
        
        # Process activities
        for activity in service["activities"]:
            activity_config = {
                "timeout_minutes": activity["timeoutSeconds"] // 60 if activity["timeoutSeconds"] else 10,
                "retry_attempts": activity["retryAttempts"] if activity["retryAttempts"] else 3,
                "retry_initial_interval_seconds": 1,
                "retry_maximum_interval_seconds": 30
            }
            
            # Add description if available
            if activity["description"]:
                activity_config["description"] = activity["description"]
            
            service_config["activities"][activity["name"]] = activity_config
            result["discovery_metadata"]["activities_discovered"] += 1
        
        result["services"][service_name] = service_config
        result["discovery_metadata"]["services_discovered"] += 1
    
    # Generate pipelines based on discovered activities
    pipelines = infer_pipelines_from_graphql_activities(services_data)
    result["pipelines"] = pipelines
    result["discovery_metadata"]["pipelines_inferred"] = len(pipelines)
    
    return result


def infer_pipelines_from_graphql_activities(services_data: List[Dict]) -> Dict[str, Any]:
    """Infer logical pipelines based on GraphQL activity data."""
    pipelines = {}
    
    # Collect all activities with their details
    all_activities = []
    for service in services_data:
        for activity in service["activities"]:
            all_activities.append({
                "service": service["name"],
                "name": activity["name"],
                "full_name": f"{service['name']}.{activity['name']}",
                "description": activity.get("description", ""),
                "parameters": activity.get("parameters", []),
                "returns": activity.get("returns", {})
            })
    
    # Infer document processing pipeline
    chunk_activities = [a for a in all_activities if 'chunk' in a['name'].lower()]
    embedding_activities = [a for a in all_activities if 'embedding' in a['name'].lower() or 'index' in a['name'].lower()]
    
    if chunk_activities and embedding_activities:
        pipelines["document_processing"] = {
            "name": "DocumentProcessingPipeline",
            "description": "Processes documents through chunking and embedding",
            "steps": [
                {
                    "activity": chunk_activities[0]["name"],
                    "type": "local" if chunk_activities[0]["service"] == "local_activities" else "remote",
                    "input_transform": "documents"
                },
                {
                    "activity": embedding_activities[0]["name"],
                    "type": "remote",
                    "service": embedding_activities[0]["service"],
                    "input_transform": "chunked_docs_with_collection"
                }
            ]
        }
        
        # Add service field for remote steps
        if pipelines["document_processing"]["steps"][0]["type"] == "remote":
            pipelines["document_processing"]["steps"][0]["service"] = chunk_activities[0]["service"]
    
    # Infer document retrieval pipeline
    search_activities = [a for a in all_activities if 'search' in a['name'].lower()]
    if search_activities:
        pipelines["document_retrieval"] = {
            "name": "DocumentRetrievalPipeline",
            "description": "Searches for documents using semantic similarity",
            "steps": [
                {
                    "activity": search_activities[0]["name"],
                    "type": "remote",
                    "service": search_activities[0]["service"],
                    "input_transform": "query_with_collection"
                }
            ]
        }
    
    # Infer health check pipeline
    health_activities = [a for a in all_activities if 'health' in a['name'].lower()]
    if health_activities:
        pipelines["health_check"] = {
            "name": "HealthCheckPipeline",
            "description": "Checks health status of all services",
            "steps": [
                {
                    "activity": health_activities[0]["name"],
                    "type": "remote",
                    "service": health_activities[0]["service"],
                    "input_transform": "health_request"
                }
            ]
        }
    
    # Infer data normalization pipeline
    normalize_activities = [a for a in all_activities if 'normalize' in a['name'].lower()]
    if normalize_activities:
        pipelines["data_normalization"] = {
            "name": "DataNormalizationPipeline",
            "description": "Normalizes data using configured transforms",
            "steps": [
                {
                    "activity": normalize_activities[0]["name"],
                    "type": "remote",
                    "service": normalize_activities[0]["service"],
                    "input_transform": "normalization_request"
                }
            ]
        }
    
    return pipelines


@tool
def save_generated_services_yaml(services_config: Dict[str, Any], output_path: str = "generated/services_dynamic.yaml") -> str:
    """
    Save the generated services.yaml configuration to a file.
    
    Args:
        services_config: The services configuration dictionary
        output_path: Path where to save the YAML file
        
    Returns:
        Success message with file path
    """
    try:
        # Create directory if it doesn't exist
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Remove metadata before saving
        clean_config = {k: v for k, v in services_config.items() if k != "discovery_metadata"}
        
        with open(output_path, 'w') as f:
            yaml.dump(clean_config, f, default_flow_style=False, sort_keys=False)
        
        return f"✅ Generated services.yaml saved to: {output_path}"
        
    except Exception as e:
        return f"❌ Failed to save services.yaml: {str(e)}"
    