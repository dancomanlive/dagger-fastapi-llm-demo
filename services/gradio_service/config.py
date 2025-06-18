"""
Configuration module for the RAG Chat Assistant.

Centralizes all configuration settings and environment variables.
"""

import os
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TemporalConfig:
    """Temporal service configuration"""
    host: str
    namespace: str
    task_queue: str
    workflow_name: str


@dataclass
class OpenAIConfig:
    """OpenAI service configuration"""
    api_key: str
    default_model: str
    default_temperature: float
    default_max_tokens: int


@dataclass
class UIConfig:
    """UI configuration"""
    title: str
    description: str
    server_name: str
    server_port: int
    available_collections: List[str]
    default_collection: str
    show_debug: bool


class Config:
    """Main configuration class"""
    
    def __init__(self):
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables"""
        
        # Temporal configuration
        self.temporal = TemporalConfig(
            host=os.environ.get("TEMPORAL_HOST", "localhost:7233"),
            namespace=os.environ.get("TEMPORAL_NAMESPACE", "default"),
            task_queue="document-processing-queue",
            workflow_name="GenericPipelineWorkflow"
        )
        
        # OpenAI configuration
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.openai = OpenAIConfig(
            api_key=api_key,
            default_model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
            default_temperature=float(os.environ.get("OPENAI_TEMPERATURE", "0.7")),
            default_max_tokens=int(os.environ.get("OPENAI_MAX_TOKENS", "1000"))
        )
        
        # UI configuration
        document_collection = os.environ.get("DOCUMENT_COLLECTION_NAME", "document_chunks")
        
        self.ui = UIConfig(
            title="RAG Chat Assistant",
            description="Ask questions and get answers based on your document collection with real-time streaming.",
            server_name=os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0"),
            server_port=int(os.environ.get("GRADIO_SERVER_PORT", "7860")),
            available_collections=[
                "default",
                "test-document-chunks", 
                document_collection
            ],
            default_collection=os.environ.get("DEFAULT_COLLECTION", "default"),
            show_debug=os.environ.get("SHOW_DEBUG", "true").lower() == "true"
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Check required environment variables
        if not self.openai.api_key:
            errors.append("OPENAI_API_KEY is required")
        
        # Validate port range
        if not (1 <= self.ui.server_port <= 65535):
            errors.append(f"Invalid server port: {self.ui.server_port}")
        
        # Validate temperature range
        if not (0.0 <= self.openai.default_temperature <= 2.0):
            errors.append(f"Invalid temperature: {self.openai.default_temperature}")
        
        # Validate max tokens
        if not (1 <= self.openai.default_max_tokens <= 4000):
            errors.append(f"Invalid max tokens: {self.openai.default_max_tokens}")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for display"""
        return {
            "temporal": {
                "host": self.temporal.host,
                "namespace": self.temporal.namespace,
                "task_queue": self.temporal.task_queue,
                "workflow_name": self.temporal.workflow_name
            },
            "openai": {
                "model": self.openai.default_model,
                "temperature": self.openai.default_temperature,
                "max_tokens": self.openai.default_max_tokens,
                "api_key_set": bool(self.openai.api_key)
            },
            "ui": {
                "server": f"{self.ui.server_name}:{self.ui.server_port}",
                "collections": self.ui.available_collections,
                "default_collection": self.ui.default_collection,
                "debug_mode": self.ui.show_debug
            }
        }


# Global configuration instance
config = Config()

# Alias for backward compatibility and test purposes
class RAGConfig:
    """RAG Configuration class for test compatibility"""
    
    def __init__(self):
        # Use the existing config structure
        self._config = Config()
    
    @property
    def temporal_host(self):
        return self._config.temporal.host
    
    @property
    def temporal_namespace(self):
        return self._config.temporal.namespace
    
    @property
    def workflow_task_queue(self):
        return self._config.temporal.task_queue
    
    @property
    def workflow_name(self):
        return self._config.temporal.workflow_name
