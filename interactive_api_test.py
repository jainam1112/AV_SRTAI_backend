#!/usr/bin/env python3
"""
Interactive API Test Script for /upload-transcript endpoint

This script provides an interactive menu to test different scenarios.
"""

import requests
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:10000"

def create_sample_srt(content_type="basic"):
    """Create different types of SRT files for testing"""
    
    contents = {
        "basic": """1
00:00:01,000 --> 00:00:05,000
Welcome to today's satsang.

2
00:00:05,000 --> 00:00:10,000
We will explore the nature of consciousness.

3
00:00:10,000 --> 00:00:15,000
Thank you for your attention.
""",
        "long": """1
00:00:01,000 --> 00:00:05,000
Today's discourse will cover the fundamental principles of spiritual awakening.

2
00:00:05,000 --> 00:00:10,000
The mind, in its natural state, is like a calm lake reflecting the sky.

3
00:00:10,000 --> 00:00:15,000
When disturbed by thoughts and emotions, this reflection becomes distorted.

4
00:00:15,000 --> 00:00:20,000
Through the practice of meditation, we can return to this state of clarity.

5
00:00:20,000 --> 00:00:25,000
This is not about suppressing thoughts, but observing them without attachment.
""",
        "unicode": """1
00:00:01,000 --> 00:00:05,000
नमस्ते। आज हम आध्यात्मिक जागृति पर चर्चा करेंगे।

2
00:00:05,000 --> 00:00:10,000
The consciousness is beyond all dualities. चेतना सभी द्वंद्वों से परे है।

3
00:00:10,000 --> 00:00:15,000
🕉️ OM - The primordial sound that connects us all.
"""
    }
    
    filename = f"test_{content_type}.srt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(contents.get(content_type, contents["basic"]))
    
    return filename

def test_basic_upload():
    """Test basic upload functionality"""
    print("\n🔍 Testing Basic Upload...")
    filename = create_sample_srt("basic")
    
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/upload-transcript", files=files)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Uploaded {data.get('chunks_uploaded', 0)} chunks")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        os.remove(filename)

def test_custom_metadata():
    """Test upload with custom metadata"""
    print("\n🔍 Testing Upload with Custom Metadata...")
    
    # Get user input
    print("Enter metadata (press Enter for defaults):")
    category = input("Category [Satsang]: ").strip() or "Satsang"
    location = input("Location [Bangalore]: ").strip() or "Bangalore"
    speaker = input("Speaker [Gurudev]: ").strip() or "Gurudev"
    satsang_name = input("Satsang Name [Test Discourse]: ").strip() or "Test Discourse"
    date = input("Date (YYYY-MM-DD) [today]: ").strip() or datetime.now().strftime('%Y-%m-%d')
    tags = input("Misc Tags (comma-separated) [test,api]: ").strip() or "test,api"
    
    filename = create_sample_srt("long")
    
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            data = {
                'category': category,
                'location': location,
                'speaker': speaker,
                'satsang_name': satsang_name,
                'satsang_code': f"TEST_{datetime.now().strftime('%Y%m%d')}",
                'date': date,
                'misc_tags': tags
            }
            
            response = requests.post(f"{BASE_URL}/upload-transcript", files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Uploaded {result.get('chunks_uploaded', 0)} chunks")
            print(f"Used metadata: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        os.remove(filename)

def test_unicode_content():
    """Test upload with Unicode content"""
    print("\n🔍 Testing Unicode Content Upload...")
    filename = create_sample_srt("unicode")
    
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            data = {
                'category': 'Hindi Satsang',
                'location': 'Delhi',
                'misc_tags': 'hindi,unicode,multilingual'
            }
            response = requests.post(f"{BASE_URL}/upload-transcript", files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Unicode content processed. Uploaded {result.get('chunks_uploaded', 0)} chunks")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        os.remove(filename)

def test_error_cases():
    """Test various error scenarios"""
    print("\n🔍 Testing Error Cases...")
    
    # Test 1: Invalid file extension
    print("1. Testing invalid file extension...")
    filename = "test.txt"
    with open(filename, 'w') as f:
        f.write("Not an SRT file")
    
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/upload-transcript", files=files)
        
        if response.status_code == 400:
            print("✅ Correctly rejected invalid file extension")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        os.remove(filename)
    
    # Test 2: Empty file
    print("2. Testing empty file...")
    filename = "empty.srt"
    with open(filename, 'w') as f:
        f.write("")
    
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/upload-transcript", files=files)
        
        print(f"Empty file response: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        os.remove(filename)

def check_server_status():
    """Check if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy!")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("Make sure your FastAPI server is running:")
        print("uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def show_menu():
    """Display the interactive menu"""
    print("\n" + "="*60)
    print("🚀 Interactive API Test Menu")
    print("="*60)
    print("1. Check Server Status")
    print("2. Test Basic Upload")
    print("3. Test Upload with Custom Metadata")
    print("4. Test Unicode Content Upload")
    print("5. Test Error Cases")
    print("6. Run All Tests")
    print("0. Exit")
    print("="*60)

def run_all_tests():
    """Run all tests in sequence"""
    print("\n🚀 Running All Tests...")
    
    if not check_server_status():
        return
    
    test_basic_upload()
    test_unicode_content()
    test_error_cases()
    
    print("\n✅ All automated tests completed!")

def main():
    """Main interactive loop"""
    print("🚀 Interactive API Tester for /upload-transcript")
    
    while True:
        show_menu()
        choice = input("\nEnter your choice (0-6): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            check_server_status()
        elif choice == "2":
            if check_server_status():
                test_basic_upload()
        elif choice == "3":
            if check_server_status():
                test_custom_metadata()
        elif choice == "4":
            if check_server_status():
                test_unicode_content()
        elif choice == "5":
            if check_server_status():
                test_error_cases()
        elif choice == "6":
            run_all_tests()
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
