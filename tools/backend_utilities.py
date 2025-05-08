import json
from typing import List, Dict, Any

def flatten_query_responses(responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flatten query responses to extract relevant fields.

    Args:
        responses: List of query response dictionaries.

    Returns:
        List of flattened dictionaries.
    """
    flattened = []
    for response in responses:
        flattened.append({
            "text": response.get("text"),
            "score": response.get("score"),
            "metadata": response.get("metadata", {})
        })
    return flattened

def clean_knn_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean KNN parameters by removing unnecessary fields.

    Args:
        parameters: Dictionary of KNN parameters.

    Returns:
        Cleaned dictionary of KNN parameters.
    """
    return {k: v for k, v in parameters.items() if k not in ["debug", "internal"]}

def load_dataset(file_path: str) -> List[Dict[str, Any]]:
    """
    Load a dataset from a JSONL file.

    Args:
        file_path: Path to the JSONL file.

    Returns:
        List of dictionaries representing the dataset.
    """
    with open(file_path, "r") as f:
        return [json.loads(line) for line in f]
