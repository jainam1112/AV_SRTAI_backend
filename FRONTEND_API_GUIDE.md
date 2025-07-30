# Frontend Integration Guide - Upload Transcript API

## Quick Reference for Frontend Developers

### Main Endpoints

#### Upload Transcript
```
POST /upload-transcript
Content-Type: multipart/form-data
```

#### Biographical Extraction
```
POST /transcripts/{transcript_name}/extract-bio
Content-Type: application/json

GET /transcripts/{transcript_name}/bio-status
GET /transcripts
```

### Required Field
- `file`: SRT file (must have .srt extension)

### Optional Fields (with defaults)
- `category`: "Miscellaneous"
- `location`: "Unknown" 
- `speaker`: "Gurudev"
- `satsang_name`: ""
- `satsang_code`: ""
- `misc_tags`: "" (comma-separated)
- `date`: Today's date (YYYY-MM-DD format)

### Success Response (200)
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

### Success Response with Issues (200)
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

### Error Responses (400/500)
```json
{
  "detail": "Error message here"
}
```

## Complete cURL Examples

### Upload Transcript (Main Endpoint)

### 1. Minimal Upload
```bash
curl -X POST "http://localhost:10000/upload-transcript" \
  -F "file=@transcript.srt"
```

### 2. Upload with Custom Date (Most Common)
```bash
curl -X POST "http://localhost:10000/upload-transcript" \
  -F "file=@transcript.srt" \
  -F "date=2025-07-27"
```

### 3. Complete Upload with All Metadata
```bash
curl -X POST "http://localhost:10000/upload-transcript" \
  -F "file=@satsang_transcript.srt" \
  -F "category=Satsang" \
  -F "location=Bangalore Ashram" \
  -F "speaker=Gurudev Sri Sri Ravi Shankar" \
  -F "satsang_name=Nature of Consciousness" \
  -F "satsang_code=SAT2025001" \
  -F "misc_tags=consciousness,meditation,awareness,spirituality" \
  -F "date=2025-07-27"
```

### 4. Production Example with Error Handling
```bash
curl -X POST "https://your-api.com/upload-transcript" \
  -F "file=@transcript.srt" \
  -F "category=Satsang" \
  -F "date=2025-07-27" \
  --max-time 300 \
  --retry 3 \
  -w "Status: %{http_code}\nTime: %{time_total}s\n"
```

### Bio Extraction Endpoints

### 5. Extract Biographical Information
```bash
curl -X POST "http://localhost:10000/transcripts/my_transcript/extract-bio" \
  -H "Content-Type: application/json" \
  -d '{"transcript_name": "my_transcript"}'
```

### 6. Extract with Custom Fine-tuned Model
```bash
curl -X POST "http://localhost:10000/transcripts/my_transcript/extract-bio" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_name": "my_transcript",
    "ft_model_id": "ft:gpt-3.5-turbo:your-org:your-model:id"
  }'
```

### 7. Check Bio Extraction Status
```bash
curl -X GET "http://localhost:10000/transcripts/my_transcript/bio-status"
```

**Bio Extraction Response:**
```json
{
  "status": "success",
  "transcript_name": "my_transcript",
  "chunks_processed": 15,
  "chunks_updated": 12,
  "model_used": "ft:gpt-3.5-turbo:org:bio-model:123",
  "extraction_summary": {
    "early_life_childhood": 3,
    "education_learning": 2,
    "spiritual_journey_influences": 5,
    "family_personal_relationships": 2
  }
}
```

**Bio Status Response:**
```json
{
  "success": true,
  "data": {
    "transcript_name": "my_transcript",
    "total_chunks": 15,
    "chunks_with_bio": 12,
    "bio_coverage_percentage": 80.0,
    "category_summary": {
      "early_life_childhood": 3,
      "education_learning": 2,
      "spiritual_journey_influences": 5
    },
    "needs_extraction": false
  }
}
```

## JavaScript/TypeScript Examples

### Simple Upload Function
```javascript
async function uploadTranscript(file, metadata = {}) {
  const formData = new FormData();
  formData.append('file', file);
  
  // Add metadata with defaults
  formData.append('category', metadata.category || 'Miscellaneous');
  formData.append('location', metadata.location || 'Unknown');
  formData.append('speaker', metadata.speaker || 'Gurudev');
  formData.append('satsang_name', metadata.satsang_name || '');
  formData.append('satsang_code', metadata.satsang_code || '');
  formData.append('misc_tags', metadata.misc_tags || '');
  formData.append('date', metadata.date || new Date().toISOString().split('T')[0]);

  const response = await fetch('/upload-transcript', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  const result = await response.json();
  
  // Handle validation results
  if (result.validation) {
    console.log('Validation Results:', result.validation);
    
    if (!result.validation.coverage_complete) {
      console.warn('Upload completed with issues:', {
        textCoverage: result.validation.text_coverage_percentage,
        timelineCoverage: result.validation.timeline_coverage_percentage,
        missingSubtitles: result.validation.missing_subtitles_count,
        errors: result.validation.errors,
        warnings: result.validation.warnings
      });
    }
  }

  return result;
}
```

