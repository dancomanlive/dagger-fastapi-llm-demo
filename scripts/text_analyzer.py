import sys
import json
from collections import Counter
import re

def analyze_text(text):
    """
    Analyze text and return statistics including:
    - Word count
    - Character count
    - Most common words
    - Average word length
    """
    # Clean and normalize text
    cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
    words = cleaned_text.split()
    
    # Count words
    word_count = len(words)
    
    # Count characters (excluding spaces)
    char_count = len(text.replace(" ", ""))
    
    # Find most common words
    word_freq = Counter(words).most_common(5)
    
    # Calculate average word length
    avg_word_length = sum(len(word) for word in words) / max(1, word_count)
    
    return {
        "word_count": word_count,
        "character_count": char_count,
        "most_common_words": dict(word_freq),
        "average_word_length": round(avg_word_length, 2)
    }

if __name__ == "__main__":
    # Check if input is provided as argument
    if len(sys.argv) > 1:
        input_text = sys.argv[1]
        result = analyze_text(input_text)
        print(json.dumps(result))
    elif not sys.stdin.isatty():
        # Read from stdin if available
        input_text = sys.stdin.read()
        result = analyze_text(input_text)
        print(json.dumps(result))
    else:
        print(json.dumps({"error": "No input provided"}))
