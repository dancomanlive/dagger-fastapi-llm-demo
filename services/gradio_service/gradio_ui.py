"""
Gradio UI - User interface layer for the RAG chat application.

This module contains only UI components and delegates all business logic to the RAG service.
"""

import gradio as gr
from typing import List, Tuple, Dict
try:
    from .rag_service import RAGService, SystemStatusService, ResponseMetrics
    from .config import config
except ImportError:
    # Fallback for when running tests from workspace root
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from rag_service import RAGService, SystemStatusService, ResponseMetrics
    from config import config


class GradioInterface:
    """Gradio interface for RAG chat application"""
    
    def __init__(self, rag_service: RAGService = None, config_obj = None):
        # Allow dependency injection for testing
        if config_obj is None:
            config_obj = config
        
        self.config = config_obj  # Store config for tests
        
        if rag_service is None:
            self.rag_service = RAGService(config_obj)
        else:
            self.rag_service = rag_service
            
        self.status_service = SystemStatusService(config_obj)
        
        # Configuration from config module
        self.default_collection = config_obj.ui.default_collection
        self.available_collections = config_obj.ui.available_collections
    
    def create_app(self) -> gr.Blocks:
        """Create and configure the Gradio interface"""
        
        # Custom CSS for better styling
        custom_css = """
        .gradio-container {
            max-width: 1200px !important;
        }
        .chat-message {
            padding: 10px;
            margin: 5px 0;
            border-radius: 10px;
        }
        .metrics-panel {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 10px;
        }
        """
        
        with gr.Blocks(
            title="RAG Chat Assistant",
            theme=gr.themes.Soft(),
            css=custom_css
        ) as demo:
            
            # Header
            gr.Markdown(f"# 🤖 {config.ui.title}")
            gr.Markdown(config.ui.description)
            
            with gr.Row():
                # Main chat interface
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(
                        height=500,
                        bubble_full_width=False,
                        show_copy_button=True,
                        placeholder="Start a conversation...",
                        show_label=False
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            placeholder="Type your question here...",
                            scale=4,
                            show_label=False,
                            container=False
                        )
                        submit_btn = gr.Button("Send", variant="primary", scale=1)
                        clear_btn = gr.Button("Clear", scale=1)
                
                # Settings and metrics panel
                with gr.Column(scale=1):
                    self._create_settings_panel()
                    self._create_metrics_panel()
                    self._create_debug_panel()
            
            # Example queries
            self._create_examples_section(msg)
            
            # Wire up events
            self._setup_event_handlers(demo, msg, chatbot, submit_btn, clear_btn)
        
        return demo
    
    def _create_settings_panel(self):
        """Create the settings panel"""
        # Collection selection
        self.collection_dropdown = gr.Dropdown(
            choices=self.available_collections,
            value=self.default_collection,
            label="📁 Document Collection",
            interactive=True
        )
        
        # Advanced settings
        with gr.Accordion("⚙️ Advanced Settings", open=False):
            self.temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=config.openai.default_temperature,
                step=0.1,
                label="Temperature",
                info="Higher values make output more creative"
            )
            self.max_tokens = gr.Slider(
                minimum=100,
                maximum=2000,
                value=config.openai.default_max_tokens,
                step=100,
                label="Max Tokens",
                info="Maximum response length"
            )
    
    def _create_metrics_panel(self):
        """Create the metrics display panel"""
        with gr.Accordion("📊 Response Metrics", open=True):
            self.metrics_json = gr.JSON(
                label="Last Response Stats",
                value={
                    "response_time": 0,
                    "token_count": 0,
                    "collection_name": "None",
                    "processing_time": 0,
                    "total_chunks": 0,
                    "retrieval_status": "pending"
                }
            )
        
        # Retrieved Documents
        with gr.Accordion("📄 Retrieved Documents", open=False):
            self.retrieved_docs = gr.JSON(
                label="Document Chunks",
                value=[]
            )
    
    def _create_debug_panel(self):
        """Create the debug information panel"""
        with gr.Accordion("🔧 Debug Info", open=False):
            self.cache_info = gr.JSON(label="System Status")
            refresh_cache = gr.Button("🔄 Refresh Status")
            
            self.service_status = gr.JSON(label="Architecture Info")
            test_services_btn = gr.Button("🧪 Test Services")
            
            # Wire up debug events
            refresh_cache.click(self._get_system_status, outputs=self.cache_info)
            test_services_btn.click(self._get_architecture_info, outputs=self.service_status)
    
    def _create_examples_section(self, msg_input):
        """Create the examples section"""
        with gr.Accordion("💡 Example Questions", open=False):
            gr.Examples(
                examples=[
                    ["What is RAG and how does it work?"],
                    ["Explain the key components of a RAG system"],
                    ["How does RAG help solve LLM hallucinations?"],
                    ["What are the benefits of modular RAG architectures?"]
                ],
                inputs=msg_input,
                label="Click an example to try it"
            )
    
    def _setup_event_handlers(self, demo, msg, chatbot, submit_btn, clear_btn):
        """Setup all event handlers"""
        
        # Submit button click
        submit_btn.click(
            self._handle_submit,
            inputs=[msg, chatbot, self.collection_dropdown, self.temperature, self.max_tokens],
            outputs=[msg, chatbot, self.metrics_json, self.retrieved_docs],
            show_progress=True
        )
        
        # Message submit (Enter key)
        msg.submit(
            self._handle_submit,
            inputs=[msg, chatbot, self.collection_dropdown, self.temperature, self.max_tokens],
            outputs=[msg, chatbot, self.metrics_json, self.retrieved_docs],
            show_progress=True
        )
        
        # Clear button
        clear_btn.click(self._clear_chat, outputs=[chatbot, msg, self.metrics_json, self.retrieved_docs])
        
        # Load initial status on startup
        demo.load(self._get_system_status, outputs=self.cache_info)
        demo.load(self._get_architecture_info, outputs=self.service_status)
    
    def _handle_submit(self, message: str, history: List[Tuple[str, str]], collection: str, temp: float, max_tok: int):
        """Handle message submission"""
        print(f"🚀 UI: Handling submit - message='{message}', collection='{collection}'")
        
        if not message.strip():
            print("❌ UI: Empty message received")
            return "", history, {"error": "Empty message"}, []
        
        print("🚀 UI: Calling RAG service...")
        
        # Stream the response from RAG service
        for result in self.rag_service.stream_rag_response(message, history, collection, temp, max_tok):
            msg_out, hist_out, metrics = result
            
            # Convert metrics to display format
            metrics_display = self._format_metrics_for_display(metrics)
            retrieved_chunks = metrics.retrieval_result.chunks
            
            yield msg_out, hist_out, metrics_display, retrieved_chunks
    
    def _format_metrics_for_display(self, metrics: ResponseMetrics) -> Dict:
        """Convert ResponseMetrics to display format"""
        return {
            "response_time": metrics.response_time,
            "token_count": metrics.token_count,
            "collection_used": metrics.collection_used,
            "collection_name": metrics.retrieval_result.collection_name,
            "processing_time": metrics.retrieval_result.processing_time,
            "query": metrics.retrieval_result.query,
            "total_chunks": metrics.retrieval_result.total_results,
            "retrieval_status": metrics.retrieval_result.status,
            "error": metrics.error
        }
    
    def _clear_chat(self):
        """Clear the chat interface"""
        return [], "", {
            "response_time": 0,
            "token_count": 0,
            "collection_name": "None",
            "processing_time": 0,
            "total_chunks": 0,
            "retrieval_status": "cleared"
        }, []
    
    def _get_system_status(self):
        """Get system status"""
        return self.status_service.get_system_status()
    
    def _get_architecture_info(self):
        """Get architecture information"""
        return self.status_service.get_architecture_info()
    
    def launch(self, **kwargs):
        """Launch the Gradio interface"""
        app = self.create_app()
        
        print("🚀 Starting RAG Chat Interface...")
        print("🔍 Checking system connectivity...")
        
        status = self.status_service.get_system_status()
        for service, state in status.items():
            print(f"   {service}: {state}")
        
        print("🌟 Launching Gradio interface...")
        print("   📱 Container URL: http://0.0.0.0:7860")
        
        # Default launch configuration
        launch_config = {
            "server_name": config.ui.server_name,
            "server_port": config.ui.server_port,
            "share": False,
            "debug": config.ui.show_debug,
            "show_error": True
        }
        launch_config.update(kwargs)
        
        app.launch(**launch_config)

def create_gradio_interface(rag_service: RAGService = None, config_obj = None):
    """
    Factory function to create a GradioInterface instance.
    
    Args:
        rag_service: Optional RAGService instance for dependency injection
        config_obj: Optional config object for dependency injection
        
    Returns:
        GradioInterface: Configured Gradio interface instance
    """
    return GradioInterface(rag_service, config_obj)
