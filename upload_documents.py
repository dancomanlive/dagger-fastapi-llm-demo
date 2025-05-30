#!/usr/bin/env python3
"""
Simple utility to load PDF files from test_data directory and trigger temporal workflow processing.
"""
import argparse
import os
import sys
import requests
import PyPDF2


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return "\n".join(page.extract_text() for page in pdf_reader.pages).strip()
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


def trigger_temporal_workflow(documents: list, temporal_api_url: str = "http://localhost:8003") -> bool:
    """Send documents to temporal service for processing."""
    try:
        payload = {
            "documents": documents
        }
        
        response = requests.post(
            f"{temporal_api_url}/process-documents",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            workflow_id = result.get("workflow_id")
            print(f"✅ Workflow started successfully! ID: {workflow_id}")
            print(f"📊 Track progress at: {temporal_api_url}/workflow/{workflow_id}/status")
            return True
        else:
            print(f"❌ Failed to start workflow. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to temporal service: {e}")
        print("Make sure the temporal service is running at {temporal_api_url}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Load PDFs and trigger temporal workflow processing.")
    parser.add_argument("--test-data-dir", default="test_data", help="Directory containing PDF files")
    parser.add_argument("--temporal-api", default="http://localhost:8003", help="Temporal API URL")
    parser.add_argument("--dry-run", action="store_true", help="Load documents but don't trigger workflow")
    args = parser.parse_args()

    print(f"Loading PDFs from: {args.test_data_dir}")
    
    if not os.path.exists(args.test_data_dir):
        print(f"Error: Directory '{args.test_data_dir}' does not exist.")
        print("Please create the directory and add PDF files.")
        sys.exit(1)
    
    documents = load_pdfs_from_directory(args.test_data_dir)
    
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
        success = trigger_temporal_workflow(documents, args.temporal_api)
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
