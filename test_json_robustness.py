#!/usr/bin/env python3
"""
Test script to verify JSON parsing improvements in bio extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bio_extraction import extract_bio_from_chunks
import json

def test_json_parsing_robustness():
    """Test bio extraction with problematic JSON responses"""
    
    print("=== Testing JSON Parsing Robustness ===\n")
    
    # Test cases that might cause JSON parsing issues
    test_cases = [
        {
            "name": "Long text chunk",
            "chunk": {
                "id": "test1",
                "payload": {
                    "original_text": "Gurudev often spoke about his early life and childhood experiences. He mentioned growing up in a spiritual family where meditation was practiced daily. His education included traditional Sanskrit studies alongside modern academic subjects. The spiritual journey began at a very young age when he started asking profound questions about the nature of existence and reality. His family relationships were deeply rooted in dharmic values and principles of compassion. During his career, he balanced worldly responsibilities with spiritual practices. His personal interests included studying ancient texts and spending time in nature. The philosophical views he developed emphasized the unity of all beings and the importance of inner transformation. His experiences and travels took him to many sacred places where he deepened his understanding. Despite various challenges and obstacles, he maintained unwavering faith in the divine path." * 10  # Make it very long
                }
            }
        },
        {
            "name": "Medium text chunk",
            "chunk": {
                "id": "test2",
                "payload": {
                    "original_text": "In his spiritual journey, Gurudev emphasized the importance of daily practice and constant remembrance of the divine. His health and wellness approach integrated both physical and spiritual aspects."
                }
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. Testing: {test_case['name']}")
        print(f"   Text length: {len(test_case['chunk']['payload']['original_text'])} characters")
        
        try:
            # Test extraction with single chunk
            bio_results = extract_bio_from_chunks(
                chunks=[test_case['chunk']],
                transcript_name=f"test_{i}"
            )
            
            if bio_results and len(bio_results) > 0:
                result = bio_results[0]
                if result and 'biographical_extractions' in result:
                    print(f"   ✅ Bio extraction successful")
                    
                    # Check structure
                    bio_data = result['biographical_extractions']
                    categories_with_data = [k for k, v in bio_data.items() if v]
                    print(f"   Categories with data: {len(categories_with_data)}")
                    
                    # Check flags
                    flags = [k for k, v in result.items() if k.startswith('has_') and v]
                    print(f"   Boolean flags set: {len(flags)}")
                    
                elif result:
                    print(f"   ✅ Fallback bio extraction created")
                    print(f"   Result keys: {list(result.keys())}")
                else:
                    print(f"   ⚠️ Empty result returned")
            else:
                print(f"   ❌ Bio extraction failed")
        
        except Exception as e:
            print(f"   ❌ Error during extraction: {e}")
        
        print()

def test_json_cleanup():
    """Test the JSON cleanup logic directly"""
    
    print("=== Testing JSON Cleanup Logic ===\n")
    
    # Simulate problematic JSON responses
    test_responses = [
        '{"early_life_childhood": ["quote 1", "quote 2"], "education_learning": ["quote 3"',  # Unterminated
        '```json\n{"early_life_childhood": ["quote 1"]}\n```',  # Markdown wrapped
        '  {"early_life_childhood": ["quote 1"]}  ',  # Extra whitespace
        'Some text before {"early_life_childhood": ["quote 1"]} and after',  # Extra text
    ]
    
    for i, test_response in enumerate(test_responses, 1):
        print(f"{i}. Testing malformed JSON:")
        print(f"   Input: {test_response[:50]}...")
        
        # Simulate the cleanup logic from bio_extraction.py
        extracted_json_str = test_response
        
        # Clean up JSON response
        if extracted_json_str.startswith("```json"):
            extracted_json_str = extracted_json_str[7:]
        if extracted_json_str.endswith("```"):
            extracted_json_str = extracted_json_str[:-3]
        extracted_json_str = extracted_json_str.strip()
        
        # Enhanced JSON cleanup for malformed responses
        if not extracted_json_str.startswith('{'):
            # Find the first { character
            start_idx = extracted_json_str.find('{')
            if start_idx != -1:
                extracted_json_str = extracted_json_str[start_idx:]
        
        # Try to fix unterminated strings at the end
        if extracted_json_str.count('"') % 2 != 0:
            # Odd number of quotes - likely unterminated string
            print(f"   Detected unterminated string, attempting fix...")
            last_quote_idx = extracted_json_str.rfind('"')
            if last_quote_idx != -1:
                remaining = extracted_json_str[last_quote_idx+1:].strip()
                if remaining and not remaining.startswith((':', ',', '}', ']')):
                    extracted_json_str = extracted_json_str[:last_quote_idx+1] + '"]}'
        
        # Try parsing
        try:
            parsed_data = json.loads(extracted_json_str)
            print(f"   ✅ Successfully parsed: {len(parsed_data)} keys")
        except json.JSONDecodeError as e:
            print(f"   ⚠️ Still failed: {e}")
            # Try recovery method
            for end_pos in range(len(extracted_json_str), 0, -1):
                test_str = extracted_json_str[:end_pos]
                if not test_str.endswith('}'):
                    test_str += '}'
                try:
                    parsed_data = json.loads(test_str)
                    print(f"   ✅ Recovered by truncating to {end_pos} chars")
                    break
                except json.JSONDecodeError:
                    continue
            else:
                print(f"   ❌ Recovery failed")
        
        print()

if __name__ == "__main__":
    test_json_cleanup()
    test_json_parsing_robustness()
