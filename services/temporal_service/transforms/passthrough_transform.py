from typing import Any, List, Dict
from .base_transform import BaseTransform

class PassthroughTransform(BaseTransform):
    def transform(self, data: Any, step_context: Dict[str, Any], workflow_input: Dict[str, Any], document_collection_name: str) -> List[Any]:
        return [data] if not isinstance(data, list) else data
