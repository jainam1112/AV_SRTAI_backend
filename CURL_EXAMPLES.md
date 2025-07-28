# Complete cURL Examples for /upload-transcript API

This guide provides complete cURL commands for testing the `/upload-transcript` endpoint that your frontend can reference.

## Base URL
```bash
BASE_URL="http://localhost:10000"  # Change to your production URL
```

## 1. Basic Upload (Minimal Parameters)

```bash
curl -X POST "$BASE_URL/upload-transcript" \
  -F "file=@your_transcript.srt" \
  -H "Content-Type: multipart/form-data"
```

**Response:**
```json
{
  "status": "success", 
  "chunks_uploaded": 3,
  "validation": {
    "coverage_complete": true,
    "text_coverage_percentage": 100.0,
    "timeline_coverage_percentage": 100.0,
    "missing_subtitles_count": 0,
    "timeline_gaps_count": 0,
    "overlapping_chunks_count": 0,
    "errors": [],
    "warnings": []
  }
}
```

## 2. Upload with Custom Date

```bash
curl -X POST "$BASE_URL/upload-transcript" \
  -F "file=@your_transcript.srt" \
  -F "date=2025-12-25" \
  -H "Content-Type: multipart/form-data"
```

## 3. Complete Upload with All Metadata

```bash
curl -X POST "$BASE_URL/upload-transcript" \
  -F "file=@satsang_transcript.srt" \
  -F "category=Satsang" \
  -F "location=Bangalore Ashram" \
  -F "speaker=Gurudev Sri Sri Ravi Shankar" \
  -F "satsang_name=Nature of Consciousness" \
  -F "satsang_code=SAT2025001" \
  -F "misc_tags=consciousness,meditation,awareness,spirituality" \
  -F "date=2025-07-27" \
  -H "Content-Type: multipart/form-data"
```

**Response:**
```json
{
  "status": "success",
  "chunks_uploaded": 5,
  "validation": {
    "coverage_complete": true,
    "text_coverage_percentage": 100.0,
    "timeline_coverage_percentage": 100.0,
    "missing_subtitles_count": 0,
    "timeline_gaps_count": 0,
    "overlapping_chunks_count": 0,
    "errors": [],
    "warnings": []
  }
}
```

## Response Examples

### Perfect Upload (100% Coverage)
```json
{
  "status": "success",
  "chunks_uploaded": 3,
  "validation": {
    "coverage_complete": true,
    "text_coverage_percentage": 100.0,
    "timeline_coverage_percentage": 100.0,
    "missing_subtitles_count": 0,
    "timeline_gaps_count": 0,
    "overlapping_chunks_count": 0,
    "errors": [],
    "warnings": []
  }
}
```

### Upload with Warnings (Issues Detected)
```json
{
  "status": "success",
  "chunks_uploaded": 3,
  "validation": {
    "coverage_complete": false,
    "text_coverage_percentage": 94.2,
    "timeline_coverage_percentage": 98.5,
    "missing_subtitles_count": 1,
    "timeline_gaps_count": 1,
    "overlapping_chunks_count": 0,
    "errors": ["Text coverage is only 94.2%"],
    "warnings": ["Found 1 timeline gaps"]
  }
}
```

### Strict Mode Failure (HTTP 422)
```json
{
  "detail": "Transcript validation failed: ['Missing 2 subtitles in chunks', 'Text coverage is only 89.1%']"
}
```

## 4. Upload with Variables (Frontend Template)

```bash
# Set your variables
FILE_PATH="/path/to/your/transcript.srt"
CATEGORY="Satsang"
LOCATION="Your Location"
SPEAKER="Speaker Name"
SATSANG_NAME="Discourse Title"
SATSANG_CODE="UNIQUE_CODE"
TAGS="tag1,tag2,tag3"
DATE="2025-07-27"

# Execute upload
curl -X POST "$BASE_URL/upload-transcript" \
  -F "file=@$FILE_PATH" \
  -F "category=$CATEGORY" \
  -F "location=$LOCATION" \
  -F "speaker=$SPEAKER" \
  -F "satsang_name=$SATSANG_NAME" \
  -F "satsang_code=$SATSANG_CODE" \
  -F "misc_tags=$TAGS" \
  -F "date=$DATE" \
  -H "Content-Type: multipart/form-data"
```

## 5. Upload with Only Required Fields + Date

```bash
curl -X POST "$BASE_URL/upload-transcript" \
  -F "file=@transcript.srt" \
  -F "date=2025-07-27" \
  -H "Content-Type: multipart/form-data"
```

## 6. Production Example with Error Handling

```bash
curl -X POST "$BASE_URL/upload-transcript" \
  -F "file=@transcript.srt" \
  -F "category=Satsang" \
  -F "location=Bangalore" \
  -F "speaker=Gurudev" \
  -F "date=2025-07-27" \
  -H "Content-Type: multipart/form-data" \
  --max-time 300 \
  --retry 3 \
  --retry-delay 5 \
  -w "Status: %{http_code}\nTime: %{time_total}s\n" \
  -o response.json
```

## 7. Using HTTPS (Production)

```bash
curl -X POST "https://your-domain.com/upload-transcript" \
  -F "file=@transcript.srt" \
  -F "category=Satsang" \
  -F "date=2025-07-27" \
  -H "Content-Type: multipart/form-data" \
  --insecure  # Only if using self-signed certificates
```

