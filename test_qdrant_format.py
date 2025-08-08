#!/usr/bin/env python3
"""
Test script to verify Qdrant bio extraction payload updates
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quadrant_client import get_chunks_for_transcript, update_chunk_with_bio_data
from constants import BIOGRAPHICAL_CATEGORY_KEYS
import json

def test_qdrant_bio_update():
    """Test updating Qdrant chunks with bio extraction data"""
    
    print("=== Testing Qdrant Bio Update ===\n")
    
    # 1. Get a sample transcript
    transcript_name = "Patrank 373 _ Is the Mind Destructive or Beneficial_ _ Pujya Gurudevshri Rakeshji"
    
    print(f"1. Fetching chunks for transcript: {transcript_name}")
    chunks = get_chunks_for_transcript(transcript_name)
    
    if not chunks:
        print("❌ No chunks found. Please ensure you have uploaded transcripts.")
        return False
    
    print(f"✅ Found {len(chunks)} chunks")
    
    # 2. Check current payload structure
    print(f"\n2. Analyzing current payload structure...")
    sample_chunk = chunks[0]
    print(f"Sample chunk ID: {sample_chunk.get('id')}")
    print(f"Payload keys: {list(sample_chunk.keys())}")
    
    # Check if bio data already exists
    has_bio = sample_chunk.get('biographical_extractions')
    print(f"Has bio data: {bool(has_bio)}")
    
    if has_bio:
        bio_categories = [cat for cat, quotes in has_bio.items() if quotes]
        print(f"Categories with data: {bio_categories}")
    
    # 3. Test bio data structure
    print(f"\n3. Testing bio update structure...")
    
    # Create sample bio extraction data
    sample_bio = {
        "biographical_extractions": {
            "early_life_childhood": ["Sample quote about childhood"],
            "education_learning": [],
            "spiritual_journey": ["Sample quote about spiritual path"],
            "health_wellness": [],
            "family_relationships": [],
            "career_work": [],
            "personal_interests": ["Sample interest quote"],
            "philosophical_views": [],
            "experiences_travels": [],
            "challenges_obstacles": []
        }
    }
    
    # Test with first chunk
    test_chunk = chunks[0]
    point_id = test_chunk.get('id')
    
    if not point_id:
        print("❌ Sample chunk missing point ID")
        return False
    
    print(f"Testing update on chunk: {point_id}")
    
    # 4. Perform update
    success = update_chunk_with_bio_data(point_id, sample_bio)
    
    if success:
        print("✅ Qdrant update successful")
        
        # 5. Verify update by fetching chunk again
        print(f"\n4. Verifying update...")
        updated_chunks = get_chunks_for_transcript(transcript_name)
        updated_chunk = next((c for c in updated_chunks if c.get('id') == point_id), None)
        
        if updated_chunk:
            print("✅ Chunk retrieved after update")
            
            # Check bio data
            bio_data = updated_chunk.get('biographical_extractions', {})
            if bio_data:
                print(f"✅ Bio data present in payload")
                categories_with_data = [cat for cat, quotes in bio_data.items() if quotes]
                print(f"Categories with data: {categories_with_data}")
                
                # Check has_{category} flags
                flags_set = []
                for cat in BIOGRAPHICAL_CATEGORY_KEYS:
                    flag_name = f"has_{cat}"
                    if updated_chunk.get(flag_name):
                        flags_set.append(flag_name)
                
                print(f"Boolean flags set: {len(flags_set)}")
                if flags_set:
                    print(f"Sample flags: {flags_set[:3]}")
                
            else:
                print("❌ Bio data not found in updated chunk")
                return False
        else:
            print("❌ Could not retrieve updated chunk")
            return False
    else:
        print("❌ Qdrant update failed")
        return False
    
    print(f"\n=== Qdrant Bio Update Test Complete ===")
    return True

def test_payload_structure():
    """Test the expected payload structure"""
    
    print("\n=== Testing Payload Structure ===\n")
    
    # Expected structure
    expected_keys = [
        "original_text",
        "timestamp", 
        "transcript_name",
        "date",
        "category",
        "location",
        "speaker",
        "satsang_name",
        "satsang_code",
        "misc_tags",
        "summary",
        "tags",
        "global_tags",
        "entities",
        "biographical_extractions"
    ]
    
    # Add has_{category} flags
    for cat in BIOGRAPHICAL_CATEGORY_KEYS:
        expected_keys.append(f"has_{cat}")
    
    print(f"Expected payload keys ({len(expected_keys)}):")
    for key in expected_keys:
        print(f"  - {key}")
    
    # Test with actual chunk
    transcript_name = "Patrank 373 _ Is the Mind Destructive or Beneficial_ _ Pujya Gurudevshri Rakeshji"
    chunks = get_chunks_for_transcript(transcript_name)
    
    if chunks:
        sample_chunk = chunks[0]
        actual_keys = list(sample_chunk.keys())
        
        print(f"\nActual chunk keys ({len(actual_keys)}):")
        for key in sorted(actual_keys):
            print(f"  - {key}")
        
        # Check for missing keys
        missing_keys = [key for key in expected_keys if key not in actual_keys]
        extra_keys = [key for key in actual_keys if key not in expected_keys]
        
        if missing_keys:
            print(f"\n⚠️ Missing keys: {missing_keys}")
        else:
            print(f"\n✅ All expected keys present")
        
        if extra_keys:
            print(f"📝 Extra keys: {extra_keys}")
    
    return True

if __name__ == "__main__":
    test_payload_structure()
    test_qdrant_bio_update()
