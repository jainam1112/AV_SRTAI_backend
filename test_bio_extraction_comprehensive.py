#!/usr/bin/env python3
"""
Comprehensive test for bio extraction API with improved error handling
"""

import requests
import json
import time
import sys
import os

# Configuration
BASE_URL = "http://localhost:8000"
TRANSCRIPT_NAME = "Patrank 373 _ Is the Mind Destructive or Beneficial_ _ Pujya Gurudevshri Rakeshji"  # Replace with your actual transcript name

def test_bio_extraction_api():
    """Test the bio extraction API endpoint"""
    
    print("=== Bio Extraction API Test ===\n")
    
    # 1. Test bio extraction status before processing
    print("1. Checking bio extraction status before processing...")
    try:
        response = requests.get(f"{BASE_URL}/transcripts/{TRANSCRIPT_NAME}/bio-status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   ✅ Status check successful")
            print(f"   Total chunks: {status_data['data']['total_chunks']}")
            print(f"   Chunks with bio: {status_data['data']['chunks_with_bio']}")
            print(f"   Coverage: {status_data['data']['bio_coverage_percentage']}%")
            print(f"   Needs extraction: {status_data['data']['needs_extraction']}")
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error during status check: {e}")
        return False
    
    print()
    
    # 2. Test bio extraction with fine-tuned model
    print("2. Starting bio extraction...")
    try:
        extraction_request = {
            "ft_model_id": "ft:gpt-3.5-turbo-0125:srmd:satsang-search-v1:BgoxJBWJ"
        }
        
        print(f"   Using fine-tuned model: {extraction_request['ft_model_id']}")
        
        response = requests.post(
            f"{BASE_URL}/transcripts/{TRANSCRIPT_NAME}/extract-bio",
            json=extraction_request,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Bio extraction successful!")
            print(f"   Status: {result['status']}")
            print(f"   Chunks processed: {result['chunks_processed']}")
            print(f"   Chunks updated: {result['chunks_updated']}")
            print(f"   Model used: {result['model_used']}")
            print(f"   Extraction summary: {result['extraction_summary']}")
            
            # Check success rate
            success_rate = (result['chunks_updated'] / result['chunks_processed']) * 100 if result['chunks_processed'] > 0 else 0
            print(f"   Success rate: {success_rate:.1f}%")
            
        else:
            print(f"   ❌ Bio extraction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⚠️ Bio extraction timed out (this might be normal for large transcripts)")
        print(f"   Check the server logs for progress...")
        return None  # Timeout is not necessarily a failure
        
    except Exception as e:
        print(f"   ❌ Error during bio extraction: {e}")
        return False
    
    print()
    
    # 3. Test bio extraction status after processing
    print("3. Checking bio extraction status after processing...")
    try:
        response = requests.get(f"{BASE_URL}/transcripts/{TRANSCRIPT_NAME}/bio-status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   ✅ Status check successful")
            print(f"   Total chunks: {status_data['data']['total_chunks']}")
            print(f"   Chunks with bio: {status_data['data']['chunks_with_bio']}")
            print(f"   Coverage: {status_data['data']['bio_coverage_percentage']}%")
            print(f"   Category summary: {status_data['data']['category_summary']}")
            print(f"   Needs extraction: {status_data['data']['needs_extraction']}")
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error during status check: {e}")
        return False
    
    print()
    
    # 4. Test retrieving chunks to verify bio data
    print("4. Sampling chunks to verify bio data...")
    try:
        response = requests.get(f"{BASE_URL}/transcripts/{TRANSCRIPT_NAME}/chunks")
        if response.status_code == 200:
            chunks_data = response.json()
            chunks = chunks_data.get('chunks', [])
            print(f"   Retrieved {len(chunks)} chunks")
            
            # Sample a few chunks to check bio data
            chunks_with_bio = 0
            sample_categories = set()
            
            for i, chunk in enumerate(chunks[:10]):  # Check first 10 chunks
                if chunk.get('biographical_extractions'):
                    chunks_with_bio += 1
                    bio_data = chunk['biographical_extractions']
                    for category, quotes in bio_data.items():
                        if quotes:  # Non-empty category
                            sample_categories.add(category)
            
            print(f"   Chunks with bio in sample: {chunks_with_bio}/10")
            print(f"   Categories found in sample: {', '.join(sorted(sample_categories))}")
            
        else:
            print(f"   ❌ Chunk retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during chunk verification: {e}")
        return False
    
    print("\n=== Bio Extraction API Test Complete ===")
    return True

def test_server_connection():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print(f"Make sure the server is running on {BASE_URL}")
        return False

def main():
    print("Bio Extraction API Test\n")
    
    # Check server connection
    if not test_server_connection():
        print("\nPlease start the server with: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    print()
    
    # Run bio extraction test
    result = test_bio_extraction_api()
    
    if result is True:
        print("\n🎉 All tests passed!")
    elif result is False:
        print("\n❌ Some tests failed!")
    else:
        print("\n⚠️ Tests completed with warnings (possible timeout)")

if __name__ == "__main__":
    main()
