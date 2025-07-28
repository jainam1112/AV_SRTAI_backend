import pytest
import io
import threading
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestUploadTranscriptEdgeCases:
    """Test edge cases and real-world scenarios for upload-transcript"""

    @pytest.fixture
    def large_srt_content(self):
        """Generate a large SRT file for testing performance"""
        content = ""
        for i in range(1, 1001):  # 1000 subtitles
            start_sec = i * 5
            end_sec = start_sec + 5
            start_time = f"00:{start_sec//60:02d}:{start_sec%60:02d},000"
            end_time = f"00:{end_sec//60:02d}:{end_sec%60:02d},000"
            content += f"{i}\n{start_time} --> {end_time}\nThis is subtitle number {i} with some spiritual content.\n\n"
        return content.encode('utf-8')

    @pytest.fixture
    def malformed_srt_content(self):
        """Generate malformed SRT content for testing error handling"""
        return """1
INVALID_TIMESTAMP --> 00:00:05,000
This subtitle has invalid timestamp format.

2
00:00:05,000 --> ALSO_INVALID
Another invalid timestamp.

MISSING_NUMBER
00:00:10,000 --> 00:00:15,000
This subtitle is missing its sequence number.
""".encode('utf-8')

    def test_large_file_upload(self, large_srt_content):
        """Test uploading a large SRT file"""
        with patch('main.parse_srt') as mock_parse, \
             patch('main.process_transcript_with_llm') as mock_llm, \
             patch('main.embed_and_tag_chunks') as mock_embed, \
             patch('main.store_chunks') as mock_store, \
             patch('builtins.open'):
            
            # Mock returns for large file
            mock_parse.return_value = [{"start": "0:00:01", "end": "0:00:05", "text": f"Chunk {i}"} for i in range(1000)]
            mock_llm.return_value = {
                "global_tags": ["large_file"],
                "chunks": [{"start": "0:00:01", "end": "0:00:05", "text": f"Chunk {i}", "summary": f"Summary {i}", "tags": [f"tag{i}"]} for i in range(1000)]
            }
            mock_embed.return_value = mock_llm.return_value["chunks"]
            mock_store.return_value = None
            
            files = {
                "file": ("large_transcript.srt", io.BytesIO(large_srt_content), "text/plain")
            }
            
            response = client.post("/upload-transcript", files=files)
            
            assert response.status_code == 200
            assert response.json()["chunks_uploaded"] == 1000

    def test_special_characters_in_content(self):
        """Test handling of special characters and Unicode in SRT content"""
        special_content = """1
00:00:01,000 --> 00:00:05,000
नमस्ते, स्वागत है। Welcome to the दर्शन.

2
00:00:05,000 --> 00:00:10,000
Today's topic: "आत्मा" & consciousness 🕉️

3
00:00:10,000 --> 00:00:15,000
Special chars: @#$%^&*()_+-={}[]|\\:";'<>?,./ और भी।
""".encode('utf-8')

        with patch('main.parse_srt') as mock_parse, \
             patch('main.process_transcript_with_llm') as mock_llm, \
             patch('main.embed_and_tag_chunks') as mock_embed, \
             patch('main.store_chunks') as mock_store, \
             patch('builtins.open'):
            
            mock_parse.return_value = [
                {"start": "0:00:01", "end": "0:00:05", "text": "नमस्ते, स्वागत है। Welcome to the दर्शन."},
                {"start": "0:00:05", "end": "0:00:10", "text": "Today's topic: \"आत्मा\" & consciousness 🕉️"},
                {"start": "0:00:10", "end": "0:00:15", "text": "Special chars: @#$%^&*()_+-={}[]|\\:\";'<>?,./ और भी।"}
            ]
            mock_llm.return_value = {
                "global_tags": ["unicode", "special_chars"],
                "chunks": mock_parse.return_value
            }
            mock_embed.return_value = mock_llm.return_value["chunks"]
            mock_store.return_value = None
            
            files = {
                "file": ("special_chars.srt", io.BytesIO(special_content), "text/plain")
            }
            
            response = client.post("/upload-transcript", files=files)
            
            assert response.status_code == 200

    def test_very_long_misc_tags(self):
        """Test handling of very long misc_tags input"""
        long_tags = ",".join([f"tag{i}" for i in range(1000)])  # 1000 tags
        
        with patch('main.parse_srt') as mock_parse, \
             patch('main.process_transcript_with_llm') as mock_llm, \
             patch('main.embed_and_tag_chunks') as mock_embed, \
             patch('main.store_chunks') as mock_store, \
             patch('builtins.open'):
            
            mock_parse.return_value = [{"start": "0:00:01", "end": "0:00:05", "text": "Test"}]
            mock_llm.return_value = {"global_tags": [], "chunks": mock_parse.return_value}
            mock_embed.return_value = mock_llm.return_value["chunks"]
            mock_store.return_value = None
            
            files = {
                "file": ("test.srt", io.BytesIO(b"1\n00:00:01,000 --> 00:00:05,000\nTest\n"), "text/plain")
            }
            
            data = {"misc_tags": long_tags}
            
            response = client.post("/upload-transcript", files=files, data=data)
            
            assert response.status_code == 200

    def test_empty_metadata_fields(self):
        """Test handling of empty metadata fields"""
        with patch('main.parse_srt') as mock_parse, \
             patch('main.process_transcript_with_llm') as mock_llm, \
             patch('main.embed_and_tag_chunks') as mock_embed, \
             patch('main.store_chunks') as mock_store, \
             patch('builtins.open'):
            
            mock_parse.return_value = [{"start": "0:00:01", "end": "0:00:05", "text": "Test"}]
            mock_llm.return_value = {"global_tags": [], "chunks": mock_parse.return_value}
            mock_embed.return_value = mock_llm.return_value["chunks"]
            mock_store.return_value = None
            
            files = {
                "file": ("test.srt", io.BytesIO(b"1\n00:00:01,000 --> 00:00:05,000\nTest\n"), "text/plain")
            }
            
            data = {
                "category": "",
                "location": "",
                "speaker": "",
                "satsang_name": "",
                "satsang_code": "",
                "misc_tags": ""
            }
            
            response = client.post("/upload-transcript", files=files, data=data)
            
            assert response.status_code == 200

    def test_concurrent_uploads(self):
        """Test handling of multiple concurrent uploads"""
        import threading
        import time
        
        results = []
        
        def upload_file(file_name):
            with patch('main.parse_srt') as mock_parse, \
                 patch('main.process_transcript_with_llm') as mock_llm, \
                 patch('main.embed_and_tag_chunks') as mock_embed, \
                 patch('main.store_chunks') as mock_store, \
                 patch('builtins.open'):
                
                mock_parse.return_value = [{"start": "0:00:01", "end": "0:00:05", "text": f"Test {file_name}"}]
                mock_llm.return_value = {"global_tags": [], "chunks": mock_parse.return_value}
                mock_embed.return_value = mock_llm.return_value["chunks"]
                mock_store.return_value = None
                
                files = {
                    "file": (f"{file_name}.srt", io.BytesIO(b"1\n00:00:01,000 --> 00:00:05,000\nTest\n"), "text/plain")
                }
                
                response = client.post("/upload-transcript", files=files)
                results.append(response.status_code)
        
        # Create multiple threads for concurrent uploads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=upload_file, args=(f"test{i}",))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All uploads should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5

    @patch('main.openai.chat.completions.create')
    def test_llm_timeout_handling(self, mock_openai):
        """Test handling of LLM API timeouts"""
        import time
        
        def slow_llm_call(*args, **kwargs):
            time.sleep(1)  # Simulate slow response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = '{"global_tags": [], "chunks": []}'
            return mock_response
        
        mock_openai.side_effect = slow_llm_call
        
        with patch('main.parse_srt') as mock_parse, \
             patch('main.embed_and_tag_chunks') as mock_embed, \
             patch('main.store_chunks') as mock_store, \
             patch('builtins.open'):
            
            mock_parse.return_value = [{"start": "0:00:01", "end": "0:00:05", "text": "Test"}]
            mock_embed.return_value = mock_parse.return_value
            mock_store.return_value = None
            
            files = {
                "file": ("test.srt", io.BytesIO(b"1\n00:00:01,000 --> 00:00:05,000\nTest\n"), "text/plain")
            }
            
            start_time = time.time()
            response = client.post("/upload-transcript", files=files)
            end_time = time.time()
            
            # Should complete even with slow LLM
            assert response.status_code == 200
            # Verify that the LLM was called (OpenAI API call)
            mock_openai.assert_called_once()

    def test_malformed_llm_response(self):
        """Test handling of malformed LLM responses"""
        with patch('main.openai.chat.completions.create') as mock_openai, \
             patch('main.parse_srt') as mock_parse, \
             patch('main.embed_and_tag_chunks') as mock_embed, \
             patch('main.store_chunks') as mock_store, \
             patch('builtins.open'):
            
            # Mock malformed JSON response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "This is not valid JSON {malformed"
            mock_openai.return_value = mock_response
            
            mock_parse.return_value = [{"start": "0:00:01", "end": "0:00:05", "text": "Test"}]
            mock_embed.return_value = [{"start": "0:00:01", "end": "0:00:05", "text": "Test"}]
            mock_store.return_value = None
            
            files = {
                "file": ("test.srt", io.BytesIO(b"1\n00:00:01,000 --> 00:00:05,000\nTest\n"), "text/plain")
            }
            
            response = client.post("/upload-transcript", files=files)
            
            # Should handle malformed response gracefully
            assert response.status_code == 200

    def test_missing_transcript_prompt_file(self):
        """Test behavior when transcript processing prompt file is missing"""
        with patch('main.parse_srt') as mock_parse, \
             patch('main.embed_and_tag_chunks') as mock_embed, \
             patch('main.store_chunks') as mock_store, \
             patch('builtins.open', side_effect=FileNotFoundError("Prompt file not found")):
            
            mock_parse.return_value = [{"start": "0:00:01", "end": "0:00:05", "text": "Test"}]
            
            files = {
                "file": ("test.srt", io.BytesIO(b"1\n00:00:01,000 --> 00:00:05,000\nTest\n"), "text/plain")
            }
            
            with pytest.raises(FileNotFoundError):
                response = client.post("/upload-transcript", files=files)

    def test_invalid_category_values(self):
        """Test handling of invalid category values"""
        with patch('main.parse_srt') as mock_parse, \
             patch('main.process_transcript_with_llm') as mock_llm, \
             patch('main.embed_and_tag_chunks') as mock_embed, \
             patch('main.store_chunks') as mock_store, \
             patch('builtins.open'):
            
            mock_parse.return_value = [{"start": "0:00:01", "end": "0:00:05", "text": "Test"}]
            mock_llm.return_value = {"global_tags": [], "chunks": mock_parse.return_value}
            mock_embed.return_value = mock_llm.return_value["chunks"]
            mock_store.return_value = None
            
            files = {
                "file": ("test.srt", io.BytesIO(b"1\n00:00:01,000 --> 00:00:05,000\nTest\n"), "text/plain")
            }
            
            # Test with invalid category (not in SATSANG_CATEGORIES)
            data = {"category": "InvalidCategory"}
            
            response = client.post("/upload-transcript", files=files, data=data)
            
            # Should accept any category (validation might be handled elsewhere)
            assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
