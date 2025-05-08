"""
Advanced Superlinked + Qdrant connector tool for RAG applications.
"""
import json
import dagger
from tools.core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def superlinked_qdrant_store(
    client: dagger.Client,
    chunks: list,
    embeddings: list,
    project_id: str,
    index_name: str = "default_index",
    metadata: list = None,
    image: str = "python:3.11-slim"
) -> str:
    """
    Store text chunks and embeddings in Superlinked with Qdrant connector.
    
    Args:
        client: Dagger client
        chunks: List of text chunks
        embeddings: List of embedding vectors 
        project_id: Superlinked project ID
        index_name: Name of the index
        metadata: List of metadata dictionaries for each chunk
        image: Container image to use
        
    Returns:
        JSON string with storage results
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Add dependencies
    container = container.with_exec(["pip", "install", "requests"])
    
    # Add environment variables for Superlinked and Qdrant connection
    container = container.with_env_variable("SUPERLINKED_API_KEY", "${SUPERLINKED_API_KEY}")
    container = container.with_env_variable("SUPERLINKED_URL", "${SUPERLINKED_URL}")
    container = container.with_env_variable("QDRANT_URL", "${QDRANT_URL}")
    container = container.with_env_variable("QDRANT_API_KEY", "${QDRANT_API_KEY}")
    
    # Prepare input data
    input_data = json.dumps({
        "project_id": project_id,
        "index_name": index_name,
        "chunks": chunks,
        "embeddings": embeddings,
        "metadata": metadata or [{}] * len(chunks)
    })
    
    # Run the superlinked_qdrant.py script with the provided data
    return await run_container_and_check(
        container=container,
        args=["python", "-c", '''
import sys
import json
from scripts.superlinked_qdrant import SuperlinkedQdrantConnector

try:
    # Parse input data
    data = json.loads('''+repr(input_data)+''')
    project_id = data.get("project_id")
    index_name = data.get("index_name", "default_index")
    chunks = data.get("chunks", [])
    embeddings = data.get("embeddings", [])
    metadata = data.get("metadata", [])
    
    # Initialize connector
    connector = SuperlinkedQdrantConnector()
    
    # Index documents
    result = connector.index_documents(
        project_id=project_id,
        index_name=index_name,
        chunks=chunks,
        embeddings=embeddings,
        metadata=metadata
    )
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
''']
    )

async def superlinked_qdrant_query(
    client: dagger.Client,
    query_embedding: list,
    project_id: str,
    index_name: str,
    filters: dict = None,
    limit: int = 5,
    image: str = "python:3.11-slim"
) -> str:
    """
    Query Superlinked with Qdrant connector.
    
    Args:
        client: Dagger client
        query_embedding: Query vector embedding
        project_id: Superlinked project ID
        index_name: Name of the index
        filters: Optional metadata filters
        limit: Maximum number of results
        image: Container image to use
        
    Returns:
        JSON string with query results
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Add dependencies
    container = container.with_exec(["pip", "install", "requests"])
    
    # Add environment variables for Superlinked and Qdrant connection
    container = container.with_env_variable("SUPERLINKED_API_KEY", "${SUPERLINKED_API_KEY}")
    container = container.with_env_variable("SUPERLINKED_URL", "${SUPERLINKED_URL}")
    container = container.with_env_variable("QDRANT_URL", "${QDRANT_URL}")
    container = container.with_env_variable("QDRANT_API_KEY", "${QDRANT_API_KEY}")
    
    # Prepare input data
    input_data = json.dumps({
        "project_id": project_id,
        "index_name": index_name,
        "query_embedding": query_embedding,
        "filters": filters,
        "limit": limit
    })
    
    # Run the superlinked_qdrant.py script with the provided data
    return await run_container_and_check(
        container=container,
        args=["python", "-c", '''
import sys
import json
from scripts.superlinked_qdrant import SuperlinkedQdrantConnector

try:
    # Parse input data
    data = json.loads('''+repr(input_data)+''')
    project_id = data.get("project_id")
    index_name = data.get("index_name")
    query_embedding = data.get("query_embedding")
    filters = data.get("filters")
    limit = data.get("limit", 5)
    
    # Initialize connector
    connector = SuperlinkedQdrantConnector()
    
    # Query documents
    result = connector.query(
        project_id=project_id,
        index_name=index_name,
        query_embedding=query_embedding,
        filters=filters,
        limit=limit
    )
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
''']
    )

