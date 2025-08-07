"""Question categorization service using LLM to classify questions into consistent categories."""
import os
from typing import List, Optional
import openai
from dotenv import load_dotenv

load_dotenv(override=True)

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define consistent categories for all questions
ALL_CATEGORIES = [
    "Symptoms & Diagnosis",
    "Treatment & Medication", 
    "Prevention & Lifestyle",
    "General"
]

# Base categories for validation (without disease/condition)
BASE_CATEGORIES = [
    "Symptoms & Diagnosis",
    "Treatment & Medication", 
    "Prevention & Lifestyle",
    "General"
]

CATEGORIZATION_PROMPT = """
You are a medical question categorizer. For each question, determine if it's medical/health-related or general conversation.

For MEDICAL questions, return:
- The main category (choose one: Symptoms & Diagnosis, Treatment & Medication, Prevention & Lifestyle)
- If the question is about a specific disease or condition, add it after a comma (e.g. Symptoms & Diagnosis, Diabetes)
- If not about a specific disease/condition, just return the category

For NON-MEDICAL questions, return: General

Available categories:
1. Symptoms & Diagnosis
2. Treatment & Medication
3. Prevention & Lifestyle
4. General

Rules:
- Medical questions include: diseases, conditions, symptoms, treatments, medications, health, medical procedures, etc.
- "What is [disease/condition]?" questions are MEDICAL and should be categorized as "Symptoms & Diagnosis"
- Always return the category first
- If a disease/condition is mentioned, add it after a comma
- If not, just return the category
- Be consistent across similar questions
- Return ONLY the category (and disease/condition if present), nothing else

Examples:
"What is diabetes?" → "Symptoms & Diagnosis, Diabetes"
"What are the symptoms of diabetes?" → "Symptoms & Diagnosis, Diabetes"
"How is diabetes treated?" → "Treatment & Medication, Diabetes"
"How can I prevent diabetes?" → "Prevention & Lifestyle, Diabetes"
"What medications are used for high blood pressure?" → "Treatment & Medication, High Blood Pressure"
"What causes migraines?" → "Symptoms & Diagnosis, Migraines"
"How can I lower my cholesterol naturally?" → "Prevention & Lifestyle, Cholesterol"
"Tell me a joke" → "General"
"What's the weather like?" → "General"
"What is leptospirosis?" → "Symptoms & Diagnosis, Leptospirosis"

Question: "{question}"
Category:"""

def categorize_question(question: str) -> Optional[str]:
    """
    Categorize a question into one of the predefined categories.
    
    Args:
        question: The question to categorize
        
    Returns:
        Category name (with disease/condition if applicable) or None if categorization fails
    """
    print(f"[DEBUG] Starting categorization for question: '{question}'")
    
    try:
        print(f"[DEBUG] Calling OpenAI API...")
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Use mini for cost efficiency
            messages=[
                {"role": "user", "content": CATEGORIZATION_PROMPT.format(question=question)}
            ],
            max_tokens=50,  # Increased to accommodate disease/condition names
            temperature=0.1  # Low temperature for consistent categorization
        )
        
        category = response.choices[0].message.content.strip()
        print(f"[DEBUG] Raw OpenAI response: '{category}'")
        
        # Validate that the response starts with one of our expected base categories
        for base_category in BASE_CATEGORIES:
            if category.startswith(base_category):
                print(f"[DEBUG] Question categorized as: '{category}' for question: '{question}'")
                return category
        
        # If no base category matches, check if it's just a base category
        if category in BASE_CATEGORIES:
            print(f"[DEBUG] Question categorized as: '{category}' for question: '{question}'")
            return category
        
        print(f"[DEBUG] Unexpected category response: '{category}' for question: '{question}'")
        # Default to General if response is unexpected
        return "General"
            
    except Exception as e:
        print(f"[DEBUG] Categorization error for question '{question}': {e}")
        return None

def get_available_categories() -> List[str]:
    """Get the list of available categories for reference."""
    return ALL_CATEGORIES.copy()

def get_base_categories() -> List[str]:
    """Get the list of base categories (without disease/condition) for validation."""
    return BASE_CATEGORIES.copy() 