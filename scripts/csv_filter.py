import sys
import json
import csv
from io import StringIO

def filter_csv(csv_content, column, value):
    """Filter CSV data based on a column value
    
    Args:
        csv_content: CSV content as a string
        column: Column name to filter on
        value: Value to filter for
        
    Returns:
        Filtered CSV as a string
    """
    # Parse CSV
    reader = csv.DictReader(StringIO(csv_content))
    
    # Filter rows
    filtered_rows = [row for row in reader if row.get(column) == value]
    
    if not filtered_rows:
        return json.dumps({"error": f"No rows found with {column}={value}"})
    
    # Get headers
    headers = filtered_rows[0].keys()
    
    # Convert back to CSV
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(filtered_rows)
    
    # Return as JSON with both CSV and parsed data
    return json.dumps({
        "filtered_csv": output.getvalue(),
        "rows": filtered_rows,
        "count": len(filtered_rows)
    })

if __name__ == "__main__":
    # Check if we have enough arguments
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python csv_filter.py <column> <value>"}))
        sys.exit(1)
    
    column = sys.argv[1]
    value = sys.argv[2]
    
    # Read CSV from stdin
    if not sys.stdin.isatty():
        csv_content = sys.stdin.read()
        result = filter_csv(csv_content, column, value)
        print(result)
    else:
        print(json.dumps({"error": "No CSV data provided"}))
