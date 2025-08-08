#!/usr/bin/env python3
"""
Simple test for bio extraction payload update
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quadrant_client import get_chunks_for_transcript, update_chunk_with_bio_data
from constants import BIOGRAPHICAL_CATEGORY_KEYS

def simple_bio_update_test():
    """Simple test of bio update functionality"""
    
    print("=== Simple Bio Update Test ===\n")
    
    # Get chunks
    transcript_name = "Patrank 491 _ Antaryatra Arambhiye _ Pujya Gurudevshri Rakeshji"
    chunks = get_chunks_for_transcript(transcript_name)
    
    print(f"Found {len(chunks)} chunks")
    
    if not chunks:
        print("❌ No chunks found")
        return False
    
    # Get first chunk
    chunk = chunks[0]
    point_id = chunk.get('id')
    
    print(f"Testing with chunk ID: {point_id}")
    print(f"Current keys: {list(chunk.keys())}")
    
    # Check current bio data (accounting for nested payload structure)
    if 'payload' in chunk:
        current_bio = chunk['payload'].get('biographical_extractions', {})
        print(f"Bio data is in payload structure")
    else:
        current_bio = chunk.get('biographical_extractions', {})
        print(f"Bio data is at root level")
    
    print(f"Current bio categories with data: {[k for k, v in current_bio.items() if v]}")
    
    # Create test bio data - only include categories with content
    test_bio = {
        "biographical_extractions": {
            "early_life_childhood": ["Test quote about early life and childhood experiences"],
            "spiritual_journey": ["Test quote about spiritual journey and growth"],
            "personal_interests": ["Test quote about hobbies and personal interests"]
        }
    }
    
    print(f"\nUpdating chunk with test bio data...")
    
    # Update
    success = update_chunk_with_bio_data(point_id, test_bio)
    
    if success:
        print("✅ Update successful")
        
        # Verify
        print("Verifying update...")
        updated_chunks = get_chunks_for_transcript(transcript_name)
        updated_chunk = next((c for c in updated_chunks if c.get('id') == point_id), None)
        
        if updated_chunk:
            # Access bio data from payload structure
            if 'payload' in updated_chunk:
                updated_bio = updated_chunk['payload'].get('biographical_extractions', {})
                bio_tags = updated_chunk['payload'].get('bio_tags', [])
            else:
                updated_bio = updated_chunk.get('biographical_extractions', {})
                bio_tags = updated_chunk.get('bio_tags', [])
            
            print(f"✅ Updated bio categories: {list(updated_bio.keys())}")
            print(f"✅ Bio tags array: {bio_tags}")
            
            # Verify no empty arrays exist
            empty_categories = [cat for cat, quotes in updated_bio.items() if not quotes]
            if empty_categories:
                print(f"⚠️ Found empty categories: {empty_categories}")
            else:
                print(f"✅ All categories have content - no empty arrays")
            
            # Verify bio_tags match actual categories
            if set(bio_tags) == set(updated_bio.keys()):
                print(f"✅ Bio tags match actual categories")
            else:
                print(f"⚠️ Bio tags mismatch - Tags: {bio_tags}, Categories: {list(updated_bio.keys())}")
            
            # Show sample bio data
            if updated_bio:
                sample_category = list(updated_bio.keys())[0]
                sample_quotes = updated_bio[sample_category]
                print(f"✅ Sample from {sample_category}: {len(sample_quotes)} quote(s)")
                print(f"    First quote: {sample_quotes[0][:60]}..." if sample_quotes[0] and len(sample_quotes[0]) > 60 else f"    First quote: {sample_quotes[0]}")
            
        else:
            print("❌ Could not find updated chunk")
    else:
        print("❌ Update failed")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    simple_bio_update_test()
