from typing import Any, List, Dict
from .base_transform import BaseTransform

# Import normalization from the same service directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from normalization import normalize_documents_input, simple_documents_transform

class DocumentsTransform(BaseTransform):
    def transform(self, data: Any, step_context: Dict[str, Any], workflow_input: Dict[str, Any], document_collection_name: str) -> List[Any]:
        # Normalize the input data (eliminates all if/else chains!)
        normalized_data = normalize_documents_input(data)
        
        # Simple transform - no if/else needed!
        return simple_documents_transform(normalized_data)
