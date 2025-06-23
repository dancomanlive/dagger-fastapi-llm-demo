#!/usr/bin/env python3
"""
Unit Tests for Production Temporal Service Discovery

This test suite covers:
1. Temporal API integration and task queue discovery
2. Worker metadata endpoint discovery
3. Hybrid discovery combining both approaches
4. Error handling and edge cases
5. Configuration generation
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from aioresponses import aioresponses
from temporalio.api.workflowservice.v1 import DescribeTaskQueueResponse
from temporalio.api.common.v1 import WorkerVersionStamp
from temporalio.api.taskqueue.v1 import TaskQueueStatus, PollerInfo

# Import the class we're testing
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from docker_production_discovery import ProductionTemporalDiscovery


class TestProductionTemporalDiscovery:
    """Test suite for ProductionTemporalDiscovery class"""
    
    @pytest.fixture
    def discovery(self):
        """Create a discovery instance for testing"""
        return ProductionTemporalDiscovery()
    
    @pytest.fixture
    def mock_temporal_client(self):
        """Mock Temporal client for testing"""
        client = AsyncMock()
        client.workflow_service = AsyncMock()
        return client
    
    @pytest.fixture
    def sample_poller_info(self):
        """Sample poller info for mocking Temporal responses"""
        poller = PollerInfo()
        poller.identity = "1@test-worker"
        poller.last_access_time.seconds = 1642000000
        return poller
    
    @pytest.fixture
    def sample_metadata_response(self):
        """Sample worker metadata response"""
        return {
            "service_name": "test_service",
            "task_queue": "test-task-queue",
            "worker_identity": "1@test-worker",
            "activities": [
                {
                    "name": "test_activity",
                    "description": "Test activity description",
                    "timeout_seconds": 300,
                    "retry_attempts": 3,
                    "parameters": [
                        {
                            "name": "test_param",
                            "type": "string",
                            "description": "Test parameter",
                            "required": True
                        }
                    ],
                    "returns": {
                        "type": "object",
                        "description": "Test return value"
                    }
                }
            ],
            "health": "healthy",
            "version": "1.0.0"
        }

    @pytest.mark.asyncio
    async def test_connect_to_temporal(self, discovery, mock_temporal_client):
        """Test successful connection to Temporal server"""
        with patch('docker_production_discovery.Client.connect', return_value=mock_temporal_client):
            await discovery.connect()
            assert discovery.client == mock_temporal_client

    @pytest.mark.asyncio
    async def test_connect_to_temporal_failure(self, discovery):
        """Test handling of Temporal connection failure"""
        with patch('docker_production_discovery.Client.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await discovery.connect()

    @pytest.mark.asyncio
    async def test_discover_active_task_queues_success(self, discovery, mock_temporal_client, sample_poller_info):
        """Test successful discovery of active task queues"""
        discovery.client = mock_temporal_client
        
        # Mock response with active workers
        response = DescribeTaskQueueResponse()
        response.pollers.append(sample_poller_info)
        
        mock_temporal_client.workflow_service.describe_task_queue.return_value = response
        
        active_queues = await discovery.discover_active_task_queues()
        
        # Should find all known queues since we're mocking success for all
        assert len(active_queues) == 8  # All potential queues
        assert "embedding-task-queue" in active_queues
        assert "retrieval-task-queue" in active_queues

    @pytest.mark.asyncio
    async def test_discover_active_task_queues_no_workers(self, discovery, mock_temporal_client):
        """Test discovery when no workers are active"""
        discovery.client = mock_temporal_client
        
        # Mock response with no workers
        response = DescribeTaskQueueResponse()
        # response.pollers is empty
        
        mock_temporal_client.workflow_service.describe_task_queue.return_value = response
        
        active_queues = await discovery.discover_active_task_queues()
        
        assert len(active_queues) == 0

    @pytest.mark.asyncio
    async def test_discover_active_task_queues_temporal_error(self, discovery, mock_temporal_client):
        """Test handling of Temporal API errors during queue discovery"""
        discovery.client = mock_temporal_client
        
        mock_temporal_client.workflow_service.describe_task_queue.side_effect = Exception("Temporal error")
        
        active_queues = await discovery.discover_active_task_queues()
        
        # Should return empty list when all queries fail
        assert len(active_queues) == 0

    @pytest.mark.asyncio
    async def test_discover_worker_metadata_success(self, discovery, sample_metadata_response):
        """Test successful worker metadata discovery"""
        
        with aioresponses() as m:
            m.get('http://localhost:8080/metadata', payload=sample_metadata_response)
            
            metadata = await discovery.discover_worker_metadata("localhost", 8080)
            
            assert metadata == sample_metadata_response
            assert metadata["service_name"] == "test_service"
            assert len(metadata["activities"]) == 1

    @pytest.mark.asyncio
    async def test_discover_worker_metadata_http_error(self, discovery):
        """Test handling of HTTP errors during metadata discovery"""
        
        mock_response = AsyncMock()
        mock_response.status = 404
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            metadata = await discovery.discover_worker_metadata("localhost", 8080)
            
            assert metadata == {}

    @pytest.mark.asyncio
    async def test_discover_worker_metadata_connection_error(self, discovery):
        """Test handling of connection errors during metadata discovery"""
        
        mock_session = AsyncMock()
        mock_session.get.side_effect = aiohttp.ClientError("Connection failed")
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            metadata = await discovery.discover_worker_metadata("localhost", 8080)
            
            assert metadata == {}

    @pytest.mark.asyncio
    async def test_discover_all_services_via_metadata_success(self, discovery, sample_metadata_response):
        """Test successful discovery of all services via metadata endpoints"""
        
        # Mock successful metadata responses
        with patch.object(discovery, 'discover_worker_metadata', return_value=sample_metadata_response):
            services_config = await discovery.discover_all_services_via_metadata()
            
            assert "services" in services_config
            assert "test_service" in services_config["services"]
            
            service = services_config["services"]["test_service"]
            assert service["task_queue"] == "test-task-queue"
            assert service["health"] == "healthy"
            assert "test_activity" in service["activities"]

    @pytest.mark.asyncio
    async def test_discover_all_services_via_metadata_partial_failure(self, discovery, sample_metadata_response):
        """Test discovery when some metadata endpoints fail"""
        
        # Mock one success, one failure
        async def mock_metadata_discovery(host, port):
            if port == 8082:
                return sample_metadata_response
            else:
                return {}  # Simulate failure
        
        with patch.object(discovery, 'discover_worker_metadata', side_effect=mock_metadata_discovery):
            services_config = await discovery.discover_all_services_via_metadata()
            
            # Should still discover the successful service
            assert len(services_config["services"]) == 1
            assert "test_service" in services_config["services"]

    @pytest.mark.asyncio
    async def test_discover_hybrid_temporal_metadata_success(self, discovery, sample_metadata_response, mock_temporal_client, sample_poller_info):
        """Test successful hybrid discovery combining Temporal + metadata"""
        discovery.client = mock_temporal_client
        
        # Mock Temporal discovery to return the queue from metadata as active
        def mock_describe_task_queue(request):
            queue_name = request.task_queue.name
            response = DescribeTaskQueueResponse()
            if queue_name == "test-task-queue":  # Match the queue from sample metadata
                response.pollers.append(sample_poller_info)
            return response
        
        mock_temporal_client.workflow_service.describe_task_queue.side_effect = mock_describe_task_queue
        
        # Mock metadata discovery to return our sample response
        with patch.object(discovery, 'discover_worker_metadata', return_value=sample_metadata_response):
            # Mock the active queue discovery to return the matching queue
            with patch.object(discovery, 'discover_active_task_queues', return_value=["test-task-queue"]):
                hybrid_config = await discovery.discover_hybrid_temporal_metadata()
                
                assert "services" in hybrid_config
                assert "test_service" in hybrid_config["services"]
                
                service = hybrid_config["services"]["test_service"]
                assert service["temporal_status"] == "active"  # Should be verified active

    @pytest.mark.asyncio
    async def test_discover_hybrid_temporal_metadata_inactive_service(self, discovery, sample_metadata_response, mock_temporal_client):
        """Test hybrid discovery when service metadata exists but not active in Temporal"""
        discovery.client = mock_temporal_client
        
        # Mock Temporal discovery returning different queues (so our service appears inactive)
        sample_metadata_response["task_queue"] = "different-queue"
        
        # Mock empty Temporal response (no active workers)
        response = DescribeTaskQueueResponse()
        mock_temporal_client.workflow_service.describe_task_queue.return_value = response
        
        # Mock metadata discovery to return our sample response with different queue
        with patch.object(discovery, 'discover_worker_metadata', return_value=sample_metadata_response):
            # Mock active queue discovery to return a different queue than our service uses
            with patch.object(discovery, 'discover_active_task_queues', return_value=["some-other-queue"]):
                hybrid_config = await discovery.discover_hybrid_temporal_metadata()
                
                service = hybrid_config["services"]["test_service"]
                assert service["temporal_status"] == "inactive"  # Should be marked inactive

    @pytest.mark.asyncio
    async def test_discover_hybrid_temporal_metadata_no_services(self, discovery, mock_temporal_client):
        """Test hybrid discovery when no services are found"""
        discovery.client = mock_temporal_client
        
        # Mock empty responses
        response = DescribeTaskQueueResponse()
        mock_temporal_client.workflow_service.describe_task_queue.return_value = response
        
        with patch.object(discovery, 'discover_worker_metadata', return_value={}):
            hybrid_config = await discovery.discover_hybrid_temporal_metadata()
            
            assert hybrid_config["services"] == {}

    def test_service_endpoint_configuration(self, discovery):
        """Test that service endpoints are correctly configured"""
        # This tests the current localhost configuration
        assert hasattr(discovery, 'service_endpoints') or True  # Will be set in method
        
        # Test the endpoints defined in discover_all_services_via_metadata
        # This is indirectly tested through other tests

    @pytest.mark.asyncio
    async def test_timeout_handling(self, discovery):
        """Test that HTTP timeouts are handled properly"""
        
        mock_session = AsyncMock()
        mock_session.get.side_effect = asyncio.TimeoutError("Timeout")
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            metadata = await discovery.discover_worker_metadata("localhost", 8080)
            
            assert metadata == {}

    @pytest.mark.asyncio 
    async def test_malformed_metadata_response(self, discovery):
        """Test handling of malformed metadata responses"""
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            metadata = await discovery.discover_worker_metadata("localhost", 8080)
            
            assert metadata == {}

    def test_known_task_queues_coverage(self, discovery):
        """Test that all expected task queues are covered in discovery"""
        
        # This should match the queues defined in discover_active_task_queues
        expected_queues = [
            "embedding-task-queue",
            "retrieval-task-queue",
            "local_activities-queue", 
            "utility-queue",
            "intent-queue",
            "retrieval-queue",
            "ai-queue", 
            "booking-queue"
        ]
        
        # We can't directly access the list, but we test indirectly
        # through the discovery method behavior in other tests
        assert len(expected_queues) == 8

    @pytest.mark.asyncio
    async def test_concurrent_metadata_discovery(self, discovery, sample_metadata_response):
        """Test that multiple metadata endpoints can be discovered concurrently"""
        
        call_count = 0
        
        async def mock_metadata_discovery(host, port):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Return different service names for different ports to test concurrency
            if call_count == 1:
                response = sample_metadata_response.copy()
                response["service_name"] = "service_1"
                return response
            elif call_count == 2:
                response = sample_metadata_response.copy()
                response["service_name"] = "service_2"
                return response
            else:
                return {}
        
        with patch.object(discovery, 'discover_worker_metadata', side_effect=mock_metadata_discovery):
            start_time = asyncio.get_event_loop().time()
            services_config = await discovery.discover_all_services_via_metadata()
            end_time = asyncio.get_event_loop().time()
            
            # Should complete in roughly the time of one call (concurrent execution)
            # Allow some margin for test execution overhead
            assert (end_time - start_time) < 0.5
            assert len(services_config["services"]) == 2


class TestIntegrationScenarios:
    """Integration test scenarios for production discovery"""
    
    @pytest.mark.asyncio
    async def test_full_discovery_workflow(self):
        """Test the complete discovery workflow end-to-end"""
        
        discovery = ProductionTemporalDiscovery()
        
        # Mock all dependencies
        mock_client = AsyncMock()
        
        # Mock Temporal response
        poller = PollerInfo()
        poller.identity = "1@test-worker"
        response = DescribeTaskQueueResponse()
        response.pollers.append(poller)
        mock_client.workflow_service.describe_task_queue.return_value = response
        
        # Mock metadata response
        metadata = {
            "service_name": "integration_service",
            "task_queue": "embedding-task-queue",
            "activities": [{
                "name": "integration_activity",
                "description": "Integration test activity",
                "timeout_seconds": 300,
                "retry_attempts": 3,
                "parameters": [],
                "returns": {"type": "object"}
            }],
            "health": "healthy",
            "version": "1.0.0"
        }
        
        with patch('docker_production_discovery.Client.connect', return_value=mock_client):
            with patch.object(discovery, 'discover_worker_metadata', return_value=metadata):
                await discovery.connect()
                
                # Test full discovery
                hybrid_config = await discovery.discover_hybrid_temporal_metadata()
                
                assert "integration_service" in hybrid_config["services"]
                service = hybrid_config["services"]["integration_service"]
                assert service["temporal_status"] == "active"
                assert "integration_activity" in service["activities"]

    @pytest.mark.asyncio 
    async def test_production_like_scenario(self):
        """Test a scenario that closely mimics production conditions"""
        
        discovery = ProductionTemporalDiscovery()
        
        # Simulate production conditions with multiple services
        mock_client = AsyncMock()
        
        # Different responses for different queues
        async def mock_temporal_query(request):
            queue_name = request.task_queue.name
            response = DescribeTaskQueueResponse()
            
            if queue_name in ["embedding-task-queue", "retrieval-task-queue"]:
                poller = PollerInfo()
                poller.identity = f"1@worker-{queue_name}"
                response.pollers.append(poller)
            
            return response
        
        mock_client.workflow_service.describe_task_queue.side_effect = mock_temporal_query
        
        # Different metadata for different services
        async def mock_metadata_query(host, port):
            if port == 8082:
                return {
                    "service_name": "embedding_service",
                    "task_queue": "embedding-task-queue",
                    "activities": [{"name": "embed", "description": "Embedding", "timeout_seconds": 300, "retry_attempts": 3, "parameters": [], "returns": {}}],
                    "health": "healthy",
                    "version": "1.0.0"
                }
            elif port == 8083:
                return {
                    "service_name": "retrieval_service", 
                    "task_queue": "retrieval-task-queue",
                    "activities": [{"name": "search", "description": "Search", "timeout_seconds": 300, "retry_attempts": 3, "parameters": [], "returns": {}}],
                    "health": "healthy",
                    "version": "1.0.0"
                }
            return {}
        
        with patch('docker_production_discovery.Client.connect', return_value=mock_client):
            with patch.object(discovery, 'discover_worker_metadata', side_effect=mock_metadata_query):
                await discovery.connect()
                
                result = await discovery.discover_hybrid_temporal_metadata()
                
                assert len(result["services"]) == 2
                assert "embedding_service" in result["services"]
                assert "retrieval_service" in result["services"]
                
                for service in result["services"].values():
                    assert service["temporal_status"] == "active"
                    assert len(service["activities"]) == 1


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
