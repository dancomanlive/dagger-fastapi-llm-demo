from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseTransform(ABC):
    @abstractmethod
    def transform(self, data: Any, step_context: Dict[str, Any], workflow_input: Dict[str, Any], document_collection_name: str) -> List[Any]:
        pass
