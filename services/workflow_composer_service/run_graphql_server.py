#!/usr/bin/env python3
"""
GraphQL server for workflow composer service.
Provides service introspection and dynamic workflow composition capabilities.
"""
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from gql_schema.schema import schema

# Create FastAPI app
app = FastAPI(
    title="Workflow Composer GraphQL API",
    description="Dynamic service introspection and workflow composition",
    version="1.0.0"
)

# Create GraphQL router
graphql_app = GraphQLRouter(schema)

# Add GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "workflow_composer_graphql"}

# Services endpoint for REST compatibility
@app.get("/services")
async def get_services():
    """Get services from production discovery system."""
    try:
        from gql_schema.schema import get_services_with_discovery_info, run_async
        
        discovery_data = run_async(get_services_with_discovery_info())
        services_data = discovery_data.get("services", {})
        
        # Convert to REST API format
        services = {}
        for service_name, service_info in services_data.items():
            services[service_name] = {
                "task_queue": service_info.get("task_queue"),
                "worker_identity": service_info.get("worker_identity"),
                "health": service_info.get("health"),
                "version": service_info.get("version"),
                "temporal_status": service_info.get("temporal_status"),
                "activities": {}
            }
            
            for activity_name, activity_data in service_info.get("activities", {}).items():
                services[service_name]["activities"][activity_name] = activity_data
        
        return {"services": services}
    except Exception as e:
        return {"error": str(e), "services": {}}

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Workflow Composer GraphQL Server...")
    print("🔍 GraphQL Playground: http://localhost:8001/graphql")
    print("📖 REST Services API: http://localhost:8001/services")
    print("💚 Health Check: http://localhost:8001/health")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)