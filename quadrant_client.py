import os
import requests
from embedding import get_embedding
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build Qdrant URL from host and port
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip('"')  # Remove quotes if present
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# Construct the full Qdrant URL
if QDRANT_HOST:
    QDRANT_API_URL = f"https://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points"
else:
    QDRANT_API_URL = None
    print("Warning: QDRANT_HOST not found in environment variables")


def store_chunks(chunks):
    """Store chunks in Qdrant vector database"""
    if not QDRANT_API_URL:
        print("Warning: Qdrant not configured, skipping storage")
        return
    
    if not chunks:
        print("No chunks to store")
        return
    
    payload = {
        "collection": COLLECTION_NAME,
        "points": []
    }
    for idx, chunk in enumerate(chunks):
        payload["points"].append({
            "id": f"chunk-{idx}",
            "vector": chunk["embedding"],
            "payload": chunk.get("payload", {})
        })
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {QDRANT_API_KEY}"
    }
    
    try:
        response = requests.post(QDRANT_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Successfully stored {len(chunks)} chunks to Qdrant")
    except requests.exceptions.RequestException as e:
        print(f"Error storing chunks to Qdrant: {e}")
        # Don't raise the error, just log it so the upload can continue

def setup_collection():
    # Stub: Setup Qdrant collection (vector size, distance, payload indexes)
    # Implement actual Qdrant API call here
    return True

def delete_transcript(name):
    # Stub: Delete all points for a transcript
    # Implement actual Qdrant API call here
    return True

def list_transcripts():
    # Stub: List all transcript names
    # Implement actual Qdrant API call here
    return ["sample_transcript"]

def get_chunks_for_transcript(name):
    # Stub: Get all chunks for a transcript
    # Implement actual Qdrant API call here
    return []

def search_chunks(query_text, limit=10):
    # Get embedding for the search query
    query_embedding = get_embedding(query_text)
    
    payload = {
        "collection": COLLECTION_NAME,
        "vector": query_embedding,
        "limit": limit,
        "with_payload": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {QDRANT_API_KEY}"
    }
    
    search_url = f"https://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points/search"
    response = requests.post(search_url, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()