### Usage Example
```javascript
// Basic usage
const file = document.getElementById('fileInput').files[0];
try {
  const result = await uploadTranscript(file);
  console.log(`Success! ${result.chunks_uploaded} chunks uploaded`);
  
  // Handle validation results
  if (result.validation) {
    if (result.validation.coverage_complete) {
      console.log(`Perfect upload! ${result.validation.text_coverage_percentage}% coverage`);
    } else {
      console.warn('Upload completed with issues:', {
        textCoverage: `${result.validation.text_coverage_percentage}%`,
        missingSubtitles: result.validation.missing_subtitles_count,
        timelineGaps: result.validation.timeline_gaps_count,
        errors: result.validation.errors,
        warnings: result.validation.warnings
      });
      
      // Show user-friendly messages
      displayValidationWarning(result.validation);
    }
  } else {
    console.log('Perfect upload - no validation issues detected!');
  }
  
} catch (error) {
  console.error('Upload failed:', error.message);
}

// With metadata
const metadata = {
  category: 'Satsang',
  location: 'Bangalore Ashram',
  speaker: 'Gurudev',
  date: '2025-07-27',
  misc_tags: 'consciousness,meditation'
};

const result = await uploadTranscript(file, metadata);

// Helper function to display validation warnings
function displayValidationWarning(validation) {
  const message = [
    `Text Coverage: ${validation.text_coverage_percentage.toFixed(1)}%`,
    `Timeline Coverage: ${validation.timeline_coverage_percentage.toFixed(1)}%`,
    `Missing Subtitles: ${validation.missing_subtitles_count}`,
    `Timeline Gaps: ${validation.timeline_gaps_count}`
  ].join('\n');
  
  alert(`Upload completed with warnings:\n\n${message}`);
}
```

### TypeScript Interface
```typescript
interface UploadMetadata {
  category?: string;
  location?: string;
  speaker?: string;
  satsang_name?: string;
  satsang_code?: string;
  misc_tags?: string;
  date?: string; // YYYY-MM-DD format
}

interface ValidationInfo {
  coverage_complete: boolean;
  text_coverage_percentage: number;
  timeline_coverage_percentage: number;
  missing_subtitles_count: number;
  timeline_gaps_count: number;
  overlapping_chunks_count: number;
  errors: string[];
  warnings: string[];
  detailed_report?: string; // Only in detailed mode
}

interface UploadResponse {
  status: 'success';
  chunks_uploaded: number;
  validation?: ValidationInfo; // Only included when issues detected or in detailed/strict mode
}

interface ErrorResponse {
  detail: string;
}
```

## React Hook Example
```javascript
import { useState } from 'react';

function useTranscriptUpload() {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const upload = async (file, metadata = {}) => {
    setUploading(true);
    setError(null);

    try {
      const result = await uploadTranscript(file, metadata);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setUploading(false);
    }
  };

  return { upload, uploading, error };
}

// Usage in component
function UploadComponent() {
  const { upload, uploading, error } = useTranscriptUpload();

  const handleUpload = async (file) => {
    try {
      const result = await upload(file, { date: '2025-07-27' });
      alert(`Success! ${result.chunks_uploaded} chunks uploaded`);
    } catch (err) {
      // Error already set in hook
    }
  };

  return (
    <div>
      <input type="file" accept=".srt" onChange={(e) => handleUpload(e.target.files[0])} />
      {uploading && <p>Uploading...</p>}
      {error && <p style={{color: 'red'}}>Error: {error}</p>}
    </div>
  );
}
```

## Common Error Cases

### File Extension Error
```bash
# This will fail
curl -X POST "/upload-transcript" -F "file=@document.txt"
# Response: {"detail": "Only .srt files are supported."}
```

### Missing File
```bash
# This will fail
curl -X POST "/upload-transcript"
# Response: 422 Unprocessable Entity
```

### Invalid Date Format
```bash
# This might cause issues (use YYYY-MM-DD)
curl -X POST "/upload-transcript" -F "file=@test.srt" -F "date=07/27/2025"
```

