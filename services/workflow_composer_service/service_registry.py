"""
DEPRECATED: Service registry for discovering and executing activities across services.

⚠️  WARNING: This module is deprecated and will be removed in a future version.
    The workflow composer service now uses production discovery via:
    - docker_production_discovery.py for live Temporal + metadata endpoint discovery
    - gql_schema/schema.py for GraphQL API with production data

    This registry system is only kept for compatibility with legacy tools:
    - agents/tools/io_matching.py
    - test files

    New integrations should use the production discovery GraphQL API.
"""
import os
import yaml
import logging
from typing import Dict, Any, List
from functools import lru_cache

logger = logging.getLogger(__name__)

# Global registry to store all registered activities
_activity_registry: Dict[str, Dict[str, Any]] = {}
_registry_initialized = False

def init_registry(registry_path: str = "config/registry.yaml") -> Dict[str, Any]:
    """Initialize the activity registry from configuration"""
    global _activity_registry, _registry_initialized
    
    if _registry_initialized:
        return _activity_registry
    
    if os.path.exists(registry_path):
        with open(registry_path, 'r') as f:
            registry_data = yaml.safe_load(f)
        
        # Normalize the registry structure
        _activity_registry = {}
        for service_name, service_data in registry_data.get("services", {}).items():
            for activity_name, activity_data in service_data.get("activities", {}).items():
                qualified_name = f"{service_name}.{activity_name}"
                _activity_registry[qualified_name] = {
                    "service": service_name,
                    "name": activity_name,
                    "description": activity_data.get("description", ""),
                    "task_queue": activity_data.get("task_queue", f"{service_name}-queue"),
                    "timeout_seconds": activity_data.get("timeout_seconds", 300),
                    "retry_attempts": activity_data.get("retry_attempts", 3),
                    "parameters": activity_data.get("parameters", []),
                    "returns": activity_data.get("returns", {})
                }
        
        logger.info(f"Loaded {len(_activity_registry)} activities from registry")
        _registry_initialized = True
        return _activity_registry
    else:
        logger.warning(f"Registry file not found: {registry_path}")
        _registry_initialized = True
        return {}

def register_activity(
    service_name: str,
    activity_name: str,
    description: str,
    task_queue: str = None,
    timeout_seconds: int = 300,
    retry_attempts: int = 3,
    parameters: List[Dict[str, Any]] = None,
    returns: Dict[str, Any] = None
) -> None:
    """Register an activity in the registry"""
    global _activity_registry
    
    if not _registry_initialized:
        init_registry()
    
    qualified_name = f"{service_name}.{activity_name}"
    _activity_registry[qualified_name] = {
        "service": service_name,
        "name": activity_name,
        "description": description,
        "task_queue": task_queue or f"{service_name}-queue",
        "timeout_seconds": timeout_seconds,
        "retry_attempts": retry_attempts,
        "parameters": parameters or [],
        "returns": returns or {}
    }
    
    logger.info(f"Registered activity: {qualified_name}")

def get_activity_metadata(activity_id: str) -> Dict[str, Any]:
    """Get metadata for a specific activity"""
    if not _registry_initialized:
        init_registry()
    
    return _activity_registry.get(activity_id, {})

@lru_cache(maxsize=1)
def get_all_activities() -> Dict[str, Dict[str, Any]]:
    """Get all registered activities with their metadata"""
    if not _registry_initialized:
        init_registry()
    
    return _activity_registry

def get_activities_by_service(service_name: str) -> Dict[str, Dict[str, Any]]:
    """Get all activities for a specific service"""
    all_activities = get_all_activities()
    return {
        activity_id: metadata 
        for activity_id, metadata in all_activities.items() 
        if metadata.get("service") == service_name
    }

def get_service_list() -> List[str]:
    """Get a list of all registered services"""
    if not _registry_initialized:
        init_registry()
    
    services = set(metadata.get("service") for metadata in _activity_registry.values())
    return sorted(list(services))

def export_registry_for_llm() -> Dict[str, Any]:
    """Export the registry in a format optimized for LLM consumption"""
    if not _registry_initialized:
        init_registry()
    
    # Organize by service for better comprehension
    services = {}
    for activity_id, metadata in _activity_registry.items():
        service_name = metadata.get("service")
        if service_name not in services:
            services[service_name] = {
                "name": service_name,
                "activities": {}
            }
        
        # Add activity with simplified metadata for LLM
        activity_name = metadata.get("name")
        services[service_name]["activities"][activity_name] = {
            "description": metadata.get("description", ""),
            "parameters": metadata.get("parameters", []),
            "returns": metadata.get("returns", {}),
        }
    
    return {
        "services": services,
        "workflow_examples": _load_workflow_examples()
    }

