#!/usr/bin/env python3
"""
Simple utility to load PDF files and trigger temporal workflow processing.
Updated to work with Temporal client directly.
"""
import argparse
import os
import sys
import asyncio
import PyPDF2
from temporalio.client import Client
from datetime import timedelta


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    print(f"🔍 Extracting text from {pdf_path}...")
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pages = len(pdf_reader.pages)
            print(f"  📄 Found {pages} pages")
            
            # Process pages in smaller chunks to avoid hanging
            text_parts = []
            batch_size = 10
            for i in range(0, pages, batch_size):
                end_idx = min(i + batch_size, pages)
                print(f"  📑 Processing pages {i+1}-{end_idx}...")
                
                batch_text = []
                for page_idx in range(i, end_idx):
                    try:
                        page_text = pdf_reader.pages[page_idx].extract_text()
                        batch_text.append(page_text)
                    except Exception as e:
                        print(f"    ⚠️ Error on page {page_idx+1}: {e}")
                        batch_text.append("")
                
                text_parts.extend(batch_text)
            
            full_text = "\n".join(text_parts).strip()
            print(f"  ✅ Extracted {len(full_text)} characters")
            return full_text
            
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}", file=sys.stderr)
        return ""


def load_pdfs_from_directory(directory: str) -> list:
    """Load PDFs from directory and return document list formatted for temporal API."""
    documents = []
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return documents
    
    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(directory, pdf_file)
        text = extract_text_from_pdf(pdf_path)
        if text:
            documents.append({
                "id": str(i),
                "text": text,
                "metadata": {
                    "source": pdf_file,
                    "path": pdf_path
                }
            })
        else:
            print(f"Warning: Could not extract text from {pdf_file}")
    
    return documents


async def trigger_temporal_workflow(documents: list, temporal_host: str = "localhost:7233", wait_for_completion: bool = False) -> bool:
    """Send documents to temporal service for processing via Temporal client."""
    try:
        client = await Client.connect(f"{temporal_host}")
        
        # Start the document processing workflow
        workflow_id = f"upload-docs-{len(documents)}-{asyncio.get_event_loop().time():.0f}"
        
        handle = await client.start_workflow(
            "DocumentProcessingWorkflow",
            documents,  # Just pass documents directly - workflow expects this as first parameter
            id=workflow_id,
            task_queue="document-processing-queue",
            execution_timeout=timedelta(minutes=10),
        )
        
        print(f"✅ Workflow started successfully! ID: {workflow_id}")
        print(f"📊 Track progress at: http://localhost:8081/namespaces/default/workflows/{workflow_id}")
        
        if wait_for_completion:
            print("⏳ Waiting for workflow to complete...")
            result = await handle.result()
            print(f"🎉 Workflow completed! Result: {result}")
        else:
            print("⏳ Use --wait flag to wait for workflow completion...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to temporal service: {e}")
        print(f"Make sure the temporal service is running at {temporal_host}")
        return False


async def main_async():
    parser = argparse.ArgumentParser(description="Load PDFs and trigger temporal workflow processing.")
    parser.add_argument("--temporal-host", default="localhost:7233", help="Temporal host:port")
    parser.add_argument("--directory", default="document_files", help="Directory containing PDF files")
    parser.add_argument("--dry-run", action="store_true", help="Load documents but don't trigger workflow")
    parser.add_argument("--wait", action="store_true", help="Wait for workflow completion")
    args = parser.parse_args()

    data_directory = args.directory
    print(f"Loading PDFs from: {data_directory}")
    
    if not os.path.exists(data_directory):
        print(f"Error: Directory '{data_directory}' does not exist.")
        print("Please create the directory and add PDF files.")
        sys.exit(1)
    
    documents = load_pdfs_from_directory(data_directory)
    
    if not documents:
        print("No documents loaded. Please add PDF files to the directory.")
        sys.exit(1)

    print(f"Successfully loaded {len(documents)} documents")
    
    if args.dry_run:
        print("🔍 Dry run mode - documents ready but workflow not triggered")
        for doc in documents:
            print(f"  - {doc['id']}: {doc['metadata']['source']} ({len(doc['text'])} chars)")
    else:
        print("🚀 Triggering temporal workflow...")
        success = await trigger_temporal_workflow(documents, args.temporal_host, args.wait)
        if not success:
            sys.exit(1)


def main():
    """Main entry point that runs the async main function."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
