import pytest
import os
import tempfile
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-api-key',
        'QDRANT_HOST': 'localhost',
        'QDRANT_PORT': '6333',
    }):
        yield

@pytest.fixture
def temp_transcript_prompt():
    """Create a temporary transcript processing prompt file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
You are an AI assistant that processes spiritual discourse transcripts.
Your task is to intelligently chunk the transcript and provide summaries and tags.

Please process the following transcript and return a JSON response with:
1. global_tags: Array of overall themes/topics
2. chunks: Array of intelligent chunks with summaries and tags

Each chunk should have:
- start: timestamp
- end: timestamp  
- text: the actual text
- summary: brief summary of the chunk
- tags: relevant tags for the chunk
""")
        f.flush()
        
        # Patch the file reading in main.py to use our temp file
        with patch('builtins.open') as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = f.read()
            yield f.name
        
        # Clean up
        os.unlink(f.name)

@pytest.fixture
def sample_srt_content():
    """Sample SRT content for testing"""
    return """1
00:00:01,000 --> 00:00:05,000
Welcome to the spiritual discourse.

2
00:00:05,000 --> 00:00:10,000
Today we will discuss the nature of consciousness.

3
00:00:10,000 --> 00:00:15,000
Understanding the self is the first step to enlightenment.

4
00:00:15,000 --> 00:00:20,000
The journey inward requires patience and dedication.

5
00:00:20,000 --> 00:00:25,000
Through meditation, we can achieve inner peace.
"""
