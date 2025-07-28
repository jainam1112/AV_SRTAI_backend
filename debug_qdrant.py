#!/usr/bin/env python3

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

QDRANT_HOST = os.getenv('QDRANT_HOST')
QDRANT_PORT = os.getenv('QDRANT_PORT', '6333')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', '').strip('"')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')

print("=== Qdrant Configuration Debug ===")
print(f"Host: {QDRANT_HOST}")
print(f"Port: {QDRANT_PORT}")
print(f"API Key (first 20 chars): {QDRANT_API_KEY[:20]}...")
print(f"Collection: {COLLECTION_NAME}")
print()

# Test 1: List collections
print("=== Test 1: List Collections ===")
headers = {
    'Authorization': f'Bearer {QDRANT_API_KEY}',
    'Content-Type': 'application/json'
}

collections_url = f'https://{QDRANT_HOST}:{QDRANT_PORT}/collections'
print(f"URL: {collections_url}")

try:
    response = requests.get(collections_url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        collections_data = response.json()
        print("✅ Authentication successful!")
        collections = collections_data.get('result', {}).get('collections', [])
        print(f"Available collections: {[c['name'] for c in collections]}")
        
        # Check if our collection exists
        collection_exists = any(c['name'] == COLLECTION_NAME for c in collections)
        print(f"Collection '{COLLECTION_NAME}' exists: {collection_exists}")
        
    elif response.status_code == 403:
        print("❌ 403 Forbidden - API key is invalid or lacks permissions")
        print("Response:", response.text)
    elif response.status_code == 401:
        print("❌ 401 Unauthorized - API key format is incorrect")
        print("Response:", response.text)
    else:
        print(f"❌ Unexpected status code: {response.status_code}")
        print("Response:", response.text)
        
except requests.exceptions.Timeout:
    print("❌ Request timed out - check network connection")
except requests.exceptions.ConnectionError:
    print("❌ Connection error - check host and port")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: Check specific collection
print("=== Test 2: Check Collection Info ===")
collection_info_url = f'https://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}'
print(f"URL: {collection_info_url}")

try:
    response = requests.get(collection_info_url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Collection accessible!")
        collection_info = response.json()
        result = collection_info.get('result', {})
        print(f"Collection status: {result.get('status', 'unknown')}")
        print(f"Vector size: {result.get('config', {}).get('params', {}).get('vectors', {}).get('size', 'unknown')}")
        print(f"Points count: {result.get('points_count', 'unknown')}")
    elif response.status_code == 404:
        print("❌ Collection not found - needs to be created")
    elif response.status_code == 403:
        print("❌ 403 Forbidden - no access to this collection")
    else:
        print(f"❌ Status: {response.status_code}")
        print("Response:", response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 3: Test the exact endpoint that's failing
print("=== Test 3: Test Points Endpoint (The Failing One) ===")
points_url = f'https://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points'
print(f"URL: {points_url}")

# Test with GET first (safer)
try:
    response = requests.get(points_url, headers=headers, timeout=10)
    print(f"GET Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Points endpoint accessible!")
    elif response.status_code == 403:
        print("❌ 403 Forbidden - no write access to points")
        print("This suggests the API key has read-only permissions")
    elif response.status_code == 404:
        print("❌ Collection not found")
    else:
        print(f"❌ Status: {response.status_code}")
        print("Response:", response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n=== Recommendations ===")
print("1. If you get 403 Forbidden:")
print("   - Check if your API key has write permissions")
print("   - Regenerate your API key in Qdrant Cloud dashboard")
print("   - Ensure the collection exists and you have access")
print()
print("2. If the collection doesn't exist:")
print("   - Create it manually in Qdrant Cloud dashboard")
print("   - Or implement collection creation in setup_collection()")
print()
print("3. If you get authentication errors:")
print("   - Double-check your API key in Qdrant Cloud")
print("   - Make sure there are no extra spaces or quotes")
