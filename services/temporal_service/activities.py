"""
Temporal activities for document processing pipeline.
"""

import logging
from typing import Any
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def health_check_activity(input_data: Any = None) -> str:
    """Simple health check activity."""
    return "Activity worker is healthy"
