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
import requests
import json
from typing import Generator, List, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_openai_client():
    """Get OpenAI client with API key from environment"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return openai.OpenAI(api_key=api_key)

# Configuration - Docker service URLs
FASTAPI_BASE_URL = os.getenv("FASTAPI_SERVICE_URL", "http://fastapi:8000")
RETRIEVER_SERVICE_URL = os.getenv("RETRIEVER_SERVICE_URL", "http://retriever-service:8000")
DEFAULT_COLLECTION = "default"
AVAILABLE_COLLECTIONS = ["default", "documents", "research", "manuals"]

def get_context_for_query(query: str, collection: str) -> str:
    """Get context using the existing FastAPI retriever service"""
    try:
        # Call the existing retriever service using Docker service name
        retriever_url = RETRIEVER_SERVICE_URL
        
        response = requests.post(
            f"{retriever_url}/retrieve",
            json={
                "query": query,
                "collection": collection,
                "top_k": 5
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            contexts = data.get("retrieved_contexts", [])
            
            if contexts:
                # Combine the retrieved contexts
                combined_context = "\n\n".join([
                    f"Context {i+1}: {ctx.get('text', '')}" 
                    for i, ctx in enumerate(contexts)
                ])
                return combined_context
            else:
                return "No relevant context found."
        else:
            return f"Error retrieving context: {response.status_code}"
            
    except Exception as e:
        return f"Error retrieving context: {str(e)}"

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
        # Get context from retriever service
        context = get_context_for_query(query, collection)
        
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

def get_cache_status() -> dict:
    """Get cache status from FastAPI debug endpoint"""
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/debug/cache", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def test_services() -> dict:
    """Test connectivity to all services"""
    services = {}
    
    # Test FastAPI
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/health", timeout=5)
        services["FastAPI"] = "✅ Connected" if response.status_code == 200 else f"❌ HTTP {response.status_code}"
    except Exception as e:
        services["FastAPI"] = f"❌ {str(e)}"
    
    # Test Retriever Service
    try:
        response = requests.get(f"{RETRIEVER_SERVICE_URL}/", timeout=5)
        services["Retriever"] = "✅ Connected" if response.status_code == 200 else f"❌ HTTP {response.status_code}"
    except Exception as e:
        services["Retriever"] = f"❌ {str(e)}"
    
    # Test OpenAI
    try:
        if os.getenv("OPENAI_API_KEY"):
            services["OpenAI"] = "✅ API Key Set"
        else:
            services["OpenAI"] = "❌ No API Key"
    except Exception as e:
        services["OpenAI"] = f"❌ {str(e)}"
    
    return services

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
        
        refresh_cache.click(get_cache_status, outputs=cache_info)
        test_services_btn.click(test_services, outputs=service_status)
        
        # Load initial status on startup
        demo.load(get_cache_status, outputs=cache_info)
        demo.load(test_services, outputs=service_status)
    
    return demo

def main():
    """Main entry point"""
    print("🚀 Starting RAG Chat Interface...")
    
    # Check if required services are available
    print("🔍 Checking service connectivity...")
    status = test_services()
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
