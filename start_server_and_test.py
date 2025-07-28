#!/usr/bin/env python3
"""
Server Starter Script

This script starts the FastAPI server and runs a quick test.
"""

import subprocess
import time
import requests
import os
import sys

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    
    try:
        # Start the server in the background
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("⏳ Waiting for server to start...")
        time.sleep(5)  # Wait for server to start
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:10000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is running successfully!")
                print("🌐 Server URL: http://localhost:10000")
                print("📖 API Docs: http://localhost:10000/docs")
                return process
            else:
                print("❌ Server started but health check failed")
                return None
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server")
            return None
            
    except FileNotFoundError:
        print("❌ uvicorn not found. Install it with: pip install uvicorn")
        return None
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def run_quick_test():
    """Run a quick test to verify the API is working"""
    print("\n🔍 Running quick API test...")
    
    # Create a simple SRT file
    srt_content = """1
00:00:01,000 --> 00:00:05,000
Testing the API with a simple upload.

2
00:00:05,000 --> 00:00:10,000
This is a test satsang transcript.
"""
    
    filename = "quick_test.srt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            data = {
                'category': 'Test',
                'date': '2025-07-27',
                'misc_tags': 'test,api,quick'
            }
            response = requests.post("http://localhost:10000/upload-transcript", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Quick test successful! Uploaded {result.get('chunks_uploaded', 0)} chunks")
            return True
        else:
            print(f"❌ Quick test failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Quick test error: {e}")
        return False
    finally:
        if os.path.exists(filename):
            os.remove(filename)

def main():
    """Main function"""
    print("🚀 FastAPI Server Starter & Tester")
    print("=" * 50)
    
    # Check if server is already running
    try:
        response = requests.get("http://localhost:10000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is already running!")
            if run_quick_test():
                print("\n🎉 Your API is working perfectly!")
            return
    except:
        pass
    
    # Start the server
    process = start_server()
    
    if process:
        try:
            # Run quick test
            if run_quick_test():
                print("\n🎉 Server started and API is working!")
                print("\nYou can now:")
                print("1. Run the test scripts: python test_api.py")
                print("2. Visit the API docs: http://localhost:10000/docs")
                print("3. Test with curl or other tools")
                print("\nPress Ctrl+C to stop the server...")
                
                # Keep the server running
                process.wait()
            else:
                print("\n⚠️ Server started but API test failed")
                print("Check your logs and configuration")
                
        except KeyboardInterrupt:
            print("\n\n👋 Stopping server...")
            process.terminate()
            process.wait()
            print("✅ Server stopped")
    else:
        print("\n❌ Failed to start server")
        print("Make sure you have all dependencies installed:")
        print("pip install fastapi uvicorn python-multipart")

if __name__ == "__main__":
    main()
