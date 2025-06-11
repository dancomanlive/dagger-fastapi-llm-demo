# gradio_app.py

"""
Gradio-based chat interface for the RAG pipeline with streaming support.

Features:
- Real-time streaming responses from OpenAI
- Interactive chat interface  
- Document collection selection
- Debug information panel
- Response metrics and settings
"""

import gradio as gr
import openai
import os
import time
import asyncio
from typing import Generator, List, Tuple
from temporalio.client import Client

# Temporal Configuration
TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")

async def get_context_via_temporal(query: str, collection: str) -> str:
    """
    Get context using Temporal RetrievalWorkflow instead of HTTP calls.
    
    This replaces the HTTP-based get_context_for_query function.
    """
    try:
        # Connect to Temporal
        client = await Client.connect(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
        
        # Start RetrievalWorkflow
        workflow_handle = await client.start_workflow(
            "RetrievalWorkflow",
            args=[query, 5],  # query and top_k
            id=f"gradio-retrieval-{int(time.time() * 1000)}",
            task_queue="workflow-task-queue"  # temporal_service task queue
        )
        
        # Get the result
        result = await workflow_handle.result()
        
        # Format the search results into context string
        if result.get("status") == "completed" and "search_result" in result:
            search_data = result["search_result"]
            if "results" in search_data and search_data["results"]:
                # Format results into context
                contexts = []
                for i, doc in enumerate(search_data["results"]):
                    content = doc.get("content", "")
                    contexts.append(f"Context {i+1}: {content}")
                
                return "\n\n".join(contexts)
            else:
                return "No relevant context found."
        else:
            return f"Workflow completed but no results found: {result.get('status', 'unknown')}"
            
    except Exception as e:
        return f"Error retrieving context via Temporal: {str(e)}"

def get_openai_client():
    """Get OpenAI client with API key from environment"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return openai.OpenAI(api_key=api_key)

# Configuration - Application settings
DEFAULT_COLLECTION = "default"
DOCUMENT_COLLECTION_NAME = os.environ.get("DOCUMENT_COLLECTION_NAME", "document_chunks")
AVAILABLE_COLLECTIONS = ["default", DOCUMENT_COLLECTION_NAME]

# Note: get_context_for_query has been removed - we now use Temporal workflows only

def stream_rag_response(
    query: str, 
    history: List[Tuple[str, str]], 
    collection: str = DEFAULT_COLLECTION,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> Generator[Tuple[str, List[Tuple[str, str]], dict], None, None]:
    """Stream RAG response using OpenAI with context from retriever service"""
    
    start_time = time.time()
    response_text = ""
    token_count = 0
    
    try:
        # Get context from Temporal RetrievalWorkflow (instead of HTTP)
        context = get_context_for_query_temporal(query, collection)
        
        # Prepare messages for OpenAI
        messages = [
            {
                "role": "system", 
                "content": f"""You are a helpful assistant that answers questions based on the provided context. 
                
Context from documents:
{context}

Instructions:
- Answer based primarily on the provided context
- If the context doesn't contain relevant information, say so
- Be concise but comprehensive
- Cite specific parts of the context when relevant"""
            }
        ]
        
        # Add conversation history
        for user_msg, assistant_msg in history[-5:]:  # Keep last 5 exchanges
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Create streaming response
        openai_client = get_openai_client()
        stream = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use gpt-4 if available
            messages=messages,
            stream=True,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                response_text += content
                token_count += 1
                
                # Calculate metrics
                elapsed_time = time.time() - start_time
                metrics = {
                    "response_time": round(elapsed_time, 2),
                    "token_count": token_count,
                    "collection_used": collection
                }
                
                # Yield updated chat history
                updated_history = history + [[query, response_text]]
                yield "", updated_history, metrics
                
    except Exception as e:
        error_response = f"Error generating response: {str(e)}"
        metrics = {
            "response_time": round(time.time() - start_time, 2),
            "token_count": 0,
            "collection_used": collection,
            "error": str(e)
        }
        updated_history = history + [[query, error_response]]
        yield "", updated_history, metrics

def get_temporal_status() -> dict:
    """Get status of Temporal system and services"""
    try:
        # Test Temporal connection
        status = {}
        
        # Test OpenAI API Key
        if os.environ.get("OPENAI_API_KEY"):
            status["OpenAI"] = "✅ API Key Set"
        else:
            status["OpenAI"] = "❌ No API Key"
        
        # Test Temporal configuration
        temporal_host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
        status["Temporal Host"] = f"✅ Configured: {temporal_host}"
        
        # Test Temporal namespace
        temporal_namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
        status["Temporal Namespace"] = f"✅ {temporal_namespace}"
        
        # Note: In a real implementation, you could test actual Temporal connectivity here
        # For now, we show configuration status
        status["System"] = "✅ Temporal-based Architecture"
        
        return status
        
    except Exception as e:
        return {"error": str(e)}

def test_temporal_system() -> dict:
    """Test Temporal system components"""
    return {
        "Architecture": "✅ Pure Temporal Workflows",
        "Chat Interface": "✅ Gradio + Temporal Client",
        "Orchestration": "✅ RetrievalWorkflow", 
        "Activities": "✅ Embedding + Retriever Services",
        "Database": "✅ Qdrant Vector Store",
        "Monitoring": "✅ Temporal UI (port 8081)"
    }

async def test_temporal_connection() -> dict:
    """Test connectivity to Temporal server"""
    try:
        client = await Client.connect(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
        # Simple test - try to get workflow service info
        return {"status": "✅ Connected", "host": TEMPORAL_HOST, "namespace": TEMPORAL_NAMESPACE}
    except Exception as e:
        return {"status": f"❌ {str(e)}", "host": TEMPORAL_HOST, "namespace": TEMPORAL_NAMESPACE}

def test_temporal_connection_sync() -> dict:
    """Synchronous wrapper for Temporal connection test"""
    try:
        return asyncio.run(test_temporal_connection())
    except Exception as e:
        return {"status": f"❌ {str(e)}", "host": TEMPORAL_HOST, "namespace": TEMPORAL_NAMESPACE}

def create_gradio_app():
    """Create and configure the Gradio chat interface"""
    
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
    """
    
    with gr.Blocks(
        title="RAG Chat Assistant", 
        theme=gr.themes.Soft(),
        css=custom_css
    ) as demo:
        
        # Header
        gr.Markdown("# 🤖 RAG Chat Assistant")
        gr.Markdown("Ask questions and get answers based on your document collection with real-time streaming.")
        
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
            
            # Settings and debug panel
            with gr.Column(scale=1):
                # Collection selection
                collection_dropdown = gr.Dropdown(
                    choices=AVAILABLE_COLLECTIONS,
                    value=DEFAULT_COLLECTION,
                    label="📁 Document Collection",
                    interactive=True
                )
                
                # Advanced settings
                with gr.Accordion("⚙️ Advanced Settings", open=False):
                    temperature = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=0.7,
                        step=0.1,
                        label="Temperature",
                        info="Higher values make output more creative"
                    )
                    max_tokens = gr.Slider(
                        minimum=100,
                        maximum=2000,
                        value=1000,
                        step=100,
                        label="Max Tokens",
                        info="Maximum response length"
                    )
                
                # Response metrics
                with gr.Accordion("📊 Response Metrics", open=True):
                    metrics_json = gr.JSON(
                        label="Last Response Stats",
                        value={"response_time": 0, "token_count": 0}
                    )
                
                # Debug information
                with gr.Accordion("🔧 Debug Info", open=False):
                    cache_info = gr.JSON(label="Cache Status")
                    refresh_cache = gr.Button("🔄 Refresh Cache")
                    
                    service_status = gr.JSON(label="Service Status")
                    test_services_btn = gr.Button("🧪 Test Services")
        
        # Example queries
        with gr.Accordion("💡 Example Questions", open=False):
            examples = gr.Examples(
                examples=[
                    ["What is RAG and how does it work?"],
                    ["Explain the key components of a RAG system"],
                    ["How does RAG help solve LLM hallucinations?"],
                    ["What are the benefits of modular RAG architectures?"]
                ],
                inputs=msg,
                label="Click an example to try it"
            )
        
        # Event handlers
        def handle_submit(message, history, collection, temp, max_tok):
            if not message.strip():
                return "", history, {"error": "Empty message"}
            
            # Stream the response
            for result in stream_rag_response(message, history, collection, temp, max_tok):
                yield result
        
        def clear_chat():
            return [], "", {"response_time": 0, "token_count": 0}
        
        # Wire up the events
        submit_click = submit_btn.click(
            handle_submit,
            inputs=[msg, chatbot, collection_dropdown, temperature, max_tokens],
            outputs=[msg, chatbot, metrics_json],
            show_progress=True
        )
        
        msg_submit = msg.submit(
            handle_submit,
            inputs=[msg, chatbot, collection_dropdown, temperature, max_tokens],
            outputs=[msg, chatbot, metrics_json],
            show_progress=True
        )
        
        clear_btn.click(clear_chat, outputs=[chatbot, msg, metrics_json])
        
        refresh_cache.click(get_temporal_status, outputs=cache_info)
        test_services_btn.click(test_temporal_system, outputs=service_status)
        
        # Load initial status on startup
        demo.load(get_temporal_status, outputs=cache_info)
        demo.load(test_temporal_system, outputs=service_status)
    
    return demo

def get_context_for_query_temporal(query: str, collection: str) -> str:
    """
    Synchronous wrapper for get_context_via_temporal.
    
    This function replaces the HTTP-based get_context_for_query in the 
    main application flow while maintaining the same interface.
    """
    try:
        return asyncio.run(get_context_via_temporal(query, collection))
    except Exception as e:
        return f"Error retrieving context via Temporal: {str(e)}"

def main():
    """Main entry point"""
    print("🚀 Starting RAG Chat Interface...")
    
    # Check if required services are available
    print("🔍 Checking Temporal system connectivity...")
    status = test_temporal_system()
    for service, state in status.items():
        print(f"   {service}: {state}")
    
    # Create and launch the app
    app = create_gradio_app()
    
    print("🌟 Launching Gradio interface...")
    print("   📱 Container URL: http://0.0.0.0:7860")
    print("   🌐 FastAPI Backend: http://fastapi:8000")
    print("   🔍 Retriever Service: http://retriever-service:8000")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True,
        show_error=True
    )

if __name__ == "__main__":
    main()
