#!/usr/bin/env python3
"""Simple test for categorization service."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.categorization import categorize_question

def test_simple():
    """Test categorization with a simple question."""
    
    test_question = "What are the symptoms of diabetes?"
    
    print(f"Testing categorization with: '{test_question}'")
    
    try:
        result = categorize_question(test_question)
        print(f"Result: '{result}'")
        
        if result:
            print("✅ Categorization successful!")
        else:
            print("❌ Categorization returned None")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple() 