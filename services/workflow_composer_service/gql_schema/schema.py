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
        await _discovery_instance.connect()
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
        parameters = [
            Parameter(
                name=param.get("name", ""),
                type=param.get("type", "Any"),
                description=param.get("description", ""),
                required=param.get("required", True)
            )
            for param in metadata.get("parameters", [])
        ]
        
        returns_data = metadata.get("returns", {})
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
    health: Optional[str] = None
    version: Optional[str] = None
    temporal_status: Optional[str] = None


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
class ServiceDiscoveryInfo:
    """GraphQL type for service discovery information."""
    discovery_method: str
    services_discovered: int
    activities_discovered: int
    temporal_connected: bool
    metadata_endpoints_accessible: int


# Global cache for discovery data to avoid rate limiting and redundant calls
_discovery_cache = None
_cache_timestamp = None
CACHE_TTL_SECONDS = 30  # Cache for 30 seconds

async def get_services_with_discovery_info():
    """Helper to get services with discovery information, using cache to avoid rate limits."""
    global _discovery_cache, _cache_timestamp
    import time
    
    current_time = time.time()
    
    # Check if we have valid cached data
    if (_discovery_cache is not None and 
        _cache_timestamp is not None and 
        current_time - _cache_timestamp < CACHE_TTL_SECONDS):
        logger.info("Using cached discovery data to avoid rate limits")
        return _discovery_cache
    
    # Make fresh discovery call
    logger.info("Making fresh discovery call...")
    discovery = await get_discovery_instance()
    
    # Get hybrid discovery (Temporal + Metadata)
    hybrid_results = await discovery.discover_hybrid_temporal_metadata()
    
    # Cache the results
    _discovery_cache = hybrid_results
    _cache_timestamp = current_time
    
    return hybrid_results

async def get_discovery_status():
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
    services = services_data.get("services", {})
    metadata_accessible = len(services)
    
    # Count activities
    activities_count = sum(
        len(service.get("activities", {})) 
        for service in services.values()
    )
    
    return {
        "services_count": len(services),
        "activities_count": activities_count,
        "temporal_connected": temporal_connected,
        "metadata_accessible": metadata_accessible
    }

async def get_temporal_queues():
    """Get active Temporal task queues from already-discovered services to avoid rate limits."""
    try:
        # Get the services data which includes task queues
        discovery_data = await get_services_with_discovery_info()
        services_data = discovery_data.get("services", {})
        
        # Extract unique task queues from discovered services
        task_queues = set()
        for service_name, service_info in services_data.items():
            task_queue = service_info.get("task_queue")
            if task_queue and service_info.get("temporal_status") == "active":
                task_queues.add(task_queue)
        
        result = list(task_queues)
        logger.info(f"Extracted temporal queues from discovered services: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error extracting temporal queues: {e}")
        return []


