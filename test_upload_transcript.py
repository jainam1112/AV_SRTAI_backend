import pytest
import json
from unittest.mock import patch, mock_open, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import io
from datetime import datetime

# Import the app and dependencies
from main import app, process_transcript_with_llm
from models import UploadTranscriptResponse

# Create test client
client = TestClient(app)

# Sample SRT content for testing
SAMPLE_SRT_CONTENT = """1
00:00:01,000 --> 00:00:05,000
Welcome to the spiritual discourse.

2
00:00:05,000 --> 00:00:10,000
Today we will discuss the nature of consciousness.

3
00:00:10,000 --> 00:00:15,000
Understanding the self is the first step to enlightenment.
"""

SAMPLE_SRT_BYTES = SAMPLE_SRT_CONTENT.encode('utf-8')

# Expected parsed chunks from the SRT
EXPECTED_PARSED_CHUNKS = [
    {
        "start": "0:00:01",
        "end": "0:00:05", 
        "text": "Welcome to the spiritual discourse."
    },
    {
        "start": "0:00:05",
        "end": "0:00:10",
        "text": "Today we will discuss the nature of consciousness."
    },
    {
        "start": "0:00:10", 
        "end": "0:00:15",
        "text": "Understanding the self is the first step to enlightenment."
    }
]

# Mock LLM response
MOCK_LLM_RESPONSE = {
    "global_tags": ["spirituality", "consciousness", "enlightenment"],
    "chunks": [
        {
            "start": "0:00:01",
            "end": "0:00:05",
            "text": "Welcome to the spiritual discourse.",
            "summary": "Introduction to spiritual discourse",
            "tags": ["introduction", "spiritual"]
        },
        {
            "start": "0:00:05", 
            "end": "0:00:10",
            "text": "Today we will discuss the nature of consciousness.",
            "summary": "Discussion about consciousness",
            "tags": ["consciousness", "discussion"]
        },
        {
            "start": "0:00:10",
            "end": "0:00:15", 
            "text": "Understanding the self is the first step to enlightenment.",
            "summary": "Self-understanding and enlightenment",
            "tags": ["self", "enlightenment"]
        }
    ]
}


