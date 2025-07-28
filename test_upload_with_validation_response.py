#!/usr/bin/env python3
"""
Test script to demonstrate validation in API responses
"""

import requests
import json
import tempfile
import os

def test_upload_with_validation_response():
    """Test upload endpoint and show validation in response"""
    
    print("🧪 TESTING UPLOAD WITH VALIDATION RESPONSE")
    print("="*50)
    
    # Create a test SRT file
    test_srt_content = """1
00:00:01,000 --> 00:00:10,000
Welcome to today's satsang. Today we will explore the nature of consciousness.

2
00:00:10,000 --> 00:00:20,000
Consciousness is the fundamental reality that underlies all experience.

3
00:00:20,000 --> 00:00:30,000
When we meditate, we begin to recognize this pure awareness within ourselves.

4
00:00:30,000 --> 00:00:40,000
This understanding brings us closer to our authentic self and inner peace.
"""
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        f.write(test_srt_content)
        temp_srt_path = f.name
    
    print(f"📄 Created test SRT file: {temp_srt_path}")
    
    # Test different validation modes
    validation_modes = ["warn", "detailed", "strict"]
    base_url = "http://localhost:10000"
    
    for mode in validation_modes:
        print(f"\n🔧 Testing validation mode: {mode}")
        print("-" * 30)
        
        # Set environment variable for this test
        os.environ["VALIDATION_MODE"] = mode
        
        try:
            # Prepare the upload request
            with open(temp_srt_path, 'rb') as srt_file:
                files = {'file': ('test_transcript.srt', srt_file, 'text/plain')}
                data = {
                    'category': 'Satsang',
                    'location': 'Test Location',
                    'speaker': 'Test Speaker',
                    'date': '2025-07-27'
                }
                
                # Make the request
                response = requests.post(f"{base_url}/upload-transcript", files=files, data=data)
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload Successful!")
                print(f"📦 Chunks Uploaded: {result['chunks_uploaded']}")
                
                if 'validation' in result and result['validation']:
                    validation = result['validation']
                    print(f"\n📋 Validation Results:")
                    print(f"   ✓ Coverage Complete: {validation['coverage_complete']}")
                    print(f"   📝 Text Coverage: {validation['text_coverage_percentage']:.1f}%")
                    print(f"   ⏱️ Timeline Coverage: {validation['timeline_coverage_percentage']:.1f}%")
                    print(f"   🚫 Missing Subtitles: {validation['missing_subtitles_count']}")
                    print(f"   ⏳ Timeline Gaps: {validation['timeline_gaps_count']}")
                    print(f"   🔄 Overlapping Chunks: {validation['overlapping_chunks_count']}")
                    
                    if validation['errors']:
                        print(f"   ❌ Errors: {validation['errors']}")
                    
                    if validation['warnings']:
                        print(f"   ⚠️ Warnings: {validation['warnings']}")
                    
                    if validation.get('detailed_report'):
                        print(f"\n📄 Detailed Report:\n{validation['detailed_report']}")
                else:
                    print("ℹ️ No validation information in response (passed validation)")
                
            elif response.status_code == 422:
                error = response.json()
                print("❌ Upload Failed - Validation Error!")
                print(f"   Error: {error['detail']}")
                
            else:
                print(f"❌ Upload Failed - HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error - Is the server running?")
            print("   Start server with: python -m uvicorn main:app --reload --port 8000")
            continue
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    # Clean up
    os.unlink(temp_srt_path)
    print(f"\n🗑️ Cleaned up temp file: {temp_srt_path}")

def show_example_responses():
    """Show example response formats"""
    
    print("\n📋 EXAMPLE API RESPONSES")
    print("="*50)
    
    print("\n1️⃣ Success Response (Validation Passed):")
    success_response = {
        "status": "success",
        "chunks_uploaded": 3,
        "validation": {
            "coverage_complete": True,
            "text_coverage_percentage": 100.0,
            "timeline_coverage_percentage": 100.0,
            "missing_subtitles_count": 0,
            "timeline_gaps_count": 0,
            "overlapping_chunks_count": 0,
            "errors": [],
            "warnings": []
        }
    }
    print(json.dumps(success_response, indent=2))
    
    print("\n2️⃣ Success Response (With Warnings):")
    warning_response = {
        "status": "success",
        "chunks_uploaded": 3,
        "validation": {
            "coverage_complete": False,
            "text_coverage_percentage": 94.2,
            "timeline_coverage_percentage": 98.5,
            "missing_subtitles_count": 1,
            "timeline_gaps_count": 1,
            "overlapping_chunks_count": 0,
            "errors": ["Text coverage is only 94.2%"],
            "warnings": ["Found 1 timeline gaps"]
        }
    }
    print(json.dumps(warning_response, indent=2))
    
    print("\n3️⃣ Error Response (Strict Mode):")
    error_response = {
        "detail": "Transcript validation failed: ['Missing 2 subtitles in chunks', 'Text coverage is only 89.1%']"
    }
    print(json.dumps(error_response, indent=2))
    
    print("\n4️⃣ Detailed Response (Debug Mode):")
    detailed_response = {
        "status": "success",
        "chunks_uploaded": 3,
        "validation": {
            "coverage_complete": True,
            "text_coverage_percentage": 100.0,
            "timeline_coverage_percentage": 100.0,
            "missing_subtitles_count": 0,
            "timeline_gaps_count": 0,
            "overlapping_chunks_count": 0,
            "errors": [],
            "warnings": [],
            "detailed_report": "📊 TRANSCRIPT VALIDATION REPORT\n==================================================\n✅ VALIDATION PASSED - All subtitles covered\n\n📈 Coverage Statistics:\n   Text Coverage: 100.0%\n   Timeline Coverage: 100.0%\n   Original Subtitles: 4\n   Generated Chunks: 2"
        }
    }
    print(json.dumps(detailed_response, indent=2))

