#!/usr/bin/env python3
"""
Input Normalization Functions

This module provides functions to normalize various input formats into
standard dictionaries, eliminating the need for if/else chains in transforms.

The goal: Any input type -> Standard dict format -> Simple transform logic
"""

from typing import Any, Dict, List, Union


def normalize_query_input(data: Any, default_collection: str = "default", default_top_k: int = 10) -> Dict[str, Any]:
    """
    Normalize any query input to standard format.
    
    Args:
        data: Input data (str, list, dict, or any other type)
        default_collection: Default collection name
        default_top_k: Default top_k value
        
    Returns:
        Dict with keys: query, collection, top_k
        
    Examples:
        normalize_query_input("test") -> {"query": "test", "collection": "default", "top_k": 10}
        normalize_query_input(["test"]) -> {"query": "test", "collection": "default", "top_k": 10}
        normalize_query_input({"query": "test", "top_k": 5}) -> {"query": "test", "collection": "default", "top_k": 5}
    """
    # Handle None input
    if data is None:
        return {"query": "", "collection": default_collection, "top_k": default_top_k}
    
    # Handle string input
    if isinstance(data, str):
        return {"query": data, "collection": default_collection, "top_k": default_top_k}
    
    # Handle list input
    if isinstance(data, list):
        query = str(data[0]) if data else ""
        return {"query": query, "collection": default_collection, "top_k": default_top_k}
    
    # Handle dict input
    if isinstance(data, dict):
        return {
            "query": data.get("query", ""),
            "collection": data.get("collection", default_collection),
            "top_k": data.get("top_k", default_top_k)
        }
    
    # Handle any other type by converting to string
    return {"query": str(data), "collection": default_collection, "top_k": default_top_k}


def normalize_documents_input(data: Any) -> List[Dict[str, Any]]:
    """
    Normalize any documents input to standard list format.
    
    Args:
        data: Input data (dict with documents/retrieved_documents, list, or single doc)
        
    Returns:
        List of document dictionaries
        
    Examples:
        normalize_documents_input({"retrieved_documents": [doc1, doc2]}) -> [doc1, doc2]
        normalize_documents_input([doc1, doc2]) -> [doc1, doc2]
        normalize_documents_input(doc1) -> [doc1]
    """
    # Handle None input
    if data is None:
        return []
    
    # Handle dict with retrieved_documents (from retriever service)
    if isinstance(data, dict) and "retrieved_documents" in data:
        return data["retrieved_documents"]
    
    # Handle dict with documents key
    if isinstance(data, dict) and "documents" in data:
        return data["documents"]
    
    # Handle direct list
    if isinstance(data, list):
        return data
    
    # Handle single document (wrap in list)
    return [data]


def normalize_args_input(*args, default_top_k: int = 5) -> Dict[str, Any]:
    """
    Normalize function arguments to standard format.
    
    This handles the dual format problem in retriever service:
    - args = (["query", "collection", top_k],)  # List format
    - args = ("query", "collection", top_k)     # Direct format
    
    Args:
        *args: Variable arguments
        default_top_k: Default top_k value for retriever service
        
    Returns:
        Dict with keys: query, collection, top_k
        
    Raises:
        ValueError: If insufficient arguments provided
    """
    if len(args) == 1 and isinstance(args[0], list) and len(args[0]) >= 2:
        # List format: args = (["query", "collection", top_k],)
        arg_list = args[0]
        query = arg_list[0]
        collection = arg_list[1]
        top_k = arg_list[2] if len(arg_list) > 2 else default_top_k
        
    elif len(args) >= 2:
        # Direct format: args = ("query", "collection", top_k)
        query = args[0]
        collection = args[1]
        top_k = args[2] if len(args) > 2 else default_top_k
        
    else:
        raise ValueError(f"Expected at least 2 arguments (query, collection), got {len(args)}: {args}")
    
    return {
        "query": str(query),
        "collection": str(collection),
        "top_k": int(top_k)
    }


# Simple transform functions (no if/else needed after normalization!)

def simple_query_transform(normalized_data: Dict[str, Any]) -> List[str]:
    """
    Simple query transform - no if/else needed!
    
    Args:
        normalized_data: Output from normalize_query_input()
        
    Returns:
        List in format [query, collection, top_k]
    """
    return [
        normalized_data["query"],
        normalized_data["collection"], 
        normalized_data["top_k"]
    ]


def simple_documents_transform(normalized_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Simple documents transform - no if/else needed!
    
    Args:
        normalized_data: Output from normalize_documents_input()
        
    Returns:
        The same list (already normalized)
    """
    return normalized_data


def simple_args_transform(normalized_data: Dict[str, Any]) -> tuple:
    """
    Simple args transform - no if/else needed!
    
    Args:
        normalized_data: Output from normalize_args_input()
        
    Returns:
        Tuple of (query, collection, top_k)
    """
    return (
        normalized_data["query"],
        normalized_data["collection"],
        normalized_data["top_k"]
    )
