# Document Upload Interface

A simple, user-friendly Gradio interface for uploading PDF documents to the SmartÆgent X-7 knowledge base.

## ✨ Features

- **Drag & Drop Upload**: Simply drag PDF files onto the interface
- **Real-time Processing**: See processing status and results immediately  
- **Workflow Monitoring**: Direct links to Temporal UI for tracking
- **Multiple Files**: Upload multiple PDFs at once
- **Automatic Processing**: Documents are automatically chunked, embedded, and indexed

## 🚀 Quick Start

### Option 1: Direct Launch
```bash
cd services/gradio_service
python upload_app.py
```

### Option 2: Launch Both Interfaces
```bash
cd services/gradio_service
python launch_both.py
```

### Option 3: From Root Directory
```bash
python upload_documents.py --start-service
```

## 🌐 Access Points

- **Upload Interface**: http://localhost:7861
- **Chat Interface**: http://localhost:7860  
- **Temporal Monitoring**: http://localhost:8081

## 📋 Requirements

- Temporal service running (`localhost:7233`)
- All microservices healthy (embedding, retrieval, etc.)
- Qdrant vector database available

## 🔄 Processing Flow

1. **Upload**: Select or drag PDF files
2. **Extract**: Text extraction from PDFs
3. **Process**: Trigger Temporal workflow
4. **Chunk**: Documents split into semantic chunks
5. **Embed**: Generate vector embeddings
6. **Index**: Store in Qdrant database
7. **Ready**: Available for chat queries

## 📁 Document Collections

Documents are stored in the `uploaded_documents` collection by default. You can query them in the chat interface by selecting this collection.

## ⚠️ Migration Notice

This interface replaces the complex command-line `upload_documents.py` script. The original script is backed up as `upload_documents.py.backup` for reference.

## 🛠️ Development

The upload interface is built with:
- **Gradio**: Web interface framework
- **PyPDF2**: PDF text extraction
- **Temporalio**: Workflow orchestration client
- **AsyncIO**: Asynchronous processing

## 🔍 Troubleshooting

### Service Connection Issues
```bash
# Check Temporal connection
docker-compose ps temporal

# Check service logs
docker-compose logs -f embedding-service
docker-compose logs -f retrieval-service
```

### Upload Issues
- Ensure files are valid PDFs
- Check file permissions
- Verify Temporal workers are running

### Processing Issues
- Monitor workflow in Temporal UI
- Check service health in docker-compose
- Review error messages in the interface
