"""
Advanced text chunking module with intelligent document structure awareness.
"""
import re
import json
import sys
from typing import List, Dict, Any, Optional, Tuple

def detect_document_sections(text: str) -> List[Dict[str, Any]]:
    """
    Detect document sections based on heading patterns.
    
    Args:
        text: Document text
        
    Returns:
        List of sections with text and metadata
    """
    # Define patterns for section headings
    heading_patterns = [
        (r'^#+\s+(.+)$', 'markdown_heading'),  # Markdown headings
        (r'^(\d+\.(\d+\.)*)\s+(.+)$', 'numbered_heading'),  # Numbered headings
        (r'^([A-Z][a-z]+(\s+[A-Z][a-z]+){0,5})$', 'capitalized_heading'),  # Capitalized short sentences
    ]
    
    # Split text into lines
    lines = text.split('\n')
    
    sections = []
    current_section = {"text": "", "metadata": {"level": 0, "title": "Default Section"}}
    current_level = 0
    
    for line in lines:
        is_heading = False
        
        # Check for heading patterns
        for pattern, heading_type in heading_patterns:
            match = re.match(pattern, line, re.MULTILINE)
            if match:
                # Save previous section if it has content
                if current_section["text"].strip():
                    sections.append(current_section)
                
                # Determine heading level
                if heading_type == 'markdown_heading':
                    level = line.count('#')
                    title = match.group(1)
                elif heading_type == 'numbered_heading':
                    level = line.count('.')
                    title = match.group(3)
                else:
                    level = 1
                    title = match.group(0)
                
                # Create new section
                current_section = {
                    "text": line + "\n",
                    "metadata": {
                        "level": level,
                        "title": title,
                        "heading_type": heading_type
                    }
                }
                current_level = level
                is_heading = True
                break
        
        if not is_heading:
            current_section["text"] += line + "\n"
    
    # Add the last section
    if current_section["text"].strip():
        sections.append(current_section)
    
    return sections

def chunk_document_with_overlap(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    respect_sections: bool = True
) -> List[Dict[str, Any]]:
    """
    Intelligently chunk a document with overlap, respecting section boundaries when possible.
    
    Args:
        text: Document text
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        respect_sections: Whether to try to keep sections intact
        
    Returns:
        List of chunks with metadata
    """
    chunks = []
    
    if respect_sections:
        sections = detect_document_sections(text)
        
        for section_idx, section in enumerate(sections):
            section_text = section["text"]
            section_metadata = section["metadata"]
            
            # If section is smaller than chunk_size, keep it whole
            if len(section_text) <= chunk_size:
                chunks.append({
                    "text": section_text,
                    "metadata": {
                        "section_idx": section_idx,
                        "chunk_idx": 0,
                        "is_section_start": True,
                        "is_section_end": True,
                        **section_metadata
                    }
                })
            else:
                # Split section into chunks
                section_chunks = split_text_with_overlap(section_text, chunk_size, overlap)
                
                for chunk_idx, chunk_text in enumerate(section_chunks):
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "section_idx": section_idx,
                            "chunk_idx": chunk_idx,
                            "is_section_start": chunk_idx == 0,
                            "is_section_end": chunk_idx == len(section_chunks) - 1,
                            **section_metadata
                        }
                    })
    else:
        # Simple chunking without section awareness
        simple_chunks = split_text_with_overlap(text, chunk_size, overlap)
        
        for i, chunk_text in enumerate(simple_chunks):
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "chunk_idx": i,
                    "is_section_start": i == 0,
                    "is_section_end": i == len(simple_chunks) - 1
                }
            })
    
    return chunks

def split_text_with_overlap(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Split text into chunks with overlap.
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    chunks = []
    
    # If text is smaller than chunk_size, return as is
    if len(text) <= chunk_size:
        return [text]
    
    # Split text into chunks with overlap
    start = 0
    while start < len(text):
        # Get chunk of size chunk_size or remaining text if smaller
        end = min(start + chunk_size, len(text))
        
        # Try to find a good boundary (period followed by space or newline)
        if end < len(text):
            # Search for a sentence boundary within the last 20% of the chunk
            search_start = max(start + int(chunk_size * 0.8), start)
            boundary_match = re.search(r'[.!?]\s+', text[search_start:end])
            
            if boundary_match:
                # Adjust end to the sentence boundary
                end = search_start + boundary_match.end()
        
        # Extract chunk
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Move start position for next chunk, considering overlap
        start = max(start + chunk_size - overlap, start + 1)
        
        # Ensure progress
        if start >= len(text):
            break
    
    return chunks

def add_document_metadata(chunks: List[Dict[str, Any]], document_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Add document-level metadata to all chunks.
    
    Args:
        chunks: List of chunks with metadata
        document_metadata: Document-level metadata to add
        
    Returns:
        List of chunks with updated metadata
    """
    updated_chunks = []
    
    for chunk in chunks:
        # Create a copy of chunk metadata and update with document metadata
        updated_metadata = {**chunk["metadata"], **document_metadata}
        
        # Create updated chunk
        updated_chunk = {
            "text": chunk["text"],
            "metadata": updated_metadata
        }
        
        updated_chunks.append(updated_chunk)
    
    return updated_chunks

if __name__ == "__main__":
    # Check if a document is provided
    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
            text = data.get("text", "")
            chunk_size = data.get("chunk_size", 1000)
            overlap = data.get("overlap", 200)
            respect_sections = data.get("respect_sections", True)
            document_metadata = data.get("document_metadata", {})
            
            if not text:
                print(json.dumps({"error": "No text provided"}))
                sys.exit(1)
            
            # Chunk the document
            chunks = chunk_document_with_overlap(
                text=text,
                chunk_size=chunk_size,
                overlap=overlap,
                respect_sections=respect_sections
            )
            
            # Add document metadata if provided
            if document_metadata:
                chunks = add_document_metadata(chunks, document_metadata)
            
            # Extract just the text from the chunks for compatibility with existing pipeline
            chunk_texts = [chunk["text"] for chunk in chunks]
            chunk_metadata = [chunk["metadata"] for chunk in chunks]
            
            # Return the chunks and metadata
            result = {
                "chunks": chunk_texts,
                "metadata": chunk_metadata,
                "count": len(chunks)
            }
            
            print(json.dumps(result))
            
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON input"}))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
    else:
        print(json.dumps({"error": "No input provided"}))
