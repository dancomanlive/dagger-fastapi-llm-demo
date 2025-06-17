"""
Service registry for discovering and executing activities across services.
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
