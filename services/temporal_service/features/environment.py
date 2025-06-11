"""
Behave environment setup for Temporal service integration tests.

This file sets up the test environment, including starting/stopping 
Temporal workers and services needed for integration testing.
"""

import asyncio
import logging

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def before_all(context):
    """Set up before all tests."""
    logger.info("Setting up Behave test environment for Temporal service")
    context.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(context.loop)
    
    # We'll use Temporal's test environment for integration tests
    context.temporal_env = None
    context.client = None
    context.worker = None
    

def before_scenario(context, scenario):
    """Set up before each scenario."""
    logger.info(f"Starting scenario: {scenario.name}")
    

def after_scenario(context, scenario):
    """Clean up after each scenario."""
    logger.info(f"Finished scenario: {scenario.name}")
    if hasattr(context, 'workflow_handle') and context.workflow_handle:
        # Cancel any running workflows
        try:
            context.loop.run_until_complete(context.workflow_handle.cancel())
        except Exception:
            pass  # Workflow might already be done


def after_all(context):
    """Clean up after all tests."""
    logger.info("Tearing down Behave test environment")
    if context.loop and not context.loop.is_closed():
        context.loop.close()
