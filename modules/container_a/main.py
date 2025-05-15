#!/usr/bin/env python3
"""
Container A module - Generates a JSON file
"""
import json
import argparse
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Container A: Generate JSON data")
    parser.add_argument("--output", default="output.json", help="Output file path")
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting Container A with output path: {args.output}")
        
        # Create data dictionary
        data = {
            "message": "Hello from Container A",
            "value": 42,
            "timestamp": "2025-05-14T12:00:00Z"
        }
        
        # Save to output file
        output_path = args.output
        
        # Ensure directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created directory: {output_dir}")
            
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Data written to {output_path}: {data}")
        
        # Print output location for debugging
        print(f"Output file created at: {os.path.abspath(output_path)}")
    except Exception as e:
        logger.exception(f"Error in Container A: {e}")
        raise
    
if __name__ == "__main__":
    main()
