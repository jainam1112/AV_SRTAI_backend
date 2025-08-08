#!/usr/bin/env python3
"""
Comprehensive test for the expanded entity extraction system
Tests the new endpoint and functionality
"""

import requests
import json
import os
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TRANSCRIPT = "test_chunks.srt"  # Make sure this exists in your backend folder

def test_entity_extraction_endpoint():
    """Test the comprehensive entity extraction endpoint"""
    
    print("🧪 Testing Entity Extraction Endpoint...")
    print("=" * 60)
    
    # Test with AI extraction (default)
    print("\n1. Testing AI-based entity extraction:")
    payload_ai = {
        "use_ai": True,
        "include_statistics": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/transcripts/{TEST_TRANSCRIPT}/extract-entities",
            json=payload_ai,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI extraction successful!")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Transcript: {data.get('transcript_name')}")
            print(f"   - Chunks processed: {data.get('chunks_processed')}")
            print(f"   - Chunks updated: {data.get('chunks_updated')}")
            print(f"   - Method used: {data.get('method_used')}")
            
            if data.get('entity_statistics'):
                stats = data['entity_statistics']
                print(f"   - Total entities found: {stats.get('total_entities', 0)}")
                print(f"   - Chunks with entities: {stats.get('chunks_with_entities', 0)}")
                
                entity_counts = stats.get('entity_counts', {})
                print("   - Entity breakdown:")
                for entity_type, count in entity_counts.items():
                    if count > 0:
                        print(f"     * {entity_type}: {count}")
                        
        else:
            print(f"❌ AI extraction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ AI extraction error: {e}")
    
    # Test with rule-based extraction
    print("\n2. Testing rule-based entity extraction:")
    payload_rules = {
        "use_ai": False,
        "include_statistics": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/transcripts/{TEST_TRANSCRIPT}/extract-entities",
            json=payload_rules,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Rule-based extraction successful!")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Method used: {data.get('method_used')}")
            print(f"   - Chunks processed: {data.get('chunks_processed')}")
            print(f"   - Chunks updated: {data.get('chunks_updated')}")
            
            if data.get('entity_statistics'):
                stats = data['entity_statistics']
                print(f"   - Total entities found: {stats.get('total_entities', 0)}")
                print(f"   - Chunks with entities: {stats.get('chunks_with_entities', 0)}")
                
        else:
            print(f"❌ Rule-based extraction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Rule-based extraction error: {e}")
    
    # Test without statistics
    print("\n3. Testing without statistics:")
    payload_no_stats = {
        "use_ai": True,
        "include_statistics": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/transcripts/{TEST_TRANSCRIPT}/extract-entities",
            json=payload_no_stats,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Extraction without statistics successful!")
            print(f"   - Statistics included: {data.get('entity_statistics') is not None}")
            
        else:
            print(f"❌ Extraction without statistics failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Extraction without statistics error: {e}")

def test_search_with_entities():
    """Test if entity data is available in search results"""
    
    print("\n🔍 Testing Search with Entity Data...")
    print("=" * 60)
    
    try:
        # Perform a search
        search_payload = {
            "query": "spiritual practice meditation",
            "top_k": 3
        }
        
        response = requests.post(
            f"{BASE_URL}/search",
            json=search_payload
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            print(f"✅ Search successful! Found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                print(f"\n   Result {i}:")
                print(f"   - Score: {result.get('score', 'N/A')}")
                print(f"   - Transcript: {result.get('transcript_name', 'N/A')}")
                
                payload = result.get('payload', {})
                
                # Check for entity data
                has_entities = False
                entity_types = ['people', 'places', 'concepts', 'scriptures', 'dates', 'organizations', 'events', 'objects']
                
                for entity_type in entity_types:
                    entities = payload.get(entity_type, [])
                    if entities:
                        if not has_entities:
                            print("   - Entities found:")
                            has_entities = True
                        print(f"     * {entity_type}: {entities}")
                
                if not has_entities:
                    print("   - No entity data found in this result")
                    
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Search error: {e}")

def test_error_conditions():
    """Test error handling"""
    
    print("\n⚠️ Testing Error Conditions...")
    print("=" * 60)
    
    # Test with non-existent transcript
    print("\n1. Testing with non-existent transcript:")
    try:
        response = requests.post(
            f"{BASE_URL}/transcripts/nonexistent_file.srt/extract-entities",
            json={"use_ai": False}
        )
        
        if response.status_code == 404:
            print("✅ Correctly returned 404 for non-existent transcript")
        else:
            print(f"❌ Expected 404, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error condition test failed: {e}")

def main():
    """Run comprehensive entity extraction tests"""
    
    print("🚀 Starting Comprehensive Entity Extraction Tests")
    print("=" * 80)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print("✅ Server is running")
    except:
        print("❌ Server is not running. Please start the server first:")
        print("   python main.py")
        return
    
    # Check if test transcript exists
    test_file_path = os.path.join(os.path.dirname(__file__), TEST_TRANSCRIPT)
    if not os.path.exists(test_file_path):
        print(f"⚠️ Test file {TEST_TRANSCRIPT} not found")
        print("   Please upload a transcript first or use an existing one")
        return
    
    # Run tests
    test_entity_extraction_endpoint()
    test_search_with_entities()
    test_error_conditions()
    
    print("\n" + "=" * 80)
    print("🎉 Entity Extraction Tests Complete!")
    print("\nNext steps:")
    print("1. Check the Qdrant database to verify entity data was stored")
    print("2. Test with different types of spiritual content")
    print("3. Compare AI vs rule-based extraction results")

if __name__ == "__main__":
    main()