class TestUploadTranscript:
    """Test class for the upload-transcript endpoint"""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies"""
        with patch('main.parse_srt') as mock_parse_srt, \
             patch('main.embed_and_tag_chunks') as mock_embed_and_tag, \
             patch('main.store_chunks') as mock_store_chunks, \
             patch('main.process_transcript_with_llm') as mock_process_llm, \
             patch('builtins.open', mock_open(read_data="Mock prompt content")):
            
            # Set up mock return values
            mock_parse_srt.return_value = EXPECTED_PARSED_CHUNKS.copy()
            mock_process_llm.return_value = MOCK_LLM_RESPONSE.copy()
            
            # Mock embed_and_tag_chunks to return enriched chunks
            def mock_embed_func(chunks):
                enriched = []
                for chunk in chunks:
                    enriched_chunk = chunk.copy()
                    enriched_chunk.update({
                        "entities": {"people": ["Gurudev"], "places": ["Ashram"]},
                        "biographical_extractions": {"spiritual_journey_influences": ["enlightenment"]}
                    })
                    enriched.append(enriched_chunk)
                return enriched
            
            mock_embed_and_tag.side_effect = mock_embed_func
            mock_store_chunks.return_value = None
            
            yield {
                'parse_srt': mock_parse_srt,
                'embed_and_tag': mock_embed_and_tag,
                'store_chunks': mock_store_chunks,
                'process_llm': mock_process_llm
            }

    def test_successful_upload(self, mock_dependencies):
        """Test successful transcript upload with all valid inputs"""
        # Prepare test file
        files = {
            "file": ("test_transcript.srt", io.BytesIO(SAMPLE_SRT_BYTES), "text/plain")
        }
        
        # Make request
        response = client.post("/upload-transcript", files=files)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["chunks_uploaded"] == 3
        
        # Verify mocks were called
        mock_dependencies['parse_srt'].assert_called_once()
        mock_dependencies['process_llm'].assert_called_once()
        mock_dependencies['embed_and_tag'].assert_called_once()
        mock_dependencies['store_chunks'].assert_called_once()

    def test_upload_with_metadata(self, mock_dependencies):
        """Test upload with custom metadata"""
        files = {
            "file": ("test_transcript.srt", io.BytesIO(SAMPLE_SRT_BYTES), "text/plain")
        }
        
        data = {
            "category": "Pravachan",
            "location": "Sayla",
            "speaker": "Gurudev",
            "satsang_name": "Morning Discourse",
            "satsang_code": "MD001",
            "misc_tags": "morning,discourse,meditation"
        }
        
        response = client.post("/upload-transcript", files=files, data=data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        
        # Verify the LLM was called with parsed chunks
        mock_dependencies['process_llm'].assert_called_once()
        args, kwargs = mock_dependencies['process_llm'].call_args
        subtitles = args[0]
        assert len(subtitles) == 3
        assert subtitles[0]["text"] == "Welcome to the spiritual discourse."

    def test_invalid_file_extension(self, mock_dependencies):
        """Test upload with invalid file extension"""
        files = {
            "file": ("test_transcript.txt", io.BytesIO(SAMPLE_SRT_BYTES), "text/plain")
        }
        
        response = client.post("/upload-transcript", files=files)
        
        assert response.status_code == 400
        assert "Only .srt files are supported" in response.json()["detail"]

    def test_invalid_encoding(self, mock_dependencies):
        """Test upload with invalid file encoding"""
        # Create invalid UTF-8 content
        invalid_content = b'\xff\xfe\x00\x00Invalid UTF-8 content'
        
        files = {
            "file": ("test_transcript.srt", io.BytesIO(invalid_content), "text/plain")
        }
        
        response = client.post("/upload-transcript", files=files)
        
        assert response.status_code == 400
        assert "File must be UTF-8 encoded" in response.json()["detail"]

    def test_empty_file(self, mock_dependencies):
        """Test upload with empty file"""
        files = {
            "file": ("empty.srt", io.BytesIO(b""), "text/plain")
        }
        
        response = client.post("/upload-transcript", files=files)
        
        # Should still process successfully but with no chunks
        assert response.status_code == 200

    def test_parse_srt_failure(self, mock_dependencies):
        """Test behavior when SRT parsing fails"""
        mock_dependencies['parse_srt'].side_effect = Exception("SRT parsing failed")
        
        files = {
            "file": ("test_transcript.srt", io.BytesIO(SAMPLE_SRT_BYTES), "text/plain")
        }
        
        with pytest.raises(Exception):
            response = client.post("/upload-transcript", files=files)

    def test_llm_processing_failure(self, mock_dependencies):
        """Test behavior when LLM processing fails"""
        mock_dependencies['process_llm'].side_effect = Exception("LLM processing failed")
        
        files = {
            "file": ("test_transcript.srt", io.BytesIO(SAMPLE_SRT_BYTES), "text/plain")
        }
        
        with pytest.raises(Exception):
            response = client.post("/upload-transcript", files=files)

    def test_embedding_failure(self, mock_dependencies):
        """Test behavior when embedding fails"""
        mock_dependencies['embed_and_tag'].side_effect = Exception("Embedding failed")
        
        files = {
            "file": ("test_transcript.srt", io.BytesIO(SAMPLE_SRT_BYTES), "text/plain")
        }
        
        with pytest.raises(Exception):
            response = client.post("/upload-transcript", files=files)

    def test_storage_failure(self, mock_dependencies):
        """Test behavior when chunk storage fails"""
        mock_dependencies['store_chunks'].side_effect = Exception("Storage failed")
        
        files = {
            "file": ("test_transcript.srt", io.BytesIO(SAMPLE_SRT_BYTES), "text/plain")
        }
        
        with pytest.raises(Exception):
            response = client.post("/upload-transcript", files=files)

    def test_date_formatting(self, mock_dependencies):
        """Test date handling - both user-provided and default"""
        files = {
            "file": ("test_transcript.srt", io.BytesIO(SAMPLE_SRT_BYTES), "text/plain")
        }
        
        # Test 1: User-provided date
        data = {"date": "2025-12-25"}
        response = client.post("/upload-transcript", files=files, data=data)
        assert response.status_code == 200
        
        # Test 2: Default date (should use today's date)
        response = client.post("/upload-transcript", files=files)
        assert response.status_code == 200

    def test_misc_tags_parsing(self, mock_dependencies):
        """Test that misc_tags are properly parsed from comma-separated string"""
        files = {
            "file": ("test_transcript.srt", io.BytesIO(SAMPLE_SRT_BYTES), "text/plain")
        }
        
        data = {
            "misc_tags": "tag1, tag2 ,  tag3  , tag4"
        }
        
        response = client.post("/upload-transcript", files=files, data=data)
        
        assert response.status_code == 200
        # The tags should be properly cleaned and split

    def test_chunk_payload_creation(self, mock_dependencies):
        """Test that chunk payloads are created with all required fields"""
        files = {
            "file": ("test_transcript.srt", io.BytesIO(SAMPLE_SRT_BYTES), "text/plain")
        }
        
        response = client.post("/upload-transcript", files=files)
        
        assert response.status_code == 200
        
        # Verify store_chunks was called with properly formatted chunks
        store_call_args = mock_dependencies['store_chunks'].call_args[0][0]
        
        for chunk in store_call_args:
            payload = chunk["payload"]
            
            # Check required fields exist
            required_fields = [
                "original_text", "timestamp", "transcript_name", "date",
                "category", "location", "speaker", "satsang_name", "satsang_code",
                "misc_tags", "summary", "tags", "global_tags", "entities",
                "biographical_extractions"
            ]
            
            for field in required_fields:
                assert field in payload
            
            # Check biographical flags are added
            assert "has_spiritual_journey_influences" in payload

    def test_response_model_validation(self, mock_dependencies):
        """Test that the response matches the expected model"""
        files = {
            "file": ("test_transcript.srt", io.BytesIO(SAMPLE_SRT_BYTES), "text/plain")
        }
        
        response = client.post("/upload-transcript", files=files)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Validate response structure
        response_model = UploadTranscriptResponse(**response_data)
        assert response_model.status == "success"
        assert response_model.chunks_uploaded == 3


class TestProcessTranscriptWithLLM:
    """Test the LLM processing function separately"""

    @patch('main.openai.chat.completions.create')
    def test_successful_llm_processing(self, mock_openai):
        """Test successful LLM processing"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(MOCK_LLM_RESPONSE)
        mock_openai.return_value = mock_response
        
        result = process_transcript_with_llm(EXPECTED_PARSED_CHUNKS, "Test prompt")
        
        assert result == MOCK_LLM_RESPONSE
        mock_openai.assert_called_once()

    @patch('main.openai.chat.completions.create')
    def test_llm_invalid_json_response(self, mock_openai):
        """Test LLM returning invalid JSON"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_openai.return_value = mock_response
        
        result = process_transcript_with_llm(EXPECTED_PARSED_CHUNKS, "Test prompt")
        
        assert "raw_output" in result
        assert result["raw_output"] == "Invalid JSON response"

    @patch('main.openai.chat.completions.create')
    def test_llm_api_failure(self, mock_openai):
        """Test LLM API failure"""
        mock_openai.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            process_transcript_with_llm(EXPECTED_PARSED_CHUNKS, "Test prompt")


# Integration test fixtures
@pytest.fixture
def sample_srt_file():
    """Provide a sample SRT file for testing"""
    return io.BytesIO(SAMPLE_SRT_BYTES)


if __name__ == "__main__":
    pytest.main([__file__])
