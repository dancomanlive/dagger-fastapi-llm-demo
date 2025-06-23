#!/usr/bin/env python3
"""
Test script to demonstrate dynamic services.yaml generation using CodeAgent.
This shows how the agent can introspect services and build configuration dynamically.
"""
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents/tools"))

def test_dynamic_generation_without_agent():
    """Test the dynamic generation tools directly without requiring OpenAI API."""
    from agents.tools.dynamic_yaml_generation import (
        generate_services_yaml_from_graphql,
        save_generated_services_yaml
    )
    
    print("🚀 TESTING DYNAMIC SERVICES.YAML GENERATION")
    print("=" * 60)
    print("🔍 Using direct tool calls (no OpenAI API required)")
    print("")
    
    # Step 1: Generate services.yaml from GraphQL introspection
    print("🔧 Step 1: Introspecting services via GraphQL...")
    generated_config = generate_services_yaml_from_graphql("../")
    
    if "error" in generated_config:
        print(f"❌ Generation failed: {generated_config['error']}")
        return
    
    print("✅ Generation successful!")
    print(f"   Services: {generated_config['discovery_metadata']['services_discovered']}")
    print(f"   Activities: {generated_config['discovery_metadata']['activities_discovered']}")
    print(f"   Pipelines: {generated_config['discovery_metadata']['pipelines_inferred']}")
    print("")
    
    # Step 2: Save generated configuration
    print("💾 Step 2: Saving generated configuration...")
    save_result = save_generated_services_yaml(generated_config, "generated/services_dynamic.yaml")
    print(f"   {save_result}")
    print("")
    
    print("🎯 DYNAMIC GENERATION TEST COMPLETE!")
    print("📁 Check the 'generated/' folder for output files")
    return generated_config

def test_with_agent():
    """Test using the actual CodeAgent (requires OpenAI API key)."""
    try:
        from agents.agent_factory import create_workflow_composer_agent
        
        print("🤖 TESTING WITH CODEAGENT")
        print("=" * 60)
        
        # Create the agent
        agent = create_workflow_composer_agent()
        
        # Test dynamic generation
        prompt = """
        Use your tools to dynamically generate a services.yaml configuration by introspecting 
        the actual service implementations in this workspace. Compare the generated configuration 
        with the existing services.yaml file. Show me what activities and pipelines you discover 
        through code analysis versus what's currently configured.
        """
        
        print("🎯 Sending prompt to agent...")
        result = agent.run(prompt)
        print("📝 Agent response:")
        print(result)
        
    except ImportError as e:
        print(f"❌ Agent test skipped: {e}")
        print("💡 This requires OpenAI API key and smolagents dependencies")
    except Exception as e:
        print(f"❌ Agent test failed: {e}")

if __name__ == "__main__":
    print("🎮 Choose test mode:")
    print("1. Direct tool testing (no API key required)")
    print("2. Full CodeAgent testing (requires OpenAI API key)")
    print("3. Both")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice in ["1", "3"]:
        print("\n" + "="*80)
        test_dynamic_generation_without_agent()
    
    if choice in ["2", "3"]:
        print("\n" + "="*80)
        test_with_agent()
    
    print("\n🎉 Testing complete!")