## JavaScript Fetch Equivalent for Frontend

### Basic Upload
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('date', '2025-07-27');

fetch('/upload-transcript', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### Complete Upload with All Fields
```javascript
const uploadTranscript = async (file, metadata) => {
  const formData = new FormData();
  
  // Required file
  formData.append('file', file);
  
  // Optional metadata with defaults
  formData.append('category', metadata.category || 'Miscellaneous');
  formData.append('location', metadata.location || 'Unknown');
  formData.append('speaker', metadata.speaker || 'Gurudev');
  formData.append('satsang_name', metadata.satsang_name || '');
  formData.append('satsang_code', metadata.satsang_code || '');
  formData.append('misc_tags', metadata.misc_tags || '');
  formData.append('date', metadata.date || new Date().toISOString().split('T')[0]);

  try {
    const response = await fetch('/upload-transcript', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Upload failed:', error);
    throw error;
  }
};

// Usage
const metadata = {
  category: 'Satsang',
  location: 'Bangalore Ashram',
  speaker: 'Gurudev Sri Sri Ravi Shankar',
  satsang_name: 'Nature of Consciousness',
  satsang_code: 'SAT2025001',
  misc_tags: 'consciousness,meditation,awareness',
  date: '2025-07-27'
};

uploadTranscript(fileInput.files[0], metadata)
  .then(result => console.log('Upload successful:', result))
  .catch(error => console.error('Upload failed:', error));
```

## React Example Component

```jsx
import React, { useState } from 'react';

const TranscriptUploader = () => {
  const [file, setFile] = useState(null);
  const [metadata, setMetadata] = useState({
    category: 'Satsang',
    location: 'Bangalore Ashram',
    speaker: 'Gurudev',
    satsang_name: '',
    satsang_code: '',
    misc_tags: '',
    date: new Date().toISOString().split('T')[0]
  });
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
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
        alert(`Upload successful! ${result.chunks_uploaded} chunks uploaded.`);
      } else {
        alert(`Upload failed: ${result.detail}`);
      }
    } catch (error) {
      alert(`Upload error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleUpload}>
      <input
        type="file"
        accept=".srt"
        onChange={(e) => setFile(e.target.files[0])}
        required
      />
      
      <input
        type="text"
        placeholder="Category"
        value={metadata.category}
        onChange={(e) => setMetadata({...metadata, category: e.target.value})}
      />
      
      <input
        type="date"
        value={metadata.date}
        onChange={(e) => setMetadata({...metadata, date: e.target.value})}
      />
      
      <button type="submit" disabled={uploading || !file}>
        {uploading ? 'Uploading...' : 'Upload Transcript'}
      </button>
    </form>
  );
};
```

## Error Responses

### Invalid File Extension
```bash
curl -X POST "$BASE_URL/upload-transcript" \
  -F "file=@document.txt"
```
**Response (400):**
```json
{
  "detail": "Only .srt files are supported."
}
```

### Invalid Encoding
**Response (400):**
```json
{
  "detail": "File must be UTF-8 encoded."
}
```

### Server Error
**Response (500):**
```json
{
  "detail": "Internal server error"
}
```

## Testing Your API

### 1. Health Check First
```bash
curl -X GET "$BASE_URL/health"
```
**Expected Response:**
```json
{
  "success": true,
  "data": {
    "status": "ok"
  }
}
```

### 2. Create Test SRT File
```bash
cat > test_transcript.srt << 'EOF'
1
00:00:01,000 --> 00:00:05,000
Welcome to today's satsang.

2
00:00:05,000 --> 00:00:10,000
We will discuss consciousness and awareness.

3
00:00:10,000 --> 00:00:15,000
Thank you for joining us today.
EOF
```

### 3. Test Upload
```bash
curl -X POST "$BASE_URL/upload-transcript" \
  -F "file=@test_transcript.srt" \
  -F "date=2025-07-27" \
  -v
```

## Production Considerations

### 1. File Size Limits
Add file size validation to your frontend:
```javascript
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

if (file.size > MAX_FILE_SIZE) {
  alert('File too large. Maximum size is 10MB.');
  return;
}
```

### 2. Progress Tracking
```javascript
const xhr = new XMLHttpRequest();
xhr.upload.addEventListener('progress', (e) => {
  if (e.lengthComputable) {
    const percentComplete = (e.loaded / e.total) * 100;
    console.log(`Upload ${percentComplete}% complete`);
  }
});
```

### 3. Timeout Handling
```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes

fetch('/upload-transcript', {
  method: 'POST',
  body: formData,
  signal: controller.signal
})
.finally(() => clearTimeout(timeoutId));
```

## Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | File | Yes | - | SRT subtitle file |
| `category` | String | No | "Miscellaneous" | Content category |
| `location` | String | No | "Unknown" | Recording location |
| `speaker` | String | No | "Gurudev" | Speaker name |
| `satsang_name` | String | No | "" | Discourse title |
| `satsang_code` | String | No | "" | Unique identifier |
| `misc_tags` | String | No | "" | Comma-separated tags |
| `date` | String | No | Today | Date in YYYY-MM-DD format |

Use these examples as templates for your frontend implementation! 🚀