def _load_workflow_examples() -> List[Dict[str, Any]]:
    """Load example workflows to help the LLM understand composition patterns"""
    example_path = "config/workflow_examples.yaml"
    if os.path.exists(example_path):
        with open(example_path, 'r') as f:
            return yaml.safe_load(f).get("examples", [])
    return []

def save_registry() -> None:
    """Save the current registry to the registry file"""
    if not _registry_initialized:
        return
    
    # Convert flat registry to hierarchical structure by service
    services = {}
    for activity_id, metadata in _activity_registry.items():
        service_name = metadata.get("service")
        activity_name = metadata.get("name")
        
        if service_name not in services:
            services[service_name] = {"activities": {}}
        
        services[service_name]["activities"][activity_name] = {
            "description": metadata.get("description", ""),
            "task_queue": metadata.get("task_queue"),
            "timeout_seconds": metadata.get("timeout_seconds"),
            "retry_attempts": metadata.get("retry_attempts"),
            "parameters": metadata.get("parameters", []),
            "returns": metadata.get("returns", {})
        }
    
    # Save to file
    os.makedirs("config", exist_ok=True)
    with open("config/registry.yaml", 'w') as f:
        yaml.dump({"services": services}, f, default_flow_style=False)

# I/O Matching and Transform System
def get_activity_io_metadata(activity_id: str) -> Dict[str, Any]:
    """
    Get comprehensive I/O metadata for activity matching.
    
    Args:
        activity_id: Qualified activity ID (e.g., "embedding_service.perform_embedding_and_indexing_activity")
        
    Returns:
        Dict containing input/output schemas, compatible transforms, and suggestions
    """
    if not _registry_initialized:
        init_registry()
    
    activity = _activity_registry.get(activity_id, {})
    if not activity:
        return {}
    
    # Extract I/O schemas
    input_schema = activity.get("parameters", [])
    output_schema = activity.get("returns", {})
    
    # Determine compatible transforms based on activity type
    compatible_transforms = _get_compatible_transforms(activity_id, input_schema)
    
    # Suggest input/output activities based on I/O compatibility
    suggested_inputs = _get_suggested_input_activities(activity_id, input_schema)
    suggested_outputs = _get_suggested_output_activities(activity_id, output_schema)
    
    return {
        "input_schema": input_schema,
        "output_schema": output_schema,
        "compatible_transforms": compatible_transforms,
        "suggested_inputs": suggested_inputs,
        "suggested_outputs": suggested_outputs
    }

def find_compatible_transform(output_schema: Dict[str, Any], input_schema: List[Dict[str, Any]]) -> str:
    """
    Find the appropriate transform to match output schema to input schema.
    
    Args:
        output_schema: Output schema from previous activity
        input_schema: Input schema for next activity
        
    Returns:
        Transform name that can adapt the output to the input
    """
    # Extract output type and input requirements
    output_type = output_schema.get("type", "unknown")
    
    # Get primary input parameter
    primary_input = input_schema[0] if input_schema else {}
    input_type = primary_input.get("type", "unknown")
    input_name = primary_input.get("name", "unknown")
    
    # Transform mapping logic
    transform_map = {
        # Document processing transforms - exact matches
        ("List[Dict]", "List[Dict]", "documents"): "documents",
        
        # Embedding service needs both documents and collection
        ("List[Dict]", "List[Dict]", "documents", True): "chunked_docs_with_collection",
        
        # Query processing transforms  
        ("str", "str", "query"): "query_with_collection",
        ("Dict", "str", "query"): "extracted_query",
        
        # Search result transforms
        ("Dict", "List[Dict]", "documents"): "extracted_documents",
    }
    
    # Check if this activity needs collection parameter (multi-param activity)
    needs_collection = len(input_schema) > 1 and any(
        param.get("name") in ["collection_name", "collection"] 
        for param in input_schema
    )
    
    # Try exact match with collection requirement
    if needs_collection:
        key = (output_type, input_type, input_name, True)
        if key in transform_map:
            return transform_map[key]
    
    # Try to find exact match without collection
    key = (output_type, input_type, input_name)
    if key in transform_map:
        return transform_map[key]
    
    # Try partial matches
    for (out_type, in_type, in_name), transform in transform_map.items():
        if output_type == out_type and input_type == in_type:
            return transform
        elif output_type == out_type and input_name == in_name:
            return transform
    
    # Default to passthrough
    return "passthrough"

