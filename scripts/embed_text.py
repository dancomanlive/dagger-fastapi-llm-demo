import sys
import json
import os
from sentence_transformers import SentenceTransformer

# Replace the placeholder with the actual embedding model
def get_embeddings(texts):
    """Generate embeddings for a list of text chunks."""
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    embeddings = model.encode(texts)
    return embeddings.tolist()

if __name__ == "__main__":
    # Check if OPENAI_API_KEY is set
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print(json.dumps({"error": "OPENAI_API_KEY not set in environment"}))
        sys.exit(1)
        
    # Input should be a JSON object with 'chunks' field containing text chunks
    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
            chunks = data.get('chunks', [])
            
            if not chunks:
                print(json.dumps({"error": "No text chunks provided"}))
                sys.exit(1)
                
            # Generate embeddings
            embeddings = get_embeddings(chunks)
            
            result = {
                'embeddings': embeddings,
                'chunks': chunks,
                'count': len(chunks),
                'dimensions': len(embeddings[0]) if embeddings else 0
            }
            print(json.dumps(result))
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON input"}))
    else:
        print(json.dumps({"error": "No input provided"}))
