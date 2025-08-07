#!/usr/bin/env python3
"""
Verify bio extraction integration works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quadrant_client import get_chunks_for_transcript

def verify_bio_integration():
    """Verify bio extraction integration"""
    
    print("=== Verify Bio Integration ===\n")
    
    transcript_name = "Patrank 491 _ Antaryatra Arambhiye _ Pujya Gurudevshri Rakeshji"
    chunks = get_chunks_for_transcript(transcript_name)
    
    if not chunks:
        print("❌ No chunks found")
        return
    
    print(f"Found {len(chunks)} chunks")
    
    # Check first chunk that should have bio data
    chunk = chunks[0]
    payload = chunk.get('payload', {})
    
    print(f"\nChunk ID: {chunk.get('id')}")
    print(f"Payload keys: {list(payload.keys())}")
    
    # Check bio data
    bio_data = payload.get('biographical_extractions', {})
    if bio_data:
        print(f"\n✅ Bio data found!")
        print(f"Bio categories with content: {list(bio_data.keys())}")
        
        # Verify no empty arrays exist
        empty_categories = [cat for cat, quotes in bio_data.items() if not quotes]
        if empty_categories:
            print(f"⚠️ Found empty categories (should be cleaned): {empty_categories}")
        else:
            print(f"✅ All bio categories have content - no empty arrays")
        
        # Show sample quotes
        for category in list(bio_data.keys())[:2]:  # Show first 2 categories
            quotes = bio_data[category]
            print(f"  {category}: {len(quotes)} quote(s)")
            for quote in quotes[:1]:  # Show first quote
                print(f"    • {quote[:80]}..." if len(quote) > 80 else f"    • {quote}")
    else:
        print(f"❌ No bio data found")
    
    # Check bio tags array
    bio_tags = payload.get('bio_tags', [])
    print(f"\nBio tags array: {bio_tags}")
    print(f"Number of bio tags: {len(bio_tags)}")
    
    # Verify bio_tags match categories with data
    if bio_data:
        actual_categories_with_data = [k for k, v in bio_data.items() if v]
        tags_match = set(bio_tags) == set(actual_categories_with_data)
        print(f"Bio tags match categories with data: {'✅' if tags_match else '❌'}")
        if not tags_match:
            print(f"  Expected: {actual_categories_with_data}")
            print(f"  Actual: {bio_tags}")
    
    # Check if old boolean flags still exist (should be removed)
    old_flag_keys = [k for k in payload.keys() if k.startswith('has_')]
    if old_flag_keys:
        print(f"\n⚠️ Old boolean flags still present: {len(old_flag_keys)} fields")
        print(f"Sample old flags: {old_flag_keys[:5]}")
    else:
        print(f"\n✅ No old boolean flags found - clean payload structure")
    
    # Verify other payload fields are preserved
    essential_fields = ['transcript_name', 'original_text', 'timestamp']
    print(f"\nEssential fields preserved:")
    for field in essential_fields:
        if field in payload:
            value = payload[field]
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + '...'
            print(f"  ✅ {field}: {value}")
        else:
            print(f"  ❌ {field}: MISSING")
    
    print(f"\n=== Verification Complete ===")

if __name__ == "__main__":
    verify_bio_integration()
