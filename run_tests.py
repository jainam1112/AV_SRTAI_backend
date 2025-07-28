#!/usr/bin/env python3
"""
Test runner script for the upload-transcript endpoint.
Run this script to execute all tests for the upload functionality.
"""

import subprocess
import sys
import os

def run_tests():
    """Run all upload-transcript tests"""
    print("🧪 Running Upload-Transcript Unit Tests")
    print("=" * 50)
    
    # Ensure we're in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Install dependencies if needed
    print("📦 Installing test dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    # Run the main test suite
    print("\n🔍 Running main test suite...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_upload_transcript.py",
            "-v",
            "--tb=short",
            "--disable-warnings"
        ], check=True)
        print("✅ Main tests passed!")
    except subprocess.CalledProcessError:
        print("❌ Main tests failed!")
        return False
    
    # Run edge case tests
    print("\n🔍 Running edge case tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_upload_transcript_edge_cases.py",
            "-v",
            "--tb=short",
            "--disable-warnings"
        ], check=True)
        print("✅ Edge case tests passed!")
    except subprocess.CalledProcessError:
        print("❌ Edge case tests failed!")
        return False
    
    # Run all tests with coverage if pytest-cov is available
    print("\n📊 Running tests with coverage...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_upload_transcript*.py",
            "--cov=main",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "-v"
        ], check=False)  # Don't fail if coverage not available
        if result.returncode == 0:
            print("✅ Coverage report generated in htmlcov/")
    except FileNotFoundError:
        print("⚠️  pytest-cov not available, skipping coverage report")
    
    print("\n🎉 All tests completed successfully!")
    print("\nTest Summary:")
    print("- ✅ Main functionality tests")
    print("- ✅ Edge case tests")
    print("- ✅ Error handling tests")
    print("- ✅ Integration tests")
    
    return True

def run_specific_test(test_name):
    """Run a specific test"""
    print(f"🧪 Running specific test: {test_name}")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"-k", test_name,
            "-v",
            "--tb=short"
        ], check=True)
        print(f"✅ Test {test_name} passed!")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Test {test_name} failed!")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)
