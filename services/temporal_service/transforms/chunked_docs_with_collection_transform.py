from typing import Any, List, Dict
from .base_transform import BaseTransform

class ChunkedDocsWithCollectionTransform(BaseTransform):
    def transform(self, data: Any, step_context: Dict[str, Any], workflow_input: Dict[str, Any], document_collection_name: str) -> List[Any]:
        collection_name = document_collection_name
        if isinstance(workflow_input, dict):
            collection_name = workflow_input.get("collection", document_collection_name)
        
        # Unwrap nested lists if needed
        documents = data
        while isinstance(documents, list) and len(documents) == 1 and isinstance(documents[0], list):
            documents = documents[0]
        
        return [documents, collection_name]