@strawberry.type
class Query:
    """GraphQL queries for service introspection using production discovery."""
    
    @strawberry.field
    def services(self) -> List[Service]:
        """Get all available services and their activities from production discovery."""
        try:
            # Get data from production discovery
            discovery_data = run_async(get_services_with_discovery_info())
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
                        "parameters": activity_data.get("parameters", []),
                        "returns": activity_data.get("returns", {})
                    }
                    activities.append(Activity.from_registry(qualified_name, metadata))
                
                services.append(Service(
                    name=service_name,
                    activities=activities,
                    activity_count=len(activities),
                    task_queue=service_info.get("task_queue"),
                    worker_identity=service_info.get("worker_identity"),
                    temporal_status=service_info.get("temporal_status"),
                    health=service_info.get("health"),
                    version=service_info.get("version")
                ))
            
            return services
        except Exception as e:
            logger.error(f"Error fetching services: {e}")
            # Return empty list if production discovery fails
            return []
    
    @strawberry.field
    def discovery_info(self) -> ServiceDiscoveryInfo:
        """Get information about the discovery process."""
        try:
            discovery_data = run_async(get_discovery_status())
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
    
    @strawberry.field
    def temporal_status(self) -> List[str]:
        """Get list of active Temporal task queues."""
        try:
            queues = run_async(get_temporal_queues())
            logger.info(f"Temporal status query returning: {queues}")
            return queues
        except Exception as e:
            logger.error(f"Error getting Temporal status: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @strawberry.field
    def activity(self, id: str) -> Optional[Activity]:
        """Get details for a specific activity."""
        try:
            # Parse activity ID (format: service_name.activity_name)
            if "." not in id:
                return None
                
            service_name, activity_name = id.split(".", 1)
            
            # Get discovery data (will use cache if available)
            discovery_data = run_async(get_services_with_discovery_info())
            services_data = discovery_data.get("services", {})
            
            if service_name in services_data:
                service_info = services_data[service_name]
                activities = service_info.get("activities", {})
                
                if activity_name in activities:
                    activity_data = activities[activity_name]
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
                    return Activity.from_registry(id, metadata)
            
            return None
        except Exception as e:
            logger.error(f"Error fetching activity {id}: {e}")
            return None
    
    @strawberry.field
    def activities_by_service(self, service_name: str) -> List[Activity]:
        """Get all activities for a specific service."""
        try:
            # Get discovery data (will use cache if available)
            discovery_data = run_async(get_services_with_discovery_info())
            services_data = discovery_data.get("services", {})
            
            activities = []
            if service_name in services_data:
                service_info = services_data[service_name]
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
            
            return activities
        except Exception as e:
            logger.error(f"Error fetching activities for service {service_name}: {e}")
            return []
    
    @strawberry.field
    def search_activities(self, query: str) -> List[Activity]:
        """Search activities by name or description."""
        try:
            # Get discovery data (will use cache if available)
            discovery_data = run_async(get_services_with_discovery_info())
            services_data = discovery_data.get("services", {})
            query_lower = query.lower()
            
            matching_activities = []
            for service_name, service_info in services_data.items():
                for activity_name, activity_data in service_info.get("activities", {}).items():
                    description = activity_data.get("description", "")
                    if (query_lower in activity_name.lower() or 
                        query_lower in description.lower()):
                        
                        qualified_name = f"{service_name}.{activity_name}"
                        metadata = {
                            "service": service_name,
                            "name": activity_name,
                            "description": description,
                            "task_queue": service_info.get("task_queue", ""),
                            "timeout_seconds": activity_data.get("timeout_seconds", 300),
                            "retry_attempts": activity_data.get("retry_attempts", 3),
                            "input_schema": activity_data.get("input_schema", {}),
                            "output_schema": activity_data.get("output_schema", {})
                        }
                        matching_activities.append(Activity.from_registry(qualified_name, metadata))
            
            return matching_activities
        except Exception as e:
            logger.error(f"Error searching activities with query '{query}': {e}")
            return []


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
    """GraphQL mutations for workflow composition."""
    
    @strawberry.mutation
    def generate_services_yaml(self, introspect_path: str = "../") -> GenerateServicesYamlResponse:
        """Generate services.yaml configuration by introspecting actual services via HTTP GraphQL API."""
        try:
            # Import here to avoid circular imports
            from agents.tools.dynamic_yaml_generation import generate_services_yaml_from_graphql
            import yaml
            
            # Generate configuration using HTTP requests to GraphQL API
            logger.info("Generating YAML via HTTP GraphQL API...")
            config = generate_services_yaml_from_graphql()
            
            if "error" in config:
                return GenerateServicesYamlResponse(
                    success=False,
                    services_count=0,
                    activities_count=0,
                    pipelines_count=0,
                    error_message=config["error"]
                )
            
            # Convert to YAML string
            yaml_content = yaml.dump(
                {k: v for k, v in config.items() if k != "discovery_metadata"},
                default_flow_style=False,
                sort_keys=False
            )
            
            metadata = config.get("discovery_metadata", {})
            
            return GenerateServicesYamlResponse(
                success=True,
                services_count=metadata.get("services_discovered", 0),
                activities_count=metadata.get("activities_discovered", 0),
                pipelines_count=metadata.get("pipelines_inferred", 0),
                yaml_content=yaml_content
            )
            
        except Exception as e:
            logger.error(f"Error generating services YAML: {e}")
            import traceback
            traceback.print_exc()
            return GenerateServicesYamlResponse(
                success=False,
                services_count=0,
                activities_count=0,
                pipelines_count=0,
                error_message=str(e)
            )


# Create the schema
schema = strawberry.Schema(query=Query, mutation=Mutation)