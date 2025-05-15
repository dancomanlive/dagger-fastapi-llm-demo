#!/usr/bin/env python3
"""
Container B module - Processes JSON data from Container A
"""
import json
import argparse
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Container B: Process JSON data")
    parser.add_argument("--input", required=True, help="Input JSON file path")
    parser.add_argument("--output", default="processed_output.json", help="Output file path")
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting Container B with input: {args.input}, output: {args.output}")
        
        # Read input file
        with open(args.input, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Input data: {data}")
        
        # Process the data
        processed_data = {
            "original_message": data["message"],
            "original_value": data["value"],
            "processed_message": f"Processed: {data['message']}",
            "processed_value": data["value"] * 2,
            "timestamp": data.get("timestamp", "no timestamp provided")
        }
        
        # Save to output file
        output_path = args.output
        
        # Ensure directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created directory: {output_dir}")
            
        with open(args.output, 'w') as f:
            json.dump(processed_data, f, indent=2)
        
        logger.info(f"Processed data written to {args.output}")
        
        # Also print to stdout
        print(json.dumps(processed_data, indent=2))
    except Exception as e:
        logger.exception(f"Error in Container B: {e}")
        raise
    
if __name__ == "__main__":
    main()
