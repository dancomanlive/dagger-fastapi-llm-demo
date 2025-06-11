#!/usr/bin/env python3
"""
Test runner for Behave integration tests.

This script provides a convenient way to run the Behave BDD tests
for the temporal service integration.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run Behave tests."""
    # Change to the temporal service directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    logger.info("Running Behave integration tests...")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Check if behave is available
    try:
        result = subprocess.run(
            [sys.executable, "-m", "behave", "--version"], 
            capture_output=True, 
            text=True
        )
        logger.info(f"Behave version: {result.stdout.strip()}")
    except Exception as e:
        logger.error(f"Behave not available: {e}")
        logger.info("Install with: pip install behave behave-async")
        return 1
    
    # Prepare environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(script_dir)
    
    # Run behave tests
    cmd = [
        sys.executable, "-m", "behave",
        "--format", "pretty",
        "--show-timings",
        "--logging-level", "INFO",
        "features/"
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, env=env)
        return result.returncode
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
