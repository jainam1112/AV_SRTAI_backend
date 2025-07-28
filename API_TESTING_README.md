# API Testing Guide

This directory contains several Python scripts to test your `/upload-transcript` API endpoint with real HTTP requests.

## 📁 Test Files Overview

### 1. `simple_api_test.py` - Quick Start Test
**Best for:** Quick verification that your API is working

```bash
python simple_api_test.py
```

**What it tests:**
- Basic SRT file upload
- Upload with custom date parameter
- Basic error handling

### 2. `test_api.py` - Comprehensive Test Suite
**Best for:** Thorough testing of all functionality

```bash
python test_api.py
```

**What it tests:**
- Basic upload functionality
- Upload with all metadata fields
- Custom date handling
- Invalid file extension handling
- Unicode content processing
- Performance testing (3 uploads with timing)
- Other endpoints (/health, /transcripts, etc.)

### 3. `interactive_api_test.py` - Interactive Testing
**Best for:** Manual testing with custom inputs

```bash
python interactive_api_test.py
```

**Features:**
- Interactive menu system
- Custom metadata input
- Real-time server status checking
- Error scenario testing
- Step-by-step testing process

## 🚀 How to Use

### Step 1: Start Your FastAPI Server
```bash
uvicorn main:app --reload
```

### Step 2: Choose a Test Script

#### For Quick Testing:
```bash
python simple_api_test.py
```

#### For Complete Testing:
```bash
python test_api.py
```

#### For Interactive Testing:
```bash
python interactive_api_test.py
```

## 📋 Test Scenarios Covered

### ✅ Basic Functionality
- SRT file upload and processing
- Date parameter (user-provided vs default)
- Metadata handling (category, location, speaker, etc.)
- Response format validation

### ✅ Edge Cases
- Unicode and special characters
- Large tag lists
- Empty metadata fields
- Invalid file extensions
- Empty files

### ✅ Error Handling
- Server connectivity
- Invalid file types
- Malformed requests
- Server errors

## 📊 Expected Results

### Successful Upload Response:
```json
{
  "status": "success",
  "chunks_uploaded": 3
}
```

### Error Response:
```json
{
  "detail": "Only .srt files are supported."
}
```

## 🛠️ Customization

### Testing with Your Own SRT Files
Modify any test script to use your own files:

```python
# In any test script, replace the sample content with:
filename = "your_actual_file.srt"
with open(filename, 'rb') as f:
    files = {'file': (filename, f, 'text/plain')}
    # ... rest of the test
```

### Testing Different Metadata
Use the interactive script or modify the metadata in any test:

```python
data = {
    'category': 'Your Category',
    'location': 'Your Location',
    'speaker': 'Your Speaker',
    'satsang_name': 'Your Satsang Name',
    'satsang_code': 'YOUR_CODE',
    'date': '2025-07-27',
    'misc_tags': 'tag1,tag2,tag3'
}
```

## 🔧 Troubleshooting

### "Cannot connect to server" Error
- Make sure your FastAPI server is running: `uvicorn main:app --reload`
- Check if the server is running on `http://localhost:10000`
- Verify the server is not blocked by firewall

### "Invalid file extension" Error
- Ensure your test files have `.srt` extension
- Check that the file contains valid SRT format

### Environment Issues
Make sure you have the required packages:
```bash
pip install requests
```

## 📈 Performance Testing

The `test_api.py` script includes basic performance testing:
- Uploads the same file 3 times
- Measures response time for each upload
- Calculates average response time

For more detailed performance testing, consider using tools like:
- Apache Bench (ab)
- Locust
- pytest-benchmark

## 🔍 Debugging Tips

1. **Check server logs** while running tests
2. **Use verbose output** in your FastAPI app
3. **Monitor database/Qdrant connections**
4. **Check environment variables** are properly set

## 📝 Adding More Tests

To add your own test scenarios:

```python
def test_your_scenario():
    """Test your specific scenario"""
    # Create test data
    filename = create_sample_srt("your_type")
    
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            data = {'your': 'parameters'}
            
            response = requests.post(UPLOAD_ENDPOINT, files=files, data=data)
            
        # Assert your expectations
        assert response.status_code == 200
        # More assertions...
        
    finally:
        os.remove(filename)
```

Happy testing! 🎉
