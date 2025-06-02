# Test Data

Place your PDF files in this directory for testing the RAG pipeline.

The `upload_documents.py` script will automatically process all PDF files in this folder and add them to the Qdrant vector database.

## Supported formats:
- PDF files (.pdf)

## Example usage:
1. Copy your PDF files to this directory
2. Run: `python upload_documents.py`
3. The script will extract text from PDFs and prepare them for the temporal service

## Custom folder:
Use a different directory: `python upload_documents.py --test-data-dir /path/to/your/pdfs`
