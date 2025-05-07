import sys
import json

def process_data(data):
    """Process the input data and return a capitalized version"""
    if isinstance(data, dict):
        return {k.upper(): v.upper() if isinstance(v, str) else v for k, v in data.items()}
    elif isinstance(data, str):
        return data.upper()
    else:
        return data

# Script expects JSON data as the first argument
if len(sys.argv) > 1:
    try:
        input_data = json.loads(sys.argv[1])
        result = process_data(input_data)
        print(json.dumps(result))
    except json.JSONDecodeError:
        # If not JSON, treat as simple string
        print(process_data(sys.argv[1]))
else:
    print("No input provided")
