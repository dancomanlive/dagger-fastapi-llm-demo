from pydantic import BaseSettings

class Config(BaseSettings):
    """
    Centralized configuration for the RAG system.
    """
    chunk_size: int = 1000
    overlap: int = 200
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    qdrant_url: str
    qdrant_api_key: str
    superlinked_url: str
    superlinked_api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instantiate the configuration
config = Config()
