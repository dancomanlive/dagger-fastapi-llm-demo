import pytest
from pipelines.document_schema import DocumentSchema

def test_document_schema_validation():
    # Valid document
    valid_data = {
        "document_id": "doc1",
        "text": "This is a valid document.",
        "embeddings": [0.1, 0.2, 0.3],
        "metadata": {"author": "John Doe"}
    }
    document = DocumentSchema(**valid_data)
    assert document.document_id == "doc1"
    assert document.text == "This is a valid document."
    assert document.embeddings == [0.1, 0.2, 0.3]
    assert document.metadata["author"] == "John Doe"

    # Invalid document (missing required field)
    invalid_data = {
        "text": "This is an invalid document.",
        "embeddings": [0.1, 0.2, 0.3],
        "metadata": {"author": "John Doe"}
    }
    with pytest.raises(Exception):
        DocumentSchema(**invalid_data)
