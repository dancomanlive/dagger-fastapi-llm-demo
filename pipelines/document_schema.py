from pydantic import BaseModel, Field
from typing import List, Dict, Any

class DocumentSchema(BaseModel):
    """
    Generic schema for documents in the RAG system.
    """
    document_id: str = Field(..., description="Unique identifier for the document")
    text: str = Field(..., description="Text content of the document")
    embeddings: List[float] = Field(..., description="Vector embeddings for the document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the document")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "doc123",
                "text": "This is a sample document.",
                "embeddings": [0.1, 0.2, 0.3],
                "metadata": {"author": "John Doe", "category": "example"}
            }
        }