## Testing Commands

### 1. Check if API is running
```bash
curl -X GET "http://localhost:10000/health"
```

### 2. Create test file
```bash
cat > test.srt << 'EOF'
1
00:00:01,000 --> 00:00:05,000
Test subtitle content.

2
00:00:05,000 --> 00:00:10,000
Another test subtitle.
EOF
```

### 3. Test upload
```bash
curl -X POST "http://localhost:10000/upload-transcript" \
  -F "file=@test.srt" \
  -F "date=2025-07-27" \
  -v
```

## Production URLs
Replace `http://localhost:10000` with your production URL:
- Development: `http://localhost:10000`
- Staging: `https://staging-api.yoursite.com`
- Production: `https://api.yoursite.com`

## File Requirements
- **Format**: SRT subtitle file
- **Extension**: Must be `.srt`
- **Encoding**: UTF-8
- **Max Size**: Check your server configuration
- **Content**: Valid SRT format with timestamps and text

## Form Field Summary
| Field | Required | Type | Default | Example |
|-------|----------|------|---------|---------|
| file | ✅ | File | - | transcript.srt |
| date | ❌ | String | Today | "2025-07-27" |
| category | ❌ | String | "Miscellaneous" | "Satsang" |
| location | ❌ | String | "Unknown" | "Bangalore" |
| speaker | ❌ | String | "Gurudev" | "Gurudev Sri Sri" |
| satsang_name | ❌ | String | "" | "Nature of Mind" |
| satsang_code | ❌ | String | "" | "SAT2025001" |
| misc_tags | ❌ | String | "" | "tag1,tag2,tag3" |

## Validation Response Handling

### Understanding Validation Results

The API now returns validation information when issues are detected or when running in detailed/strict mode:

#### Perfect Upload (No validation field)
```json
{
  "status": "success",
  "chunks_uploaded": 3
}
```

#### Upload with Issues
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

### Frontend Validation Handling

```javascript
function handleUploadResult(result) {
  console.log(`✅ Upload successful! ${result.chunks_uploaded} chunks uploaded`);
  
  if (!result.validation) {
    // Perfect upload - no validation field means no issues
    showSuccessMessage("Perfect upload! All content processed successfully.");
    return;
  }
  
  const validation = result.validation;
  
  if (validation.coverage_complete) {
    // Good upload with full coverage
    showSuccessMessage(`Upload completed successfully! ${validation.text_coverage_percentage}% coverage`);
  } else {
    // Upload completed but with issues
    const issues = [];
    
    if (validation.text_coverage_percentage < 100) {
      issues.push(`Text coverage: ${validation.text_coverage_percentage.toFixed(1)}%`);
    }
    
    if (validation.missing_subtitles_count > 0) {
      issues.push(`${validation.missing_subtitles_count} subtitle(s) missing`);
    }
    
    if (validation.timeline_gaps_count > 0) {
      issues.push(`${validation.timeline_gaps_count} timeline gap(s)`);
    }
    
    showWarningMessage(`Upload completed with issues: ${issues.join(', ')}`);
  }
  
  // Handle errors and warnings
  if (validation.errors.length > 0) {
    console.error('Validation errors:', validation.errors);
  }
  
  if (validation.warnings.length > 0) {
    console.warn('Validation warnings:', validation.warnings);
  }
}

// Example usage
try {
  const result = await uploadTranscript(file, metadata);
  handleUploadResult(result);
} catch (error) {
  if (error.message.includes('Transcript validation failed')) {
    showErrorMessage('Upload failed: Transcript validation errors detected. Please check your file.');
  } else {
    showErrorMessage(`Upload failed: ${error.message}`);
  }
}
```

### UI Feedback Examples

```javascript
// Success message for perfect uploads
function showSuccessMessage(message) {
  document.getElementById('result').innerHTML = `
    <div class="alert alert-success">
      <span class="icon">✅</span>
      <span class="message">${message}</span>
    </div>
  `;
}

// Warning message for uploads with issues
function showWarningMessage(message) {
  document.getElementById('result').innerHTML = `
    <div class="alert alert-warning">
      <span class="icon">⚠️</span>
      <span class="message">${message}</span>
      <div class="details">Check the console for detailed validation information.</div>
    </div>
  `;
}

// Error message for failed uploads
function showErrorMessage(message) {
  document.getElementById('result').innerHTML = `
    <div class="alert alert-error">
      <span class="icon">❌</span>
      <span class="message">${message}</span>
    </div>
  `;
}
```

Copy and modify these examples for your frontend implementation! 🚀
