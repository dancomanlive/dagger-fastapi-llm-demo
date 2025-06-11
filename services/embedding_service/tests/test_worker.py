"""
Test for embedding worker registration - Phase 1, Step 1.3 of TDD refactoring.

Tests that the Temporal worker correctly registers the embedding activity
and can be started to listen for activity executions.
"""

import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_embedding_worker_registers_activity():
    """
    Test that the embedding worker registers the perform_embedding_and_indexing_activity.
    
    We test the worker setup without actually running it (which would run indefinitely).
    """
    from worker import EMBEDDING_TASK_QUEUE
    from activities import perform_embedding_and_indexing_activity
    
    with patch('worker.Client.connect') as mock_connect, \
         patch('worker.Worker') as mock_worker_class: # Patch the Worker class
        # Setup the mocks
        mock_client = AsyncMock() # Client connect is async
        # Provide the _config attribute that Worker expects
        mock_client._config = {
            "namespace": "default",
            "interceptors": [],
            "build_id_override": None,
            "identity_override": None,
            # Add other keys if Worker initialization complains about them
        }
        mock_connect.return_value = mock_client
        
        mock_worker_instance = mock_worker_class.return_value # Get the instance from the patched class
        mock_worker_instance.run = AsyncMock(side_effect=KeyboardInterrupt("Stop for test"))
        
        # Call the worker setup function - expect it to be interrupted
        with pytest.raises(KeyboardInterrupt):
            from worker import run_worker
            await run_worker()
        
        # Assert Client.connect was called
        mock_connect.assert_called_once()
        
        # Assert Worker was instantiated with correct parameters
        mock_worker_class.assert_called_once()
        worker_call_args = mock_worker_class.call_args
        
        assert worker_call_args[0][0] == mock_client # First positional arg is the client
        assert worker_call_args[1]['task_queue'] == EMBEDDING_TASK_QUEUE
        
        # Check that activities list includes our activity
        activities = worker_call_args[1]['activities']
        assert perform_embedding_and_indexing_activity in activities
        
        # Assert worker.run was called to start the worker
        mock_worker_instance.run.assert_called_once()


@pytest.mark.asyncio
async def test_embedding_worker_configuration():
    """
    Test that the worker is configured with the correct task queue and settings.
    """
    from worker import EMBEDDING_TASK_QUEUE
    
    # Test that task queue constant is properly defined
    assert EMBEDDING_TASK_QUEUE == "embedding-task-queue"
    assert isinstance(EMBEDDING_TASK_QUEUE, str)
    assert len(EMBEDDING_TASK_QUEUE) > 0


@pytest.mark.asyncio 
async def test_worker_handles_connection_errors():
    """
    Test that worker setup handles connection errors gracefully.
    """
    from worker import run_worker
    
    with patch('worker.Client.connect', side_effect=Exception("Connection failed")):
        # Should raise the connection error
        with pytest.raises(Exception, match="Connection failed"):
            await run_worker()
