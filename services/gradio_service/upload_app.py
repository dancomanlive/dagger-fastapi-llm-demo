#!/usr/bin/env python3
"""
Simple Gradio Upload Interface for Document Processing

This file provides a clean, simple Gradio interface for uploading PDF documents
and triggering the Temporal workflow for document processing. It replaces the 
complex command-line upload_documents.py script with an intuitive web interface.
"""

import gradio as gr
import asyncio
import PyPDF2
import os
import time
from typing import List
from temporalio.client import Client
from datetime import timedelta


class DocumentUploader:
    """Handles document upload and processing via Temporal workflows"""
    
    def __init__(self, temporal_host: str = None):
        self.temporal_host = temporal_host or os.environ.get("TEMPORAL_HOST", "localhost:7233")
        self.collection_name = "uploaded_documents"
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pages = len(pdf_reader.pages)
                
                text_parts = []
                for page_idx in range(pages):
                    try:
                        page_text = pdf_reader.pages[page_idx].extract_text()
                        text_parts.append(page_text)
                    except Exception as e:
                        print(f"Warning: Error on page {page_idx+1}: {e}")
                        text_parts.append("")
                
                full_text = "\n".join(text_parts).strip()
                return full_text
                
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def process_uploaded_files(self, files: List) -> List[dict]:
        """Process uploaded files and return document list"""
        if not files:
            return []
        
        documents = []
        for i, file_info in enumerate(files, 1):
            # file_info is a file path string when uploaded via Gradio
            file_path = file_info if isinstance(file_info, str) else file_info.name
            filename = os.path.basename(file_path)
            
            if not filename.lower().endswith('.pdf'):
                continue
                
            text = self.extract_text_from_pdf(file_path)
            if text:
                documents.append({
                    "id": str(i),
                    "text": text,
                    "metadata": {
                        "source": filename,
                        "path": file_path,
                        "upload_time": time.time()
                    }
                })
        
        return documents
    
    async def trigger_workflow(self, documents: List[dict]) -> tuple[bool, str]:
        """Trigger Temporal workflow for document processing"""
        if not documents:
            return False, "No documents to process"
        
        try:
            client = await Client.connect(self.temporal_host)
            
            workflow_id = f"upload-processing-{len(documents)}-{int(time.time())}"
            
            handle = await client.start_workflow(
                "GenericPipelineWorkflow",
                args=["document_processing", {"documents": documents, "collection": self.collection_name}],
                id=workflow_id,
                task_queue="document-processing-queue",
                execution_timeout=timedelta(minutes=10),
            )
            
            # Wait for completion
            await handle.result()
            
            success_msg = f"""
            ✅ **Documents processed successfully!**
            
            - **Workflow ID:** {workflow_id}
            - **Documents processed:** {len(documents)}
            - **Collection:** {self.collection_name}
            - **Status:** Completed
            
            📊 **Monitor workflow:** [Temporal UI](http://localhost:8081/namespaces/default/workflows/{workflow_id})
            
            Your documents are now searchable in the chat interface!
            """
            
            return True, success_msg
            
        except Exception as e:
            error_msg = f"""
            ❌ **Error processing documents:**
            
            {str(e)}
            
            Please ensure:
            - Temporal service is running at {self.temporal_host}
            - All services are healthy
            - Check docker-compose logs for details
            """
            return False, error_msg


def create_upload_interface():
    """Create the Gradio upload interface"""
    
    uploader = DocumentUploader()
    
    def process_and_upload(files):
        """Process files and trigger workflow (sync wrapper for async function)"""
        if not files:
            return "Please upload at least one PDF file.", ""
        
        # Process files
        documents = uploader.process_uploaded_files(files)
        
        if not documents:
            return "No valid PDF files found. Please upload PDF files only.", ""
        
        # Show processing status
        file_list = "\n".join([f"- {doc['metadata']['source']} ({len(doc['text'])} characters)" 
                              for doc in documents])
        processing_msg = f"""
        📄 **Files processed:**
        {file_list}
        
        🔄 **Triggering Temporal workflow...**
        """
        
        # Trigger workflow asynchronously
        try:
            success, result_msg = asyncio.run(uploader.trigger_workflow(documents))
            return processing_msg, result_msg
        except Exception as e:
            error_msg = f"❌ **Workflow error:** {str(e)}"
            return processing_msg, error_msg
    
    # Custom CSS for better styling
    css = """
    .upload-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    .status-box {
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
    }
    """
    
    with gr.Blocks(
        title="Document Upload - SmartÆgent X-7",
        theme=gr.themes.Soft(),
        css=css
    ) as demo:
        
        gr.Markdown("""
        # 📄 Document Upload
        
        Upload PDF documents to add them to the knowledge base. Documents will be processed through the Temporal workflow pipeline and made available for search in the chat interface.
        """)
        
        with gr.Row():
            with gr.Column():
                # File upload component
                file_upload = gr.File(
                    label="Upload PDF Documents",
                    file_types=[".pdf"],
                    file_count="multiple",
                    height=200
                )
                
                upload_btn = gr.Button(
                    "Process Documents",
                    variant="primary",
                    size="lg"
                )
        
        with gr.Row():
            with gr.Column():
                # Status displays
                processing_status = gr.Markdown(
                    label="Processing Status",
                    visible=True
                )
                
                result_status = gr.Markdown(
                    label="Result",
                    visible=True
                )
        
        # Footer info
        gr.Markdown("""
        ---
        ### ℹ️ Information
        
        - **Supported formats:** PDF files only
        - **Processing:** Documents are chunked, embedded, and indexed automatically
        - **Collection:** Documents are stored in the `uploaded_documents` collection
        - **Monitoring:** Track progress in the [Temporal UI](http://localhost:8081)
        - **Chat:** Use processed documents in the [Chat Interface](http://localhost:7860)
        
        ### 🔧 System Requirements
        - Temporal service running on `localhost:7233`
        - Embedding and retrieval services active
        - Qdrant vector database available
        """)
        
        # Event handlers
        upload_btn.click(
            fn=process_and_upload,
            inputs=[file_upload],
            outputs=[processing_status, result_status],
            show_progress="full"
        )
    
    return demo


def main():
    """Main entry point"""
    print("🚀 Starting Document Upload Interface...")
    print("=" * 50)
    
    # Get Temporal host from environment (same as DocumentUploader)
    temporal_host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    host, port = temporal_host.split(':')
    port = int(port)
    
    # Check if Temporal is accessible
    try:
        # Simple connection test
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result != 0:
            print(f"⚠️  Warning: Cannot connect to Temporal at {temporal_host}")
            print("   Make sure Temporal service is running with: docker-compose up -d")
        else:
            print(f"✅ Temporal service connection OK at {temporal_host}")
    except Exception as e:
        print(f"⚠️  Warning: Cannot test Temporal connection: {e}")
    
    print("=" * 50)
    
    # Create and launch interface
    demo = create_upload_interface()
    
    try:
        demo.launch(
            server_name="0.0.0.0",
            server_port=7861,  # Different port from main chat interface
            share=False,
            show_error=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error starting upload interface: {e}")


if __name__ == "__main__":
    main()