def validate_pipeline_io(activities: List[str]) -> Dict[str, Any]:
    """
    Validate that activities in a pipeline have compatible I/O.
    
    Args:
        activities: List of activity IDs to validate
        
    Returns:
        Dict with validation results, issues, and suggested transforms
    """
    if not activities:
        return {"valid": True, "issues": [], "suggested_transforms": []}
    
    issues = []
    suggested_transforms = []
    
    # Validate first activity
    first_activity = activities[0]
    first_metadata = get_activity_io_metadata(first_activity)
    first_transform = _infer_input_transform(first_activity, first_metadata["input_schema"])
    suggested_transforms.append({
        "activity": first_activity,
        "transform": first_transform
    })
    
    # Validate activity chains
    for i in range(len(activities) - 1):
        current_activity = activities[i]
        next_activity = activities[i + 1]
        
        current_metadata = get_activity_io_metadata(current_activity)
        next_metadata = get_activity_io_metadata(next_activity)
        
        current_output = current_metadata["output_schema"]
        next_input = next_metadata["input_schema"]
        
        # Try to find compatible transform
        transform = find_compatible_transform(current_output, next_input)
        suggested_transforms.append({
            "activity": next_activity,
            "transform": transform
        })
        
        # Check if transform is valid (not just passthrough for incompatible types)
        if not _schemas_compatible(current_output, next_input) and transform == "passthrough":
            issues.append({
                "position": i,
                "from_activity": current_activity,
                "to_activity": next_activity,
                "issue": f"Output type '{current_output.get('type')}' incompatible with input type '{next_input[0].get('type') if next_input else 'none'}'",
                "suggested_fix": "Consider adding intermediate transform or different activity"
            })
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "suggested_transforms": suggested_transforms
    }

def _get_compatible_transforms(activity_id: str, input_schema: List[Dict[str, Any]]) -> List[str]:
    """Get list of transforms compatible with this activity's input."""
    if not input_schema:
        return ["passthrough"]
    
    primary_input = input_schema[0]
    input_name = primary_input.get("name", "")
    
    # Map input requirements to compatible transforms
    transform_compatibility = {
        "documents": ["documents", "passthrough"],
        "query": ["query_with_collection", "passthrough"],
        "chunked_documents": ["chunked_docs_with_collection"]
    }
    
    return transform_compatibility.get(input_name, ["passthrough"])

def _get_suggested_input_activities(activity_id: str, input_schema: List[Dict[str, Any]]) -> List[str]:
    """Suggest activities that could provide input to this activity."""
    if not input_schema:
        return []
    
    primary_input = input_schema[0]
    input_name = primary_input.get("name", "")
    
    # Known activity chains
    input_suggestions = {
        "documents": ["chunk_documents_activity"],
        "chunked_documents": ["chunk_documents_activity"], 
        "query": [],  # Usually starts pipeline
    }
    
    return input_suggestions.get(input_name, [])

def _get_suggested_output_activities(activity_id: str, output_schema: Dict[str, Any]) -> List[str]:
    """Suggest activities that could use this activity's output."""
    output_type = output_schema.get("type", "")
    
    # Known activity chains
    output_suggestions = {
        "List[Dict]": ["perform_embedding_and_indexing_activity"],
        "Dict": [],  # Usually ends pipeline
    }
    
    return output_suggestions.get(output_type, [])

def _infer_input_transform(activity_id: str, input_schema: List[Dict[str, Any]]) -> str:
    """Infer the appropriate input transform for an activity."""
    if not input_schema:
        return "passthrough"
    
    primary_input = input_schema[0]
    input_name = primary_input.get("name", "")
    
    # Map activity input requirements to transforms
    transform_map = {
        "documents": "documents",
        "query": "query_with_collection",
        "chunked_documents": "chunked_docs_with_collection"
    }
    
    return transform_map.get(input_name, "passthrough")

def _schemas_compatible(output_schema: Dict[str, Any], input_schema: List[Dict[str, Any]]) -> bool:
    """Check if output schema is compatible with input schema."""
    if not input_schema:
        return True
    
    output_type = output_schema.get("type", "")
    input_type = input_schema[0].get("type", "")
    
    # Basic type compatibility
    compatible_types = {
        "List[Dict]": ["List[Dict]"],
        "Dict": ["Dict", "str"],  # Dict can often be converted to string
        "str": ["str"],
        "int": ["int", "str"],
        "float": ["float", "int", "str"]
    }
    
    return input_type in compatible_types.get(output_type, [])
