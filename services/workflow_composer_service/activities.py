import json
import os
from pathlib import Path
from typing import Dict, List, Any
from temporalio import activity
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env" 
load_dotenv(env_file)

@activity.defn
async def discover_available_activities_activity() -> Dict[str, Any]:
    """
    Discover all available activities across all services
    """
    try:
        # Import here to avoid circular imports
        from agents.tools.service_discovery import discover_services
        
        services_info = discover_services()
        
        # Flatten the activities for easier analysis
        all_activities = {}
        for service_name, service_data in services_info.get('services', {}).items():
            for activity_name, activity_info in service_data.get('activities', {}).items():
                full_activity_id = f"{service_name}.{activity_name}"
                all_activities[full_activity_id] = {
                    "service": service_name,
                    "activity": activity_name,
                    "description": activity_info.get("description", ""),
                    "parameters": activity_info.get("parameters", [])
                }
        
        return {
            "available_activities": all_activities,
            "total_services": services_info.get('total_services', 0),
            "services_summary": services_info.get('services', {})
        }
        
    except Exception as e:
        return {
            "error": f"Failed to discover activities: {str(e)}",
            "available_activities": {},
            "total_services": 0
        }

@activity.defn
async def analyze_workflow_requirements_activity(workflow_description: str, requirements: List[str]) -> Dict[str, Any]:
    """
    Analyze workflow requirements and determine what activities are needed
    """
    try:
        # Use AI agent to analyze requirements
        if not os.getenv("OPENAI_API_KEY"):
            # Fallback: simple keyword-based analysis
            required_activities = []
            
            requirement_keywords = {
                "validate": ["utility_service.validate_inputs_activity"],
                "process": ["ai_service.generate_recommendations_activity"],
                "store": ["storage_service.store_results_activity"],  # May not exist
                "notification": ["notification_service.send_notification_activity"],  # May not exist
                "search": ["retriever_service.semantic_search_activity"],
                "embed": ["embedding_service.generate_embeddings_activity"],
                "format": ["utility_service.format_response_activity"]
            }
            
            for requirement in requirements:
                req_lower = requirement.lower()
                for keyword, activities in requirement_keywords.items():
                    if keyword in req_lower:
                        required_activities.extend(activities)
            
            # Remove duplicates
            required_activities = list(set(required_activities))
            
            return {
                "required_activities": required_activities,
                "analysis_method": "keyword_based",
                "workflow_description": workflow_description,
                "requirements": requirements
            }
        
        else:
            # Use AI agent for smarter analysis
            from agents.agent_factory import create_workflow_composer_agent
            
            agent = create_workflow_composer_agent()
            
            analysis_prompt = f"""
            Analyze this workflow description and requirements to determine what activities are needed:
            
            Workflow: {workflow_description}
            Requirements: {requirements}
            
            Based on typical workflow patterns, list the specific activity IDs that would be needed.
            Use this format for activity IDs: service_name.activity_name
            
            Common patterns:
            - Validation: utility_service.validate_inputs_activity
            - Data processing: ai_service.generate_recommendations_activity
            - Search: retriever_service.semantic_search_activity
            - Formatting: utility_service.format_response_activity
            - Storage: storage_service.store_results_activity (if exists)
            - Notifications: notification_service.send_notification_activity (if exists)
            
            Return just a JSON list of required activity IDs.
            """
            
            result = agent.run(analysis_prompt)
            
            # Try to extract JSON from result
            if isinstance(result, list):
                required_activities = result
            elif isinstance(result, str):
                # Try to parse as JSON
                try:
                    required_activities = json.loads(result)
                except Exception:
                    # Fallback to simple extraction
                    required_activities = []
                    lines = result.split('\n')
                    for line in lines:
                        if '.' in line and '_activity' in line:
                            # Extract activity ID
                            parts = line.split()
                            for part in parts:
                                if '.' in part and '_activity' in part:
                                    required_activities.append(part.strip('",[]()'))
            else:
                required_activities = []
            
            return {
                "required_activities": required_activities,
                "analysis_method": "ai_agent",
                "workflow_description": workflow_description,
                "requirements": requirements,
                "agent_result": str(result)
            }
            
    except Exception as e:
        return {
            "error": f"Failed to analyze requirements: {str(e)}",
            "required_activities": [],
            "analysis_method": "error"
        }

@activity.defn
async def validate_activity_availability_activity(required_activities: List[str], available_activities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that all required activities are available
    """
    try:
        missing_activities = []
        available_activity_ids = list(available_activities.keys())
        
        for required_activity in required_activities:
            if required_activity not in available_activity_ids:
                missing_activities.append(required_activity)
        
        is_complete = len(missing_activities) == 0
        
        return {
            "is_complete": is_complete,
            "missing_activities": missing_activities,
            "available_activities": available_activity_ids,
            "required_activities": required_activities,
            "validation_status": "COMPLETE" if is_complete else "INCOMPLETE"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to validate activities: {str(e)}",
            "is_complete": False,
            "missing_activities": [],
            "validation_status": "ERROR"
        }

@activity.defn
async def generate_workflow_if_complete_activity(workflow_name: str, workflow_description: str, validation_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the workflow if all required activities are available, otherwise report missing activities
    """
    try:
        if not validation_result.get("is_complete", False):
            return {
                "status": "INCOMPLETE",
                "workflow_created": False,
                "missing_activities": validation_result.get("missing_activities", []),
                "message": f"Cannot create workflow '{workflow_name}' - missing required activities",
                "required_actions": [
                    f"Implement missing activity: {activity}" 
                    for activity in validation_result.get("missing_activities", [])
                ]
            }
        
        # All activities available - create the workflow
        from agents.tools.workflow_execution import create_workflow_from_activities
        
        # Create the workflow using the new modular approach
        workflow_config = {
            "name": workflow_name,
            "description": workflow_description,
            "activities": validation_result.get("required_activities", [])
        }
        
        result = create_workflow_from_activities(workflow_config)
        
        if result.get("success", False):
            return {
                "status": "COMPLETE",
                "workflow_created": True,
                "workflow_name": workflow_name,
                "workflow_result": result,
                "message": f"Successfully created workflow '{workflow_name}'"
            }
        else:
            return {
                "status": "FAILED",
                "workflow_created": False,
                "error": result.get("error", "Unknown error creating workflow"),
                "message": f"Failed to create workflow '{workflow_name}'"
            }
            
    except Exception as e:
        return {
            "status": "ERROR", 
            "workflow_created": False,
            "error": f"Exception during workflow generation: {str(e)}",
            "message": f"Error generating workflow '{workflow_name}'"
        }