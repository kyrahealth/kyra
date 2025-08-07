#!/usr/bin/env python3
"""Test script for the categorization service."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.categorization import categorize_question, get_available_categories, get_base_categories

def test_categorization():
    """Test the categorization function with various questions."""
    
    print("Testing categorization service...")
    print(f"Available categories: {get_available_categories()}")
    print(f"Base categories: {get_base_categories()}")
    print()
    
    # Test questions
    test_questions = [
        "What are the symptoms of diabetes?",
        "How is diabetes treated?",
        "How can I prevent diabetes?",
        "What medications are used for high blood pressure?",
        "What causes migraines?",
        "How can I lower my cholesterol naturally?",
        "Tell me a joke",
        "What's the weather like?",
        "What are the symptoms of cancer?",
        "How do I treat a headache?",
        "What causes heart disease?",
        "How can I prevent flu?",
        "What are the side effects of aspirin?",
        "How do I know if I have depression?",
        "What's the best way to lose weight?"
    ]
    
    for question in test_questions:
        try:
            category = categorize_question(question)
            print(f"Q: {question}")
            print(f"A: {category}")
            print()
        except Exception as e:
            print(f"Q: {question}")
            print(f"Error: {e}")
            print()

if __name__ == "__main__":
    test_categorization() 