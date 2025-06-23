"""
Smart workflow assistant - the main orchestrator for Pattern 2 dynamic workflow generation.
Implements the complete flow: User Message → Intent Inference → Activity Registry Query → Plan → Execute/Report
"""
from smolagents import tool

# Import the modular tools
from .intent_inference import infer_user_intent
from .service_discovery import discover_services_complete
from .workflow_planning import plan_activity_sequence
from .workflow_execution import execute_planned_workflow


@tool  
def smart_workflow_assistant(user_message: str) -> str:
    """
    The main smart workflow assistant that encapsulates the minimal, powerful agent-driven flow:
    User Message → Intent Inference → Activity Registry Query → Plan → Ask for Missing Input → Execute/Report
    
    This is the primary Pattern 2 tool that replaces static workflow definitions with dynamic, 
    agent-constructed workflows from primitives.
    
    Args:
        user_message: Natural language description of what the user wants to accomplish
        
    Returns:
        Formatted string with the complete workflow analysis and execution plan or results
    """
    try:
        result = []
        result.append("🤖 SMART WORKFLOW ASSISTANT")
        result.append("=" * 50)
        result.append(f"📝 Request: {user_message}")
        result.append("")
        
        # Step 1: Infer Intent
        result.append("🧠 STEP 1: INTENT ANALYSIS")
        intent = infer_user_intent(user_message)
        
        if "error" in intent:
            return f"❌ Intent analysis failed: {intent['error']}"
        
        result.append(f"  🎯 Primary Goal: {intent.get('primary_goal', 'unknown')}")
        result.append(f"  🔧 Action Type: {intent.get('action_type', 'unknown')}")
        result.append(f"  🏷️ Domain: {intent.get('domain', 'general')}")
        result.append(f"  📊 Confidence: {intent.get('confidence', 0.0):.1%}")
        
        if intent.get("requirements"):
            result.append(f"  📋 Requirements: {', '.join(intent['requirements'])}")
        
        result.append("")
        
        # Step 2: Discover Available Activities  
        result.append("🔍 STEP 2: ACTIVITY REGISTRY QUERY")
        available_activities = discover_services_complete()
        
        if "error" in available_activities:
            return f"❌ Service discovery failed: {available_activities['error']}"
        
        total_services = available_activities.get("total_services", 0)
        total_activities = sum(
            len(service.get("activities", {})) 
            for service in available_activities.get("services", {}).values()
        )
        
        result.append(f"  🏢 Services Found: {total_services}")
        result.append(f"  ⚙️ Activities Available: {total_activities}")
        result.append("")
        
        # Step 3: Plan Activity Sequence
        result.append("📋 STEP 3: ACTIVITY SEQUENCE PLANNING")
        plan = plan_activity_sequence(intent, available_activities)
        
        if "error" in plan:
            return f"❌ Planning failed: {plan['error']}"
        
        result.append(f"  📊 Confidence: {plan.get('confidence', 0.0):.1%}")
        result.append(f"  🔧 Complexity: {plan.get('complexity', 'unknown')}")
        result.append(f"  ✅ Activities Planned: {plan.get('total_activities', 0)}")
        result.append(f"  ❌ Missing Activities: {plan.get('missing_count', 0)}")
        result.append(f"  🚀 Executable: {'Yes' if plan.get('is_executable', False) else 'No'}")
        
        # Show planned sequence
        if plan.get("sequence"):
            result.append("  📝 Planned Sequence:")
            for i, step in enumerate(plan["sequence"], 1):
                confidence_indicator = "🎯" if step.get("confidence", 0) >= 0.9 else "⚠️" if step.get("confidence", 0) >= 0.7 else "❓"
                result.append(f"    {i}. {confidence_indicator} {step.get('activity', 'unknown')}")
                if step.get("note"):
                    result.append(f"       📝 {step['note']}")
        
        # Show missing activities
        if plan.get("missing_activities"):
            result.append("  ❌ Missing Activities:")
            for missing in plan["missing_activities"]:
                result.append(f"    • {missing}")
        
        result.append("")
        
        # Step 4: Execute or Report Missing Input
        if plan.get("is_executable", False):
            result.append("🚀 STEP 4: EXECUTION")
            execution = execute_planned_workflow(plan)
            
            if "error" in execution:
                result.append(f"  ❌ Execution Error: {execution['error']}")
            else:
                status_emoji = {
                    "completed": "✅",
                    "partial_success": "⚠️", 
                    "failed": "❌",
                    "in_progress": "🔄"
                }.get(execution.get("status"), "❓")
                
                result.append(f"  {status_emoji} Status: {execution.get('status', 'unknown')}")
                result.append(f"  📊 Success Rate: {execution.get('success_rate', 0.0):.1%}")
                result.append(f"  ✅ Steps Completed: {execution.get('steps_completed', 0)}/{execution.get('total_steps', 0)}")
                
                if execution.get("errors"):
                    result.append(f"  ❌ Errors: {len(execution['errors'])}")
        else:
            result.append("🔧 STEP 4: MISSING INPUT IDENTIFICATION")
            result.append("  Cannot execute workflow - missing required activities.")
            result.append("  📋 Required Actions:")
            
            for missing in plan.get("missing_activities", []):
                result.append(f"    • Implement activity: {missing}")
            
            result.append("")
            result.append("  💡 Suggestions:")
            result.append("    • Check if similar activities exist with different names")
            result.append("    • Implement missing activities in the appropriate services")
            result.append("    • Consider alternative workflow approaches")
        
        result.append("")
        result.append("📊 SUMMARY")
        
        if plan.get("is_executable", False):
            result.append("  🎉 Workflow successfully planned and executed!")
            result.append("  ✨ Your request has been processed using dynamic activity composition.")
        else:
            missing_count = plan.get("missing_count", 0)
            result.append(f"  🔧 Workflow planned but {missing_count} activities need implementation.")
            result.append("  📈 Progress: Analysis complete, execution pending required activities.")
        
        result.append("")
        result.append("🏗️ PATTERN 2 SUCCESS: Dynamic workflow constructed from primitives! 🎯")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"❌ Smart Workflow Assistant Error: {str(e)}"
