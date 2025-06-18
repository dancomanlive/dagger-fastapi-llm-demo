"""
Generic service configuration loader for Temporal workflows.

This module provides configuration-driven service discovery and activity execution,
making the temporal service generic and extensible.
"""

import os
import yaml
import logging
import importlib
import inspect
from typing import Dict, Any, Optional, List, Callable
from datetime import timedelta
from temporalio.common import RetryPolicy

logger = logging.getLogger(__name__)

class ServiceConfig:
    """Configuration manager for services and activities."""
    
    def __init__(self, config_path: str = None):
        """Initialize service configuration."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config", "services.yaml")
        
        self.config_path = config_path
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            logger.info(f"Loaded service configuration from {self.config_path}")
        except FileNotFoundError:
            logger.error(f"Service configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing service configuration: {e}")
            raise
    
    def get_services(self) -> Dict[str, Any]:
        """Get all service configurations."""
        return self._config.get("services", {})
    
    def get_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific service."""
        return self._config.get("services", {}).get(service_name)
    
    def get_activity_config(self, activity_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific activity across all services."""
        services = self.get_services()
        
        # Check local activities first
        if "local_activities" in services:
            local_activities = services["local_activities"]
            if activity_name in local_activities:
                config = local_activities[activity_name].copy()
                config["type"] = "local"
                config["service_name"] = "local"
                return config
        
        # Check remote services
        for service_name, service_config in services.items():
            if service_name == "local_activities":
                continue
                
            activities = service_config.get("activities", {})
            if activity_name in activities:
                config = activities[activity_name].copy()
                config["type"] = "remote"
                config["service_name"] = service_name
                config["task_queue"] = service_config.get("task_queue")
                return config
        
        return None
    
    def get_pipelines(self) -> Dict[str, Any]:
        """Get all pipeline configurations."""
        return self._config.get("pipelines", {})
    
    def get_pipeline_config(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific pipeline."""
        return self._config.get("pipelines", {}).get(pipeline_name)
    
    def get_retry_policy(self, activity_config: Dict[str, Any]) -> RetryPolicy:
        """Create RetryPolicy from activity configuration."""
        return RetryPolicy(
            initial_interval=timedelta(
                seconds=activity_config.get("retry_initial_interval_seconds", 1)
            ),
            maximum_interval=timedelta(
                seconds=activity_config.get("retry_maximum_interval_seconds", 30)
            ),
            maximum_attempts=activity_config.get("retry_attempts", 3)
        )
    
    def get_timeout(self, activity_config: Dict[str, Any]) -> timedelta:
        """Get timeout from activity configuration."""
        return timedelta(
            minutes=activity_config.get("timeout_minutes", 5)
        )
    
    def get_all_activity_names(self) -> List[str]:
        """Get all activity names from configuration."""
        activity_names = []
        services = self.get_services()
        
        # Get local activities
        if "local_activities" in services:
            activity_names.extend(services["local_activities"].keys())
        
        # Get remote service activities
        for service_name, service_config in services.items():
            if service_name != "local_activities":
                activities = service_config.get("activities", {})
                activity_names.extend(activities.keys())
        
        return activity_names
    
    def discover_activity_functions(self, module_name: str = "activities") -> List[Callable]:
        """
        Dynamically discover activity functions from a module.
        
        Args:
            module_name: Name of the module to inspect for activities
            
        Returns:
            List of activity function objects
        """
        try:
            module = importlib.import_module(module_name)
            activity_functions = []
            
            for name in dir(module):
                obj = getattr(module, name)
                if (inspect.isfunction(obj) and 
                    hasattr(obj, "__temporal_activity_definition")):
                    activity_functions.append(obj)
                    logger.debug(f"Discovered activity function: {name}")
            
            logger.info(f"Discovered {len(activity_functions)} activity functions from module {module_name}")
            return activity_functions
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            return []

# Global configuration instance
_service_config = None

def get_service_config() -> ServiceConfig:
    """Get the global service configuration instance."""
    global _service_config
    if _service_config is None:
        _service_config = ServiceConfig()
    return _service_config

def reload_config():
    """Reload the service configuration."""
    global _service_config
    _service_config = None
    return get_service_config()
