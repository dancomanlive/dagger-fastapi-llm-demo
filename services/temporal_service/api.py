"""
FastAPI service for Temporal workflow management.
Provides HTTP endpoints to start and monitor document processing workflows.
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from temporalio.client import Client
from dotenv import load_dotenv

from workflows import DocumentProcessingWorkflow

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "document-processing-queue")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8000")

app = FastAPI(title="Temporal Document Processing Service")

# Pydantic models
class Document(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = {}

class ProcessDocumentsRequest(BaseModel):
    documents: List[Document]
    workflow_id: Optional[str] = None
    embedding_service_url: Optional[str] = None

class WorkflowStatus(BaseModel):
    workflow_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Global client
temporal_client: Optional[Client] = None

@app.on_event("startup")
async def startup_event():
    """Connect to Temporal on startup."""
    global temporal_client
    try:
        temporal_client = await Client.connect(
            TEMPORAL_HOST,
            namespace=TEMPORAL_NAMESPACE
        )
        logger.info(f"Connected to Temporal at {TEMPORAL_HOST}")
    except Exception as e:
        logger.error(f"Failed to connect to Temporal: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    global temporal_client
    if temporal_client:
        # No explicit close method needed for Temporal client
        temporal_client = None

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "temporal-document-processing"}

@app.post("/process-documents", response_model=Dict[str, str])
async def process_documents(request: ProcessDocumentsRequest):
    """
    Start a document processing workflow.
    
    Args:
        request: Documents to process and optional configuration
        
    Returns:
        Workflow ID for tracking
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not available")
    
    # Generate workflow ID if not provided
    workflow_id = request.workflow_id or f"doc-processing-{uuid.uuid4()}"
    
    # Use provided embedding service URL or default
    embedding_url = request.embedding_service_url or EMBEDDING_SERVICE_URL
    
    # Convert documents to dict format
    documents_data = [doc.model_dump() for doc in request.documents]
    
    try:
        # Start the workflow with corrected argument usage
        await temporal_client.start_workflow(
            DocumentProcessingWorkflow.run,
            args=[documents_data, embedding_url],
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )
        
        logger.info(f"Started workflow {workflow_id} for {len(documents_data)} documents")
        
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "message": f"Processing {len(documents_data)} documents"
        }
        
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

@app.get("/workflow/{workflow_id}/status", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str):
    """
    Get the status of a workflow.
    
    Args:
        workflow_id: ID of the workflow to check
        
    Returns:
        Workflow status and result if completed
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not available")
    
    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)
        
        # Check if workflow is running
        try:
            # This will raise an exception if workflow is still running
            result = await handle.result()
            return WorkflowStatus(
                workflow_id=workflow_id,
                status="completed",
                result=result
            )
        except Exception as e:
            # Workflow might still be running or failed
            try:
                # Try to get workflow description for more details
                description = await handle.describe()
                status = description.status.name.lower() if description.status else "unknown"
                
                return WorkflowStatus(
                    workflow_id=workflow_id,
                    status=status,
                    error=str(e) if status == "failed" else None
                )
            except Exception as describe_error:
                return WorkflowStatus(
                    workflow_id=workflow_id,
                    status="unknown",
                    error=f"Failed to get status: {str(describe_error)}"
                )
                
    except Exception as e:
        logger.error(f"Error checking workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check workflow status: {str(e)}")

@app.get("/workflow/{workflow_id}/result")
async def get_workflow_result(workflow_id: str):
    """
    Wait for and return the workflow result.
    
    Args:
        workflow_id: ID of the workflow
        
    Returns:
        Workflow result
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not available")
    
    try:
        handle = temporal_client.get_workflow_handle(workflow_id)
        result = await handle.result()
        return result
    except Exception as e:
        logger.error(f"Error getting workflow result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow result: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