def show_frontend_examples():
    """Show frontend integration examples"""
    
    print("\n💻 FRONTEND INTEGRATION EXAMPLES")
    print("="*50)
    
    print("\n📄 JavaScript Example:")
    js_example = '''
// Upload with validation handling
async function uploadTranscript(file, metadata) {
  const formData = new FormData();
  formData.append('file', file);
  Object.keys(metadata).forEach(key => {
    formData.append(key, metadata[key]);
  });

  try {
    const response = await fetch('/upload-transcript', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    if (response.ok) {
      console.log(`✅ Upload successful! ${result.chunks_uploaded} chunks uploaded`);
      
      // Handle validation results
      if (result.validation) {
        const val = result.validation;
        
        if (val.coverage_complete) {
          showSuccessMessage(`Perfect! ${val.text_coverage_percentage}% coverage`);
        } else {
          showWarningMessage([
            `Text Coverage: ${val.text_coverage_percentage}%`,
            `Missing Subtitles: ${val.missing_subtitles_count}`,
            `Timeline Gaps: ${val.timeline_gaps_count}`
          ]);
        }
        
        // Show errors and warnings
        if (val.errors.length > 0) {
          showErrorMessages(val.errors);
        }
        if (val.warnings.length > 0) {
          showWarningMessages(val.warnings);
        }
      }
      
      return result;
    } else {
      throw new Error(result.detail || 'Upload failed');
    }
  } catch (error) {
    console.error('Upload error:', error);
    showErrorMessage(error.message);
    throw error;
  }
}

// Usage
const metadata = {
  category: 'Satsang',
  location: 'Bangalore',
  date: '2025-07-27'
};

uploadTranscript(fileInput.files[0], metadata)
  .then(result => console.log('Success:', result))
  .catch(error => console.error('Failed:', error));
'''
    
    print(js_example)
    
    print("\n⚛️ React Component Example:")
    react_example = '''
function ValidationDisplay({ validation }) {
  if (!validation) return null;

  return (
    <div className="validation-results">
      <h3>Validation Results</h3>
      
      <div className={`status ${validation.coverage_complete ? 'success' : 'warning'}`}>
        {validation.coverage_complete ? '✅ Validation Passed' : '⚠️ Issues Detected'}
      </div>
      
      <div className="metrics">
        <div>Text Coverage: {validation.text_coverage_percentage.toFixed(1)}%</div>
        <div>Timeline Coverage: {validation.timeline_coverage_percentage.toFixed(1)}%</div>
        <div>Missing Subtitles: {validation.missing_subtitles_count}</div>
        <div>Timeline Gaps: {validation.timeline_gaps_count}</div>
      </div>
      
      {validation.errors.length > 0 && (
        <div className="errors">
          <h4>Errors:</h4>
          <ul>
            {validation.errors.map((error, i) => (
              <li key={i} className="error">{error}</li>
            ))}
          </ul>
        </div>
      )}
      
      {validation.warnings.length > 0 && (
        <div className="warnings">
          <h4>Warnings:</h4>
          <ul>
            {validation.warnings.map((warning, i) => (
              <li key={i} className="warning">{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
'''
    
    print(react_example)

if __name__ == "__main__":
    # Show example responses first
    show_example_responses()
    
    # Show frontend integration examples
    show_frontend_examples()
    
    # Test with actual server (if running)
    print("\n🚀 To test with actual server:")
    print("1. Start server: python -m uvicorn main:app --reload --port 8000")
    print("2. Run: python test_upload_with_validation_response.py")
    print("3. Check different validation modes in .env file")
