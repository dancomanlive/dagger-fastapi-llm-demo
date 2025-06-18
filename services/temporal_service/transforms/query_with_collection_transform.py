from typing import Any, List, Dict
from .base_transform import BaseTransform
from temporalio import workflow

# Import normalization from the same service directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from normalization import normalize_query_input, simple_query_transform

class QueryWithCollectionTransform(BaseTransform):
    def transform(self, data: Any, step_context: Dict[str, Any], workflow_input: Dict[str, Any], document_collection_name: str) -> List[Any]:
        # Normalize the input data (eliminates all if/else chains!)
        normalized_data = normalize_query_input(data, default_collection=document_collection_name)
        
        # Simple transform - no if/else needed!
        result = simple_query_transform(normalized_data)
        
        # Logging (safe for tests)
        try:
            workflow.logger.info(f"TRANSFORM DEBUG: extracted query='{result[0]}', collection='{result[1]}', top_k={result[2]}")
        except Exception:
            # Fallback for testing without Temporal context
            import logging
            logging.getLogger(__name__).info(f"TRANSFORM DEBUG: extracted query='{result[0]}', collection='{result[1]}', top_k={result[2]}")
        
        return result
