#!/usr/bin/env python3
"""
API Testing Script for /upload-transcript endpoint

This script tests the actual API endpoint with real HTTP requests.
Run your FastAPI server first: uvicorn main:app --reload
"""

import requests
import json
import time
from datetime import datetime
import os

# Configuration
BASE_URL = "http://localhost:10000"
UPLOAD_ENDPOINT = f"{BASE_URL}/upload-transcript"

def create_sample_srt_file(filename="test_transcript.srt"):
    """Create a sample SRT file for testing"""
    srt_content = """1
00:00:01,000 --> 00:00:05,000
Welcome to today's satsang. We will discuss the nature of consciousness.

2
00:00:05,000 --> 00:00:10,000
The mind is like a monkey, jumping from thought to thought.

3
00:00:10,000 --> 00:00:15,000
Through meditation, we can learn to observe these thoughts without attachment.

4
00:00:15,000 --> 00:00:20,000
The ultimate goal is to realize our true nature as pure awareness.

5
00:00:20,000 --> 00:00:25,000
Questions and answers will follow this discourse.
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    return filename

def test_health_endpoint():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_basic_upload():
    """Test basic file upload with minimal parameters"""
    print("\n🔍 Testing basic upload...")
    
    # Create sample file
    filename = create_sample_srt_file()
    
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            
            response = requests.post(UPLOAD_ENDPOINT, files=files)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Clean up
        os.remove(filename)
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Basic upload failed: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False

def test_upload_with_metadata():
    """Test upload with all metadata fields"""
    print("\n🔍 Testing upload with metadata...")
    
    filename = create_sample_srt_file("satsang_metadata_test.srt")
    
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            data = {
                'category': 'Satsang',
                'location': 'Bangalore Ashram',
                'speaker': 'Gurudev Sri Sri Ravi Shankar',
                'satsang_name': 'Nature of Consciousness',
                'satsang_code': 'SAT2025001',
                'misc_tags': 'consciousness, meditation, awareness, mind',
                'date': '2025-07-27'
            }
            
            response = requests.post(UPLOAD_ENDPOINT, files=files, data=data)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        os.remove(filename)
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Metadata upload failed: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False

def test_upload_with_custom_date():
    """Test upload with user-provided date"""
    print("\n🔍 Testing upload with custom date...")
    
    filename = create_sample_srt_file("custom_date_test.srt")
    
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            data = {
                'date': '2024-12-25',  # Custom date
                'category': 'Special Discourse',
                'misc_tags': 'christmas, special, celebration'
            }
            
            response = requests.post(UPLOAD_ENDPOINT, files=files, data=data)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        os.remove(filename)
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Custom date upload failed: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False

def test_invalid_file_extension():
    """Test upload with invalid file extension"""
    print("\n🔍 Testing invalid file extension...")
    
    filename = "test.txt"
    with open(filename, 'w') as f:
        f.write("This is not an SRT file")
    
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            
            response = requests.post(UPLOAD_ENDPOINT, files=files)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        os.remove(filename)
        return response.status_code == 400
        
    except Exception as e:
        print(f"❌ Invalid extension test failed: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False

def test_unicode_content():
    """Test upload with Unicode content"""
    print("\n🔍 Testing Unicode content...")
    
    filename = "unicode_test.srt"
    unicode_content = """1
00:00:01,000 --> 00:00:05,000
नमस्ते। आज हम चेतना के स्वरूप पर चर्चा करेंगे।

2
00:00:05,000 --> 00:00:10,000
मन एक बंदर की तरह है, जो विचार से विचार पर कूदता रहता है।

3
00:00:10,000 --> 00:00:15,000
ध्यान के माध्यम से हम इन विचारों को बिना आसक्ति के देख सकते हैं।
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(unicode_content)
    
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            data = {
                'category': 'Hindi Satsang',
                'location': 'Delhi',
                'misc_tags': 'hindi, consciousness, meditation'
            }
            
            response = requests.post(UPLOAD_ENDPOINT, files=files, data=data)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        os.remove(filename)
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Unicode test failed: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False

def test_other_endpoints():
    """Test other available endpoints"""
    print("\n🔍 Testing other endpoints...")
    
    endpoints_to_test = [
        ("/transcripts", "GET", "List transcripts"),
        ("/collections/setup", "GET", "Setup collections")
    ]
    
    results = {}
    
    for endpoint, method, description in endpoints_to_test:
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url)
            
            print(f"  {description}: {response.status_code}")
            results[endpoint] = response.status_code == 200
            
        except Exception as e:
            print(f"  ❌ {description} failed: {e}")
            results[endpoint] = False
    
    return results

def run_performance_test():
    """Run a simple performance test"""
    print("\n🔍 Running performance test...")
    
    filename = create_sample_srt_file("perf_test.srt")
    
    try:
        times = []
        for i in range(3):
            start_time = time.time()
            
            with open(filename, 'rb') as f:
                files = {'file': (filename, f, 'text/plain')}
                data = {'misc_tags': f'performance_test_{i}'}
                response = requests.post(UPLOAD_ENDPOINT, files=files, data=data)
            
            end_time = time.time()
            duration = end_time - start_time
            times.append(duration)
            
            print(f"  Upload {i+1}: {duration:.2f}s - Status: {response.status_code}")
        
        avg_time = sum(times) / len(times)
        print(f"  Average upload time: {avg_time:.2f}s")
        
        os.remove(filename)
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False

def main():
    """Run all API tests"""
    print("🚀 Starting API Tests for /upload-transcript endpoint")
    print("=" * 60)
    
    # Check if server is running
    if not test_health_endpoint():
        print("\n❌ Server is not running or health check failed!")
        print("Please start your FastAPI server with: uvicorn main:app --reload")
        return
    
    print("✅ Server is running!")
    
    # Run all tests
    tests = [
        ("Basic Upload", test_basic_upload),
        ("Upload with Metadata", test_upload_with_metadata),
        ("Upload with Custom Date", test_upload_with_custom_date),
        ("Invalid File Extension", test_invalid_file_extension),
        ("Unicode Content", test_unicode_content),
        ("Performance Test", run_performance_test)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Test other endpoints
    other_results = test_other_endpoints()
    results.update(other_results)
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Your API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
