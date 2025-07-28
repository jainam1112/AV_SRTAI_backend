# Transcript Processing API

A FastAPI-based backend service for processing SRT subtitle files, extracting content chunks, and storing them in a Qdrant vector database for semantic search.

## Features

- **SRT File Upload**: Process subtitle files with metadata
- **Intelligent Chunking**: Use OpenAI GPT-3.5-turbo for content segmentation
- **Vector Storage**: Store embeddings in Qdrant cloud database
- **Validation System**: Comprehensive coverage analysis with multiple modes
- **Semantic Search**: Find relevant content using vector similarity
- **RESTful API**: Clean FastAPI endpoints with automatic documentation

## 🚀 Local Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
Create a `.env` file in the `backend` folder with:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=text-embedding-3-small
ANSWER_EXTRACTION_MODEL=gpt-3.5-turbo
RERANK_MODEL=gpt-4-turbo-preview

# Qdrant Configuration
QDRANT_HOST=your_qdrant_host.cloud.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_api_key_here
COLLECTION_NAME=your_collection_name

# Validation Configuration
VALIDATION_MODE=warn  # Options: strict, warn, detailed
```

4. Run the server:
```bash
python main.py
# Or alternatively:
uvicorn main:app --host 0.0.0.0 --port 10000 --reload
```

## API Documentation

The API will be available at `http://localhost:10000` with interactive documentation at `http://localhost:10000/docs`

### Upload Transcript

```bash
curl -X POST "http://localhost:10000/upload-transcript" \
  -F "file=@transcript.srt" \
  -F "category=Satsang" \
  -F "location=Bangalore" \
  -F "date=2025-07-28"
```

**Response with Validation:**
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

## Validation System

The application includes a comprehensive validation system with three modes:

- **warn**: Continue processing with warnings (default)
- **strict**: Fail upload if validation errors are found  
- **detailed**: Include detailed validation report in response

## Testing

```bash
# Run all tests
python -m pytest

# Run specific test
python -m pytest test_upload_transcript.py

# Interactive testing
python interactive_api_test.py
```

## Project Structure

```
backend/
├── main.py                    # FastAPI application entry point
├── models.py                  # Pydantic models for API requests/responses
├── srt_processor.py          # SRT file parsing and processing
├── bio_extraction.py         # Content chunking with OpenAI
├── embedding.py              # Text embedding generation
├── quadrant_client.py        # Qdrant vector database client
├── validation_utils.py       # Transcript validation and coverage analysis
├── utils.py                  # Utility functions
├── requirements.txt          # Python dependencies
├── .env                     # Environment variables (not in git)
└── tests/                   # Test files
```

## 🌐 Render Deployment

1. Push backend code to a GitHub repo.
2. Connect repo to [Render](https://render.com/).
3. Use the `render.yaml` as deploy blueprint.
4. Set the following environment variables in Render dashboard:
   - `OPENAI_API_KEY`
   - `QDRANT_HOST`
   - `QDRANT_API_KEY`
   - `COLLECTION_NAME`
   - `VALIDATION_MODE`

## Troubleshooting

### Common Issues

1. **Qdrant 403 Forbidden**
   - Check API key permissions in Qdrant Cloud
   - Verify collection exists and has write access
   - Ensure API key format is correct (no quotes)

2. **OpenAI API Errors**
   - Verify API key is valid and has credits
   - Check rate limits and token usage

3. **Upload Failures**
   - Ensure SRT file format is valid
   - Check all required metadata fields

### Debug Tools

- `debug_qdrant.py` - Test Qdrant connection and permissions
- `debug_chunks.py` - Debug chunking process
- `simple_api_test.py` - Basic API testing

For detailed frontend integration, see `FRONTEND_API_GUIDE.md`