async def process_natural_language_query(
    client: dagger.Client,
    query: str,
    model: str = "gpt-4o-mini",
    image: str = "python:3.11-slim"
) -> str:
    """
    Process a natural language query to extract structured search parameters.
    
    Args:
        client: Dagger client
        query: User's natural language query
        model: LLM model to use for processing
        image: Container image to use
        
    Returns:
        JSON string with structured search parameters
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Add dependencies
    container = container.with_exec(["pip", "install", "requests"])
    
    # Add environment variables for Superlinked and OpenAI
    container = container.with_env_variable("SUPERLINKED_API_KEY", "${SUPERLINKED_API_KEY}")
    container = container.with_env_variable("OPENAI_API_KEY", "${OPENAI_API_KEY}")
    
    # Prepare input data
    input_data = json.dumps({
        "query": query,
        "model": model
    })
    
    # Run the superlinked_qdrant.py script with the provided data
    return await run_container_and_check(
        container=container,
        args=["python", "-c", '''
import sys
import json
from scripts.superlinked_qdrant import SuperlinkedQdrantConnector

try:
    # Parse input data
    data = json.loads('''+repr(input_data)+''')
    query = data.get("query")
    model = data.get("model", "gpt-4o-mini")
    
    # Initialize connector
    connector = SuperlinkedQdrantConnector()
    
    # Process natural language query
    result = connector.process_natural_language_query(
        query=query,
        model=model
    )
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
''']
    )

async def weighted_multi_search(
    client: dagger.Client,
    query_embedding: list,
    project_id: str,
    index_name: str,
    text_query: str = None,
    weights: dict = None,
    filters: dict = None,
    limit: int = 5,
    image: str = "python:3.11-slim"
) -> str:
    """
    Perform weighted multi-factor search combining vector similarity with other factors.
    
    Args:
        client: Dagger client
        query_embedding: Vector embedding of the query
        project_id: Superlinked project ID
        index_name: Name of the index
        text_query: Optional text query for hybrid search
        weights: Dictionary of weights for different factors
        filters: Optional metadata filters
        limit: Maximum number of results
        image: Container image to use
        
    Returns:
        JSON string with weighted search results
    """
    # Get a base container configured with our scripts directory
    container = get_tool_base(
        client=client,
        image=image,
        scripts_dir=SCRIPTS_DIR,
    )
    
    # Add dependencies
    container = container.with_exec(["pip", "install", "requests"])
    
    # Add environment variables for Superlinked and Qdrant connection
    container = container.with_env_variable("SUPERLINKED_API_KEY", "${SUPERLINKED_API_KEY}")
    container = container.with_env_variable("SUPERLINKED_URL", "${SUPERLINKED_URL}")
    container = container.with_env_variable("QDRANT_URL", "${QDRANT_URL}")
    container = container.with_env_variable("QDRANT_API_KEY", "${QDRANT_API_KEY}")
    
    # Prepare input data
    input_data = json.dumps({
        "project_id": project_id,
        "index_name": index_name,
        "query_embedding": query_embedding,
        "text_query": text_query,
        "weights": weights,
        "filters": filters,
        "limit": limit
    })
    
    # Run the superlinked_qdrant.py script with the provided data
    return await run_container_and_check(
        container=container,
        args=["python", "-c", '''
import sys
import json
from scripts.superlinked_qdrant import SuperlinkedQdrantConnector

try:
    # Parse input data
    data = json.loads('''+repr(input_data)+''')
    project_id = data.get("project_id")
    index_name = data.get("index_name")
    query_embedding = data.get("query_embedding")
    text_query = data.get("text_query")
    weights = data.get("weights")
    filters = data.get("filters")
    limit = data.get("limit", 5)
    
    # Initialize connector
    connector = SuperlinkedQdrantConnector()
    
    # Perform weighted multi-search
    result = connector.weighted_multi_search(
        project_id=project_id,
        index_name=index_name,
        query_embedding=query_embedding,
        text_query=text_query,
        weights=weights,
        filters=filters,
        limit=limit
    )
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
''']
    )
