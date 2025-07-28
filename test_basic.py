import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import io

# Simple test to verify setup
def test_imports():
    """Test that basic imports work"""
    try:
        from main import app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        assert client is not None
        print("✓ Basic imports successful")
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_basic_health_endpoint():
    """Test the health endpoint to verify API is working"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] == True
    assert response_data["data"]["status"] == "ok"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
