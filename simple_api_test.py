#!/usr/bin/env python3
"""
Simple API Test for /upload-transcript endpoint

Quick test script to verify your API is working.
Usage: python simple_api_test.py
"""

import requests
import os

def test_upload():
    """Test the upload endpoint with a simple SRT file"""
    
    # Create a simple SRT file
    srt_content = """1
00:00:01,000 --> 00:00:05,000
Welcome to today's satsang.

2
00:00:05,000 --> 00:00:10,000
We will discuss consciousness and awareness.

3
00:00:10,000 --> 00:00:15,000
Thank you for joining us today.
"""
    
    filename = "simple_test.srt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    try:
        # Test 1: Basic upload
        print("🔍 Testing basic upload...")
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            response = requests.post("http://localhost:10000/upload-transcript", files=files)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Basic upload successful!")
            print(f"Response: {response.json()}")
        else:
            print("❌ Basic upload failed!")
            print(f"Error: {response.text}")
        
        # Test 2: Upload with custom date
        print("\n🔍 Testing upload with custom date...")
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            data = {
                'date': '2025-12-25',
                'category': 'Test Satsang',
                'speaker': 'Test Speaker',
                'misc_tags': 'test, api, custom_date'
            }
            response = requests.post("http://localhost:10000/upload-transcript", files=files, data=data)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Custom date upload successful!")
            print(f"Response: {response.json()}")
        else:
            print("❌ Custom date upload failed!")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("Make sure your FastAPI server is running:")
        print("uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    print("🚀 Simple API Test for /upload-transcript")
    print("=" * 50)
    test_upload()
