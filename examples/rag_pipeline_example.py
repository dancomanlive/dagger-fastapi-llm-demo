"""
DEPRECATED: This file exists for backward compatibility.
Please use the rag_pipeline_example.py instead, which demonstrates
the optimized RAG components.
"""
import sys
import os

def main():
    print("⚠️  DEPRECATED: The non-RAG pipeline has been removed.")
    print("✨ Please use rag_pipeline_example.py instead, which demonstrates")
    print("   the optimized RAG components.")
    print("\nRedirecting to example...")
    
    # Get the path to the example
    current_dir = os.path.dirname(os.path.abspath(__file__))
    example_path = os.path.join(current_dir, "rag_pipeline_example.py")
    
    # Check if the example exists
    if os.path.exists(example_path):
        print("\nTo run the example, use:")
        print(f"python {example_path}")
        sys.exit(1)
    else:
        print("Error: Example not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
