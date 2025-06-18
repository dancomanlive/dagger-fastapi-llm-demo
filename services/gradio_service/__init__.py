"""
Gradio Service Module - RAG Chat Interface

This module provides a clean, modular RAG chat interface that can be easily
integrated into larger applications.

Usage as part of a larger app:
    from services.gradio_service import RAGChatInterface
    
    # Create the interface
    chat_interface = RAGChatInterface()
    
    # Get the Gradio app component
    gradio_app = chat_interface.create_app()
    
    # Mount it in your larger app or run standalone
    chat_interface.launch()

Architecture:
    - config.py: Configuration management
    - rag_service.py: Business logic (Temporal, OpenAI integration)
    - gradio_ui.py: UI components and event handling
    - __init__.py: Public API and easy imports
"""

from .config import config
from .rag_service import RAGService, SystemStatusService, RetrievalResult, ResponseMetrics
from .gradio_ui import GradioInterface

# Main interface class for external use
class RAGChatInterface:
    """
    Main interface for the RAG Chat system.
    
    This class provides a simple API for integrating the RAG chat interface
    into larger applications.
    """
    
    def __init__(self, **config_overrides):
        """
        Initialize the RAG chat interface.
        
        Args:
            **config_overrides: Optional configuration overrides
        """
        # Apply any configuration overrides
        if config_overrides:
            for key, value in config_overrides.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        self.ui = GradioInterface()
        self.rag_service = self.ui.rag_service
        self.status_service = self.ui.status_service
    
    def create_app(self):
        """Create and return the Gradio app"""
        return self.ui.create_app()
    
    def launch(self, **kwargs):
        """Launch the interface"""
        return self.ui.launch(**kwargs)
    
    def get_status(self):
        """Get system status"""
        return self.status_service.get_system_status()
    
    def get_config(self):
        """Get current configuration"""
        return config.to_dict()

# Convenience exports
__all__ = [
    'RAGChatInterface',
    'RAGService', 
    'SystemStatusService',
    'GradioInterface',
    'RetrievalResult',
    'ResponseMetrics',
    'config'
]
