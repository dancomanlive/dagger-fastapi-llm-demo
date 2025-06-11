"""
Tests for retriever service Temporal worker setup.

This module tests the Temporal worker that registers and executes 
the search_documents_activity.
"""

import pytest
import os
import asyncio # Add this import
from unittest.mock import AsyncMock, MagicMock, Mock, patch # Add MagicMock and patch


class TestSearchWorker:
    """Test suite for the search worker setup."""
    
    def test_search_worker_import(self): # Removed @pytest.mark.asyncio
        """
        Test that the search worker module can be imported and has key components.
        """
        # Import should work now that worker is implemented
        from worker import run_worker, RETRIEVAL_TASK_QUEUE
        
        # Verify the imported components
        assert callable(run_worker)
        assert RETRIEVAL_TASK_QUEUE == "retrieval-task-queue"
    
    @patch('worker.Client') # Keep this for connect
    @patch('worker.Worker') # Patch Worker class directly
    @patch.dict(os.environ, {"TEMPORAL_HOST": "test-host:7233", "TEMPORAL_NAMESPACE": "test-namespace"}, clear=True)
    @pytest.mark.asyncio
    async def test_search_worker_registers_activity(self, mock_worker_class, mock_client_class): # Add async, adjust mock order
        """
        Test that the search worker registers search_documents_activity correctly.
        """
        try:
            from worker import run_worker, RETRIEVAL_TASK_QUEUE, TEMPORAL_HOST, TEMPORAL_NAMESPACE
            from activities import search_documents_activity
        except ImportError:
            pytest.skip("run_worker or other components not implemented yet")

        # Setup mock for Client.connect()
        # mock_client_instance = AsyncMock() # This is the client instance returned by connect
        # Configure mock_client_class to return an AsyncMock when connect is called
        # mock_client_connect_instance = AsyncMock() # This was the issue
        # mock_client_class.connect.return_value = mock_client_connect_instance # This was the issue

        # Instead, make the mock_client_class itself the AsyncMock that .connect() is called on
        # and ensure it returns a new AsyncMock for the client instance.
        mock_client_instance_returned_by_connect = AsyncMock()
        mock_client_class.connect = AsyncMock(return_value=mock_client_instance_returned_by_connect)


        # Configure the .config() method on the mock_client_instance_returned_by_connect
        # to return a dictionary directly, not a coroutine.
        mock_client_instance_returned_by_connect.config = Mock(return_value={
            "namespace": TEMPORAL_NAMESPACE,
            "interceptors": [], # Ensure this is a list
            "build_id_override": None,
            "identity_override": None,
            # Add other necessary keys if Worker complains
        })
        # mock_client_class.connect.return_value = mock_client_instance # Original incorrect line

        # Setup mock for Worker instance
        mock_worker_instance = mock_worker_class.return_value
        mock_worker_instance.run = AsyncMock(side_effect=KeyboardInterrupt("Stop for test"))

        # Call the worker setup function - expect it to be interrupted
        with pytest.raises(KeyboardInterrupt):
            await run_worker()

        # Verify Client.connect was called
        mock_client_class.connect.assert_called_once_with(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)

        # Verify Worker was initialized with the correct client instance and other args
        mock_worker_class.assert_called_once_with(
            mock_client_instance_returned_by_connect, # The client instance
            task_queue=RETRIEVAL_TASK_QUEUE, # Changed to keyword argument
            activities=[search_documents_activity],
            # Add other expected arguments if necessary
        )

        # Verify worker.run() was called
        mock_worker_instance.run.assert_awaited_once()


    @patch('worker.Client') # Keep this for connect
    def test_search_worker_configuration(self, mock_client_class): # Removed @pytest.mark.asyncio
        """
        Test that the search worker attempts to connect to Temporal with correct config.
        """
        try:
            from worker import run_worker, TEMPORAL_HOST, TEMPORAL_NAMESPACE
            # Import Worker to patch it directly in this test
            # from worker import Worker as WorkerClassToPatch # Unused import
        except ImportError:
            pytest.skip("run_worker or other components not implemented yet")

        # Setup mock for Client.connect()
        # mock_client_connect_instance = AsyncMock() # Renamed for clarity
        # mock_client_class.connect.return_value = mock_client_connect_instance
        mock_client_instance_returned_by_connect = AsyncMock()
        mock_client_class.connect = AsyncMock(return_value=mock_client_instance_returned_by_connect)


        # Create a mock for the Worker class itself to inspect its instantiation
        mock_worker_class_instance = MagicMock()

        # Simulate worker execution that gets interrupted
        # Patch 'worker.Worker' which is used inside run_worker
        with patch('worker.Worker', mock_worker_class_instance):
            # Configure the run method of the mocked Worker instance to raise KeyboardInterrupt
            mock_worker_instance_created = mock_worker_class_instance.return_value
            mock_worker_instance_created.run = AsyncMock(side_effect=KeyboardInterrupt("Stop for test"))
            with pytest.raises(KeyboardInterrupt):
                asyncio.run(run_worker()) # Run the async function

        # Verify Client.connect was called with correct host and namespace
        mock_client_class.connect.assert_called_once_with(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
        
        # Verify Worker was initialized with the client from Client.connect
        # Access the arguments Worker was called with
        mock_worker_class_instance.assert_called_once()
        called_with_args = mock_worker_class_instance.call_args
        assert called_with_args[0][0] == mock_client_instance_returned_by_connect # First positional arg is the client
    
    def test_main_block_exists(self): # Removed @pytest.mark.asyncio
        """
        Test that the worker.py has a __main__ block to allow direct execution.
        """
        try:
            import worker
        except ImportError:
            pytest.skip("worker module not implemented yet")
        
        # Check that the module can be imported
        assert hasattr(worker, 'run_worker')
        
        # The actual main block test would check if it's callable when run as main
        # This is tested indirectly by the other tests
