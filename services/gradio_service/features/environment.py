# Behave configuration for gradio service BDD tests

from behave import *
import sys
import os

# Add the service directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def before_all(context):
    """Setup before all scenarios."""
    context.test_environment = "gradio_temporal_integration"
    
def before_scenario(context, scenario):
    """Setup before each scenario."""
    context.scenario_name = scenario.name
    
def after_scenario(context, scenario):
    """Cleanup after each scenario."""
    pass
