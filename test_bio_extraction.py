#!/usr/bin/env python3
"""
Test script for biographical extraction functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bio_extraction import extract_bio_from_chunks, get_biographical_categories, validate_biographical_extraction
import json

def test_bio_extraction():
    """Test the biographical extraction function with sample data"""
    
    print("=== Testing Biographical Extraction ===\n")
    
    # Test 1: Get available categories
    print("1. Available biographical categories:")
    categories = get_biographical_categories()
    for i, category in enumerate(categories, 1):
        print(f"   {i}. {category}")
    print()
    
    # Test 2: Sample chunks for testing
    sample_chunks = [
        {
            "text": "When I was young, I used to meditate for hours in the mountains. This experience shaped my understanding of consciousness.",
            "timestamp": "00:01:00,000 --> 00:01:30,000"
        },
        {
            "text": "My education began in a traditional ashram where I learned Sanskrit and ancient scriptures from my guru.",
            "timestamp": "00:02:00,000 --> 00:02:30,000"
        },
        {
            "text": "The weather is nice today and we should go for a walk.",
            "timestamp": "00:03:00,000 --> 00:03:30,000"
        }
    ]
    
    print("2. Sample chunks for testing:")
    for i, chunk in enumerate(sample_chunks, 1):
        print(f"   Chunk {i}: {chunk['text'][:50]}...")
    print()
    
    # Test 3: Extract biographical information
    print("3. Extracting biographical information...")
    print("   This will use the fine-tuned model from your .env file (FINE_TUNED_BIO_MODEL)")
    print("   If not set, it will fall back to the default ANSWER_EXTRACTION_MODEL")
    print()
    
    try:
        # Extract using model from environment (fine-tuned model if available)
        bio_results = extract_bio_from_chunks(
            chunks=sample_chunks,
            transcript_name="test_transcript"
            # ft_model_id is None, so it will use the environment variable
        )
        
        print("4. Extraction Results:")
        for i, result in enumerate(bio_results, 1):
            print(f"\n   Chunk {i} Results:")
            if result:
                if 'biographical_extractions' in result:
                    bio_data = result['biographical_extractions']
                    if bio_data:
                        print(f"      Found biographical data:")
                        for category, quotes in bio_data.items():
                            if quotes:  # Only show categories with content
                                print(f"        {category}: {quotes}")
                    else:
                        print(f"      No biographical information found")
                
                # Show category flags
                flags = [k for k, v in result.items() if k.startswith('has_') and v]
                if flags:
                    print(f"      Categories detected: {', '.join(f.replace('has_', '') for f in flags)}")
            else:
                print(f"      No extraction performed (error or empty)")
    
    except Exception as e:
        print(f"   Error during extraction: {e}")
        print("   This might be due to:")
        print("   - Missing OpenAI API key")
        print("   - Network connectivity issues") 
        print("   - API rate limits")
        return
    
    print("\n5. Testing validation function:")
    for i, result in enumerate(bio_results, 1):
        is_valid = validate_biographical_extraction(result)
        print(f"   Chunk {i} validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    print("\n=== Test Complete ===")
    print("\nConfiguration:")
    print("   1. Set FINE_TUNED_BIO_MODEL in your .env file to use your fine-tuned model")
    print("   2. Or pass ft_model_id explicitly:")
    print("      bio_results = extract_bio_from_chunks(chunks, 'transcript_name', 'ft:gpt-3.5-turbo:your-org:your-model:id')")
    print("\nFine-tuned model format: ft:gpt-3.5-turbo:organization:name:id")

def test_validation():
    """Test the validation function with sample data"""
    print("\n=== Testing Validation Function ===\n")
    
    # Valid extraction
    valid_bio = {
        'biographical_extractions': {
            'early_life_childhood': ['quote about childhood'],
            'education_learning': [],
            'spiritual_journey': ['quote about spirituality']
        },
        'has_early_life_childhood': True,
        'has_education_learning': False,
        'has_spiritual_journey': True
    }
    
    # Invalid extraction (wrong structure)
    invalid_bio = {
        'biographical_extractions': "not a dict",
        'has_early_life_childhood': True
    }
    
    print("Testing valid biographical extraction:")
    print(f"   Result: {'✓ Valid' if validate_biographical_extraction(valid_bio) else '✗ Invalid'}")
    
    print("Testing invalid biographical extraction:")
    print(f"   Result: {'✓ Valid' if validate_biographical_extraction(invalid_bio) else '✗ Invalid'}")

if __name__ == "__main__":
    test_bio_extraction()
    test_validation()
