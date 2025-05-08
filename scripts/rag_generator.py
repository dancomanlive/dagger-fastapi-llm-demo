import sys
import json
import os
import openai
import re

def generate_response_with_citations(query, context_chunks, chunk_metadata=None, model="gpt-4o-mini"):
    """Generate a response using RAG with OpenAI, including citations to source chunks."""
    # Set up OpenAI API
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return {"error": "OPENAI_API_KEY not set in environment"}
    
    openai.api_key = api_key
    
    # Create chunk IDs for citation
    chunk_ids = []
    for i, _ in enumerate(context_chunks):
        # Use provided metadata or generate simple chunk ID
        if chunk_metadata and i < len(chunk_metadata) and 'document_id' in chunk_metadata[i]:
            chunk_id = f"{chunk_metadata[i]['document_id']}:{i}"
        else:
            chunk_id = f"chunk_{i}"
        chunk_ids.append(chunk_id)
    
    # Format context chunks with IDs for reference
    formatted_context = ""
    for i, chunk in enumerate(context_chunks):
        formatted_context += f"[{chunk_ids[i]}]: {chunk}\n\n"
    
    # Prepare prompt with citation instructions
    system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
Use information from the context to answer the question thoroughly. 
When you use information from the context, cite the source using the format [source_id].
If multiple chunks contain relevant information, cite all of them like [source_id1][source_id2].
If the context doesn't contain enough information, say so and suggest what other information might help."""
    
    user_prompt = f"""Context information:
{formatted_context}

Based only on the above context, please answer the following question, including citations to the relevant chunks:
{query}"""
    
    # Generate response using OpenAI
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        response_text = response.choices[0].message.content
        
        # Post-process to extract citations
        used_chunks = []
        for i, chunk_id in enumerate(chunk_ids):
            if f"[{chunk_id}]" in response_text:
                used_chunks.append({
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "text": context_chunks[i],
                    "metadata": chunk_metadata[i] if chunk_metadata and i < len(chunk_metadata) else {}
                })
        
        return {
            "status": "success",
            "query": query,
            "response": response_text,
            "model": model,
            "context_chunks_used": len(used_chunks),
            "citations": used_chunks
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    # Check if OpenAI API key is set
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print(json.dumps({"error": "OPENAI_API_KEY not set in environment"}))
        sys.exit(1)
        
    # Input should be a JSON object
    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
            query = data.get('query')
            context_chunks = data.get('context_chunks', [])
            chunk_metadata = data.get('chunk_metadata', [])
            model = data.get('model', 'gpt-4o-mini')
            
            if not query:
                print(json.dumps({"error": "query is required"}))
                sys.exit(1)
                
            if not context_chunks:
                print(json.dumps({"error": "context_chunks is required"}))
                sys.exit(1)
                
            # Generate response with citations
            result = generate_response_with_citations(query, context_chunks, chunk_metadata, model)
            print(json.dumps(result))
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON input"}))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
    else:
        print(json.dumps({"error": "No input provided"}))
