"""
Workflow planning tools for creating activity sequences based on user intent.
Part of the Pattern 2 workflow: ... → Plan Workflow → Generate Temporal Workflow → ...
"""
from typing import Dict, Any
from smolagents import tool


@tool
def plan_activity_sequence(intent: Dict[str, Any], available_activities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plan a sequence of activities based on user intent and available activities.
    
    Args:
        intent: Intent dictionary from infer_user_intent
        available_activities: Available activities from discover_services
        
    Returns:
        Dictionary with planned sequence and validation
    """
    try:
        plan = {
            "sequence": [],
            "missing_activities": [],
            "confidence": 0.0,
            "estimated_duration": "unknown",
            "complexity": "low"
        }
        
        primary_goal = intent.get("primary_goal", "unknown")
        domain = intent.get("domain", "general")
        
        # Build activity sequence based on intent
        if primary_goal == "search" and domain == "document_processing":
            desired_activities = [
                "validate_input",
                "extract_search_terms", 
                "generate_embeddings",
                "semantic_search",
                "filter_results",
                "rank_results",
                "format_response"
            ]
        elif primary_goal == "workflow_composition":
            desired_activities = [
                "discover_services",
                "analyze_requirements",
                "validate_activities",
                "generate_workflow",
                "test_workflow"
            ]
        elif primary_goal == "analysis":
            desired_activities = [
                "validate_input",
                "extract_data",
                "process_data",
                "analyze_results",
                "format_output"
            ]
        else:
            desired_activities = [
                "validate_input",
                "process_request",
                "format_output"
            ]
        
        # Map desired activities to available ones
        available_activity_names = []
        if "services" in available_activities:
            for service_name, service_info in available_activities["services"].items():
                activities = service_info.get("activities", {})
                available_activity_names.extend(activities.keys())
        
        # Find matches and missing activities
        for desired in desired_activities:
            # Exact match
            if desired in available_activity_names:
                plan["sequence"].append({
                    "activity": desired,
                    "service": "auto_detected",
                    "confidence": 1.0
                })
            else:
                # Fuzzy match
                matches = [act for act in available_activity_names if desired.lower() in act.lower() or act.lower() in desired.lower()]
                if matches:
                    plan["sequence"].append({
                        "activity": matches[0],
                        "service": "auto_detected", 
                        "confidence": 0.7,
                        "note": f"Fuzzy match for {desired}"
                    })
                else:
                    plan["missing_activities"].append(desired)
        
        # Calculate confidence and complexity
        total_desired = len(desired_activities)
        found_activities = len(plan["sequence"])
        plan["confidence"] = found_activities / total_desired if total_desired > 0 else 0.0
        
        if len(plan["sequence"]) > 5:
            plan["complexity"] = "high"
        elif len(plan["sequence"]) > 3:
            plan["complexity"] = "medium"
        
        plan["total_activities"] = len(plan["sequence"])
        plan["missing_count"] = len(plan["missing_activities"])
        plan["is_executable"] = len(plan["missing_activities"]) == 0
        
        return plan
        
    except Exception as e:
        return {"error": f"Failed to plan sequence: {str(e)}"}
