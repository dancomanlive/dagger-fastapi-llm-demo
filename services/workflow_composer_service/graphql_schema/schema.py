"""
GraphQL schema for workflow composer service using Strawberry.
Provides introspection of services, activities, and workflow composition capabilities.
Uses production discovery system (Temporal + Metadata endpoints) instead of static files.
"""
import strawberry
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path
import asyncio
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from docker_production_discovery import ProductionTemporalDiscovery

logger = logging.getLogger(__name__)

# Global discovery instance
_discovery_instance = None

async def get_discovery_instance():
    """Get or create production discovery instance."""
    global _discovery_instance
    if _discovery_instance is None:
        _discovery_instance = ProductionTemporalDiscovery()
        await _discovery_instance.connect_to_temporal()
    return _discovery_instance

def run_async(coro):
    """Helper to run async code in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we need to handle it differently
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

async def get_all_activities_async():
    """Get all activities from production discovery system."""
    discovery = await get_discovery_instance()
    services_data = await discovery.discover_all_services_via_metadata()
    
    all_activities = {}
    for service_name, service_data in services_data.items():
        for activity_name, activity_data in service_data.get("activities", {}).items():
            qualified_name = f"{service_name}.{activity_name}"
            all_activities[qualified_name] = {
                "service": service_name,
                "name": activity_name,
                "description": activity_data.get("description", ""),
                "task_queue": service_data.get("task_queue", f"{service_name}-queue"),
                "timeout_seconds": activity_data.get("timeout_seconds", 300),
                "retry_attempts": activity_data.get("retry_attempts", 3),
                "parameters": activity_data.get("parameters", []),
                "returns": activity_data.get("returns", {})
            }
    
    return all_activities

def get_all_activities():
    """Sync wrapper for get_all_activities_async."""
    return run_async(get_all_activities_async())

async def get_activity_metadata_async(activity_id: str):
    """Get metadata for a specific activity."""
    all_activities = await get_all_activities_async()
    return all_activities.get(activity_id)

def get_activity_metadata(activity_id: str):
    """Sync wrapper for get_activity_metadata_async."""
    return run_async(get_activity_metadata_async(activity_id))


@strawberry.type
class Parameter:
    """GraphQL type for activity parameters."""
    name: str
    type: str
    description: str
    required: bool


@strawberry.type
class ReturnInfo:
    """GraphQL type for activity return information."""
    type: str
    description: str


@strawberry.type
class TestCoverage:
    """GraphQL type for test coverage information."""
    has_tests: bool
    test_count: int


@strawberry.type
class Activity:
    """GraphQL type for workflow activities."""
    id: str
    service: str
    name: str
    description: str
    task_queue: str
    timeout_seconds: int
    retry_attempts: int
    parameters: List[Parameter]
    returns: ReturnInfo
    test_coverage: Optional[TestCoverage] = None

    @classmethod
    def from_registry(cls, activity_id: str, metadata: Dict[str, Any]) -> "Activity":
        """Create Activity from registry metadata."""
        # Handle both old format (parameters list) and new format (input_schema)
        parameters = []
        
        if "parameters" in metadata:
            # Old format from static registry
            parameters = [
                Parameter(
                    name=param.get("name", ""),
                    type=param.get("type", "Any"),
                    description=param.get("description", ""),
                    required=param.get("required", True)
                )
                for param in metadata.get("parameters", [])
            ]
        elif "input_schema" in metadata:
            # New format from metadata endpoints
            input_schema = metadata.get("input_schema", {})
            properties = input_schema.get("properties", {})
            required_fields = input_schema.get("required", [])
            
            for param_name, param_data in properties.items():
                parameters.append(Parameter(
                    name=param_name,
                    type=param_data.get("type", "Any"),
                    description=param_data.get("description", ""),
                    required=param_name in required_fields
                ))
        
        returns_data = metadata.get("returns", {})
        if not returns_data and "output_schema" in metadata:
            # Use output_schema if returns is not present
            output_schema = metadata.get("output_schema", {})
            returns_data = {
                "type": output_schema.get("type", "Any"),
                "description": output_schema.get("description", "")
            }
        
        returns = ReturnInfo(
            type=returns_data.get("type", "Any"),
            description=returns_data.get("description", "")
        )
        
        test_cov_data = metadata.get("test_coverage", {})
        test_coverage = TestCoverage(
            has_tests=test_cov_data.get("has_tests", False),
            test_count=test_cov_data.get("test_count", 0)
        ) if test_cov_data else None
        
        return cls(
            id=activity_id,
            service=metadata.get("service", ""),
            name=metadata.get("name", ""),
            description=metadata.get("description", ""),
            task_queue=metadata.get("task_queue", ""),
            timeout_seconds=metadata.get("timeout_seconds", 300),
            retry_attempts=metadata.get("retry_attempts", 3),
            parameters=parameters,
            returns=returns,
            test_coverage=test_coverage
        )


@strawberry.type
class Service:
    """GraphQL type for services."""
    name: str
    activities: List[Activity]
    activity_count: int
    task_queue: Optional[str] = None
    worker_identity: Optional[str] = None
    temporal_status: Optional[str] = None
    health: Optional[str] = None


@strawberry.type
class ServiceDiscoveryInfo:
    """GraphQL type for service discovery information."""
    discovery_method: str
    services_discovered: int
    activities_discovered: int
    temporal_connected: bool
    metadata_endpoints_accessible: int


@strawberry.type
class PipelineStep:
    """GraphQL type for pipeline steps."""
    activity: str
    type: str
    service: Optional[str] = None
    input_transform: Optional[str] = None


@strawberry.type
class Pipeline:
    """GraphQL type for pipelines."""
    name: str
    description: str
    steps: List[PipelineStep]


@strawberry.type
class DiscoveryMetadata:
    """GraphQL type for discovery metadata."""
    discovery_method: str
    services_discovered: int
    activities_discovered: int
    pipelines_inferred: int


@strawberry.type
class Query:
    """GraphQL queries for service introspection using production discovery."""
    
    @strawberry.field
    def services(self) -> List[Service]:
        """Get all available services and their activities from production discovery."""
        try:
            # Get data from production discovery
            discovery_data = run_async(self._get_services_with_discovery_info())
            services_data = discovery_data.get("services", {})
            
            # Group activities by service
            services = []
            for service_name, service_info in services_data.items():
                activities = []
                for activity_name, activity_data in service_info.get("activities", {}).items():
                    qualified_name = f"{service_name}.{activity_name}"
                    metadata = {
                        "service": service_name,
                        "name": activity_name,
                        "description": activity_data.get("description", ""),
                        "task_queue": service_info.get("task_queue", ""),
                        "timeout_seconds": activity_data.get("timeout_seconds", 300),
                        "retry_attempts": activity_data.get("retry_attempts", 3),
                        "input_schema": activity_data.get("input_schema", {}),
                        "output_schema": activity_data.get("output_schema", {})
                    }
                    activities.append(Activity.from_registry(qualified_name, metadata))
                
                services.append(Service(
                    name=service_name,
                    activities=activities,
                    activity_count=len(activities),
                    task_queue=service_info.get("task_queue"),
                    worker_identity=service_info.get("worker_identity"),
                    temporal_status=service_info.get("temporal_status"),
                    health=service_info.get("health")
                ))
            
            return services
        except Exception as e:
            logger.error(f"Error fetching services: {e}")
            return []
    
    async def _get_services_with_discovery_info(self):
        """Helper to get services with discovery information."""
        discovery = await get_discovery_instance()
        
        # Get hybrid discovery (Temporal + Metadata)
        hybrid_results = await discovery.discover_hybrid_temporal_metadata()
        
        return {"services": hybrid_results}
    
    @strawberry.field
    def discovery_info(self) -> ServiceDiscoveryInfo:
        """Get information about the discovery process."""
        try:
            discovery_data = run_async(self._get_discovery_status())
            return ServiceDiscoveryInfo(
                discovery_method="Production (Temporal + Metadata)",
                services_discovered=discovery_data.get("services_count", 0),
                activities_discovered=discovery_data.get("activities_count", 0),
                temporal_connected=discovery_data.get("temporal_connected", False),
                metadata_endpoints_accessible=discovery_data.get("metadata_accessible", 0)
            )
        except Exception as e:
            logger.error(f"Error getting discovery info: {e}")
            return ServiceDiscoveryInfo(
                discovery_method="Error",
                services_discovered=0,
                activities_discovered=0,
                temporal_connected=False,
                metadata_endpoints_accessible=0
            )
    
    async def _get_discovery_status(self):
        """Get discovery status information."""
        discovery = await get_discovery_instance()
        
        # Test Temporal connection
        temporal_connected = False
        try:
            await discovery.discover_active_task_queues()
            temporal_connected = True
        except Exception:
            pass
        
        # Test metadata endpoints
        services_data = await discovery.discover_all_services_via_metadata()
        metadata_accessible = len(services_data)
        
        # Count activities
        activities_count = sum(
            len(service.get("activities", {})) 
            for service in services_data.values()
        )
        
        return {
            "services_count": len(services_data),
            "activities_count": activities_count,
            "temporal_connected": temporal_connected,
            "metadata_accessible": metadata_accessible
        }
    
    @strawberry.field
    def activity(self, id: str) -> Optional[Activity]:
        """Get details for a specific activity."""
        metadata = get_activity_metadata(id)
        if not metadata:
            return None
        
        return Activity.from_registry(id, metadata)
    
    @strawberry.field
    def activities_by_service(self, service_name: str) -> List[Activity]:
        """Get all activities for a specific service."""
        all_activities = get_all_activities()
        
        activities = []
        for activity_id, metadata in all_activities.items():
            if metadata.get("service") == service_name:
                activities.append(Activity.from_registry(activity_id, metadata))
        
        return activities
    
    @strawberry.field
    def search_activities(self, query: str) -> List[Activity]:
        """Search activities by name or description."""
        all_activities = get_all_activities()
        query_lower = query.lower()
        
        matching_activities = []
        for activity_id, metadata in all_activities.items():
            name = metadata.get("name", "").lower()
            description = metadata.get("description", "").lower()
            
            if query_lower in name or query_lower in description:
                matching_activities.append(Activity.from_registry(activity_id, metadata))
        
        return matching_activities
    
    @strawberry.field
    def temporal_status(self) -> List[str]:
        """Get list of active Temporal task queues."""
        try:
            return run_async(self._get_temporal_queues())
        except Exception as e:
            logger.error(f"Error getting Temporal status: {e}")
            return []
    
    async def _get_temporal_queues(self):
        """Get active Temporal task queues."""
        discovery = await get_discovery_instance()
        return await discovery.discover_active_task_queues()


@strawberry.type
class GenerateServicesYamlResponse:
    """Response type for services.yaml generation."""
    success: bool
    services_count: int
    activities_count: int
    pipelines_count: int
    yaml_content: Optional[str] = None
    error_message: Optional[str] = None


@strawberry.type
class Mutation:
    """GraphQL mutations for workflow composition using production discovery."""
    
    @strawberry.mutation
    def generate_services_yaml(self) -> GenerateServicesYamlResponse:
        """Generate services.yaml configuration using production discovery system."""
        try:
            return run_async(self._generate_services_yaml_async())
        except Exception as e:
            return GenerateServicesYamlResponse(
                success=False,
                services_count=0,
                activities_count=0,
                pipelines_count=0,
                error_message=str(e)
            )
    
    async def _generate_services_yaml_async(self):
        """Async implementation of services.yaml generation."""
        discovery = await get_discovery_instance()
        
        # Get comprehensive discovery data
        services_data = await discovery.discover_hybrid_temporal_metadata()
        
        if not services_data:
            return GenerateServicesYamlResponse(
                success=False,
                services_count=0,
                activities_count=0,
                pipelines_count=0,
                error_message="No services discovered"
            )
        
        # Convert to YAML-compatible format
        yaml_config = {
            "services": {}
        }
        
        activities_count = 0
        for service_name, service_data in services_data.items():
            service_activities = service_data.get("activities", {})
            activities_count += len(service_activities)
            
            yaml_config["services"][service_name] = {
                "task_queue": service_data.get("task_queue", f"{service_name}-queue"),
                "health": service_data.get("health", "unknown"),
                "version": service_data.get("version", "1.0.0"),
                "temporal_status": service_data.get("temporal_status", "unknown"),
                "activities": {}
            }
            
            for activity_name, activity_data in service_activities.items():
                yaml_config["services"][service_name]["activities"][activity_name] = {
                    "description": activity_data.get("description", ""),
                    "timeout_seconds": activity_data.get("timeout_seconds", 300),
                    "retry_attempts": activity_data.get("retry_attempts", 3),
                    "input_schema": activity_data.get("input_schema", {}),
                    "output_schema": activity_data.get("output_schema", {})
                }
        
        # Convert to YAML string
        import yaml
        yaml_content = yaml.dump(yaml_config, default_flow_style=False, sort_keys=False)
        
        return GenerateServicesYamlResponse(
            success=True,
            services_count=len(services_data),
            activities_count=activities_count,
            pipelines_count=0,  # Not implementing pipeline inference yet
            yaml_content=yaml_content
        )


# Create the schema
schema = strawberry.Schema(query=Query, mutation=Mutation)