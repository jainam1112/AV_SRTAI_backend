#!/usr/bin/env python3
"""
Test script for biographical extraction API endpoint
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"  # Adjust port if different

def test_bio_extraction_endpoints():
    """Test the biographical extraction endpoints"""
    
    print("=== Testing Biographical Extraction API ===\n")
    
    # Test 1: Check server health
    print("1. Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("   ✓ Server is running")
        else:
            print(f"   ✗ Server health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ✗ Cannot connect to server. Is it running?")
        print("   Start the server with: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # Test 2: List available transcripts
    print("\n2. Listing available transcripts...")
    try:
        response = requests.get(f"{BASE_URL}/transcripts")
        if response.status_code == 200:
            data = response.json()
            transcripts = data.get("data", {}).get("transcripts", [])
            print(f"   ✓ Found {len(transcripts)} transcripts:")
            for i, transcript in enumerate(transcripts, 1):
                print(f"      {i}. {transcript}")
            
            if not transcripts:
                print("   ⚠️  No transcripts found. Upload a transcript first.")
                return
                
        else:
            print(f"   ✗ Failed to list transcripts: {response.status_code}")
            return
    except Exception as e:
        print(f"   ✗ Error listing transcripts: {e}")
        return
    
    # Test 3: Check bio extraction status for first transcript
    if transcripts:
        test_transcript = transcripts[0]
        print(f"\n3. Checking bio extraction status for '{test_transcript}'...")
        
        try:
            response = requests.get(f"{BASE_URL}/transcripts/{test_transcript}/bio-status")
            if response.status_code == 200:
                data = response.json()
                bio_status = data.get("data", {})
                print(f"   ✓ Bio status retrieved:")
                print(f"      Total chunks: {bio_status.get('total_chunks', 0)}")
                print(f"      Chunks with bio: {bio_status.get('chunks_with_bio', 0)}")
                print(f"      Coverage: {bio_status.get('bio_coverage_percentage', 0)}%")
                print(f"      Needs extraction: {bio_status.get('needs_extraction', True)}")
                
                category_summary = bio_status.get('category_summary', {})
                if category_summary:
                    print(f"      Categories found: {list(category_summary.keys())}")
                
            else:
                print(f"   ✗ Failed to get bio status: {response.status_code}")
                print(f"      Response: {response.text}")
        except Exception as e:
            print(f"   ✗ Error checking bio status: {e}")
    
    # Test 4: Extract biographical information
    if transcripts:
        print(f"\n4. Testing bio extraction for '{test_transcript}'...")
        print("   This may take a while depending on the number of chunks...")
        
        # Prepare request data
        request_data = {
            "transcript_name": test_transcript
            # ft_model_id is optional and will use environment variable
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/transcripts/{test_transcript}/extract-bio",
                json=request_data,
                timeout=300  # 5 minute timeout for extraction
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Bio extraction completed!")
                print(f"      Chunks processed: {data.get('chunks_processed', 0)}")
                print(f"      Chunks updated: {data.get('chunks_updated', 0)}")
                print(f"      Model used: {data.get('model_used', 'unknown')}")
                
                extraction_summary = data.get('extraction_summary', {})
                if extraction_summary:
                    print(f"      Categories extracted:")
                    for category, count in extraction_summary.items():
                        print(f"        - {category}: {count} chunks")
                else:
                    print(f"      No biographical information found")
                    
            elif response.status_code == 404:
                print(f"   ✗ Transcript not found: {response.text}")
            else:
                print(f"   ✗ Bio extraction failed: {response.status_code}")
                print(f"      Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("   ✗ Bio extraction timed out (took longer than 5 minutes)")
        except Exception as e:
            print(f"   ✗ Error during bio extraction: {e}")
    
    # Test 5: Check bio status after extraction
    if transcripts:
        print(f"\n5. Checking bio status after extraction...")
        
        try:
            response = requests.get(f"{BASE_URL}/transcripts/{test_transcript}/bio-status")
            if response.status_code == 200:
                data = response.json()
                bio_status = data.get("data", {})
                print(f"   ✓ Updated bio status:")
                print(f"      Total chunks: {bio_status.get('total_chunks', 0)}")
                print(f"      Chunks with bio: {bio_status.get('chunks_with_bio', 0)}")
                print(f"      Coverage: {bio_status.get('bio_coverage_percentage', 0)}%")
                print(f"      Needs extraction: {bio_status.get('needs_extraction', True)}")
        except Exception as e:
            print(f"   ✗ Error checking updated bio status: {e}")
    
    print("\n=== Bio Extraction API Test Complete ===")
    print("\nAPI Endpoints Available:")
    print(f"  GET  {BASE_URL}/transcripts - List all transcripts")
    print(f"  GET  {BASE_URL}/transcripts/{{name}}/bio-status - Check bio extraction status")
    print(f"  POST {BASE_URL}/transcripts/{{name}}/extract-bio - Extract biographical info")

def test_with_custom_model():
    """Test bio extraction with a custom fine-tuned model"""
    print("\n=== Testing with Custom Model ===\n")
    
    model_id = input("Enter your fine-tuned model ID (or press Enter to skip): ").strip()
    if not model_id:
        print("Skipped custom model test.")
        return
    
    transcript_name = input("Enter transcript name to test: ").strip()
    if not transcript_name:
        print("No transcript name provided.")
        return
    
    request_data = {
        "transcript_name": transcript_name,
        "ft_model_id": model_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/transcripts/{transcript_name}/extract-bio",
            json=request_data,
            timeout=300
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Custom model extraction completed!")
            print(f"  Model used: {data.get('model_used', 'unknown')}")
            print(f"  Chunks processed: {data.get('chunks_processed', 0)}")
            print(f"  Chunks updated: {data.get('chunks_updated', 0)}")
        else:
            print(f"✗ Custom model extraction failed: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error with custom model: {e}")

if __name__ == "__main__":
    test_bio_extraction_endpoints()
    
    print("\n" + "="*50 + "\n")
    
    custom_test = input("Would you like to test with a custom fine-tuned model? (y/N): ").strip().lower()
    if custom_test == 'y':
        test_with_custom_model()
