from .base_transform import BaseTransform
from .chunked_docs_with_collection_transform import ChunkedDocsWithCollectionTransform
from .documents_transform import DocumentsTransform
from .query_with_collection_transform import QueryWithCollectionTransform
from .passthrough_transform import PassthroughTransform

TRANSFORM_REGISTRY = {
    "chunked_docs_with_collection": ChunkedDocsWithCollectionTransform,
    "documents": DocumentsTransform,
    "query_with_collection": QueryWithCollectionTransform,
    "passthrough": PassthroughTransform,
}

def get_transform(transform_type: str) -> BaseTransform:
    transform_class = TRANSFORM_REGISTRY.get(transform_type)
    if not transform_class:
        return PassthroughTransform()
    return transform_class()
