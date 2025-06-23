#!/usr/bin/env python3
"""
Production-Style Temporal + Metadata Discovery for Docker Environment

This demonstrates how service discovery would work in production by:
1. Querying Temporal for active task queues and workers
2. Querying worker metadata endpoints for activity details  
3. Combining both to generate complete service configuration

This approach is much more realistic than GraphQL simulation.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any
import aiohttp
from temporalio.client import Client
from temporalio.api.workflowservice.v1 import DescribeTaskQueueRequest
from temporalio.api.enums.v1 import TaskQueueType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionTemporalDiscovery:
    """
    Production-style service discovery using Temporal APIs + worker metadata endpoints.
    
    This class demonstrates realistic service discovery for containerized environments.
    """
    
    def __init__(self, temporal_host: str = "localhost:7233", namespace: str = "default"):
        self.temporal_host = temporal_host
        self.namespace = namespace
        self.client = None
    
    async def connect(self):
        """Connect to Temporal server"""
        self.client = await Client.connect(self.temporal_host, namespace=self.namespace)
        logger.info(f"✅ Connected to Temporal at {self.temporal_host}")
    
    async def discover_active_task_queues(self) -> List[str]:
        """
        Dynamically discover active task queues by checking service metadata.
        No hardcoded queue names - derives them from running services.
        """
        
        # First, get all services and their declared task queues
        services_metadata = await self.discover_all_services_via_metadata()
        potential_queues = set()
        
        # Extract task queue names from service metadata
        for service_name, service_data in services_metadata.get("services", {}).items():
            task_queue = service_data.get("task_queue")
            if task_queue:
                potential_queues.add(task_queue)
                logger.debug(f"Found task queue '{task_queue}' from {service_name} metadata")
        
        # Also try common naming patterns based on discovered services
        for service_name in services_metadata.get("services", {}):
            # Convert service names to likely queue names
            potential_patterns = [
                f"{service_name}-task-queue",
                f"{service_name.replace('_', '-')}-task-queue", 
                f"{service_name}-queue",
                f"{service_name.replace('_service', '')}-task-queue"
            ]
            potential_queues.update(potential_patterns)
        
        logger.info(f"🔍 Checking {len(potential_queues)} dynamically discovered task queues...")
        logger.debug(f"Queue candidates: {sorted(potential_queues)}")
        
        active_queues = []
        
        for queue_name in potential_queues:
            try:
                request = DescribeTaskQueueRequest(
                    namespace=self.namespace,
                    task_queue={"name": queue_name},
                    task_queue_type=TaskQueueType.TASK_QUEUE_TYPE_ACTIVITY
                )
                
                response = await self.client.workflow_service.describe_task_queue(request)
                
                # Check if there are active workers
                if hasattr(response, 'pollers') and response.pollers:
                    active_queues.append(queue_name)
                    worker_count = len(response.pollers)
                    logger.info(f"✅ Active queue: {queue_name} ({worker_count} workers)")
                else:
                    logger.debug(f"❌ Queue {queue_name} has no workers")
                
            except Exception as e:
                logger.debug(f"❌ Queue {queue_name} not available: {e}")
        
        return active_queues
    
    async def discover_worker_metadata(self, service_host: str, service_port: int) -> Dict[str, Any]:
        """
        Discover worker metadata by querying the worker's HTTP metadata endpoint.
        
        This is how production discovery would work - each service exposes
        its own metadata endpoint for dynamic discovery.
        """
        try:
            url = f"http://{service_host}:{service_port}/metadata"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        metadata = await response.json()
                        logger.info(f"✅ Retrieved metadata from {service_host}:{service_port}")
                        return metadata
                    else:
                        logger.warning(f"❌ HTTP {response.status} from {service_host}:{service_port}")
                        return {}
        except Exception as e:
            logger.warning(f"❌ Failed to connect to {service_host}:{service_port}: {e}")
            return {}
    
    async def discover_all_services_via_metadata(self) -> Dict[str, Any]:
        """
        Discover all services by querying their metadata endpoints.
        
        In Docker environment, we query the container hostnames.
        In production, this would come from service discovery registry.
        """
        
        # Known service endpoints (using localhost for local development)
        service_endpoints = [
            {"name": "embedding-service", "host": "localhost", "port": 8082},
            {"name": "retriever-service", "host": "localhost", "port": 8083},
            # Add more services as they expose metadata endpoints
        ]
        
        services_config = {"services": {}}
        
        for endpoint in service_endpoints:
            logger.info(f"🔍 Discovering {endpoint['name']} at {endpoint['host']}:{endpoint['port']}")
            
            metadata = await self.discover_worker_metadata(endpoint['host'], endpoint['port'])
            
            if metadata and "activities" in metadata:
                service_name = metadata.get("service_name", endpoint['name'])
                
                services_config["services"][service_name] = {
                    "task_queue": metadata.get("task_queue"),
                    "worker_identity": metadata.get("worker_identity"),
                    "health": metadata.get("health"),
                    "version": metadata.get("version"),
                    "activities": {}
                }
                
                # Process activities
                for activity in metadata["activities"]:
                    activity_name = activity["name"]
                    services_config["services"][service_name]["activities"][activity_name] = {
                        "description": activity["description"],
                        "timeout_seconds": activity["timeout_seconds"],
                        "retry_attempts": activity["retry_attempts"],
                        "parameters": activity["parameters"],
                        "returns": activity["returns"]
                    }
                
                logger.info(f"✅ Discovered {service_name} with {len(metadata['activities'])} activities")
            else:
                logger.warning(f"❌ No metadata found for {endpoint['name']}")
        
        return services_config
    
    async def discover_hybrid_temporal_metadata(self) -> Dict[str, Any]:
        """
        Combine Temporal discovery with metadata endpoints for complete picture.
        
        This is the most realistic production approach:
        1. Use Temporal to find active task queues and workers
        2. Use metadata endpoints to get detailed activity information
        3. Cross-reference to build complete service configuration
        """
        
        logger.info("🔍 Starting hybrid Temporal + Metadata discovery...")
        
        # Step 1: Discover active task queues via Temporal
        active_queues = await self.discover_active_task_queues()
        
        # Step 2: Discover services via metadata endpoints
        metadata_services = await self.discover_all_services_via_metadata()
        
        # Step 3: Cross-reference and build complete picture
        combined_config = {"services": {}}
        
        for service_name, service_data in metadata_services["services"].items():
            combined_config["services"][service_name] = service_data
            
            # Add Temporal verification status
            task_queue = service_data.get("task_queue")
            if task_queue in active_queues:
                combined_config["services"][service_name]["temporal_status"] = "active"
                logger.info(f"✅ {service_name} verified active in Temporal")
            else:
                combined_config["services"][service_name]["temporal_status"] = "inactive"
                logger.warning(f"⚠️  {service_name} metadata found but not active in Temporal")
        
        return combined_config


async def main():
    """Demonstrate production-style discovery with Docker containers"""
    
    print("🔍 Production-Style Discovery: Temporal + Worker Metadata")
    print("=" * 60)
    
    discovery = ProductionTemporalDiscovery()
    await discovery.connect()
    
    print("\n1. Testing Temporal task queue discovery...")
    active_queues = await discovery.discover_active_task_queues()
    print(f"   Found {len(active_queues)} active queues: {active_queues}")
    
    print("\n2. Testing metadata endpoint discovery...")
    metadata_config = await discovery.discover_all_services_via_metadata()
    print(f"   Found {len(metadata_config['services'])} services via metadata")
    
    for service_name, service_data in metadata_config['services'].items():
        print(f"     - {service_name}: {len(service_data.get('activities', {}))} activities")
    
    print("\n3. Testing hybrid discovery (Temporal + Metadata)...")
    hybrid_config = await discovery.discover_hybrid_temporal_metadata()
    
    print(f"   Complete discovery results:")
    for service_name, service_data in hybrid_config['services'].items():
        status = service_data.get('temporal_status', 'unknown')
        activity_count = len(service_data.get('activities', {}))
        print(f"     - {service_name}: {activity_count} activities, Temporal: {status}")
    
    print("\n4. Generated services.yaml equivalent:")
    print(json.dumps(hybrid_config, indent=2))
    
    print("\n🎯 This demonstrates realistic production discovery!")
    print("   - Temporal APIs for worker/queue status")
    print("   - HTTP metadata endpoints for activity details") 
    print("   - No static configuration files needed")
    print("   - Cross-referenced for verification")


if __name__ == "__main__":
    asyncio.run(main())
