import os
import requests
from embedding import get_embedding
from dotenv import load_dotenv
import pprint
import uuid  # <-- STEP 1: Import the UUID library

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


import os
import requests
from embedding import get_embedding
from dotenv import load_dotenv
import pprint
import uuid  # <-- STEP 1: Import the UUID library

# ... (rest of your script setup) ...

def store_chunks(chunks):
    """Store chunks in Qdrant vector database using UUIDs for IDs."""
    if not QDRANT_API_URL:
        print("Warning: Qdrant not configured, skipping storage")
        return
    
    if not chunks:
        print("No chunks to store")
        return
    
    payload = {
        "points": []
    }
    for chunk in chunks: # No longer need the index 'idx'
        # --- STEP 2: Generate a unique UUID for each point ---
        # str() converts the UUID object to the string format Qdrant expects.
        point_id = str(uuid.uuid4())
        
        payload["points"].append({
            "id": point_id,
            "vector": chunk["embedding"],
            "payload": chunk.get("payload", {})
        })

    # Debug print statements
    print("=== Qdrant Chunks Payload Preview ===")
    print("!!! DEBUG: Sending", len(payload["points"]), "points.")
    print("!!! DEBUG: First point ID:", payload["points"][0]["id"])
    print("!!! DEBUG: Vector dimension being sent is:", len(payload["points"][0]["vector"]))

    headers = {
        "Content-Type": "application/json",
        "api-key": QDRANT_API_KEY
    }
    
    try:
        # Using .put is correct for upserting
        response = requests.put(QDRANT_API_URL, json=payload, headers=headers)
        
        if response.status_code >= 400:
             print(f"!!! QDRANT ERROR BODY: {response.text}")

        response.raise_for_status()
        print(f"✅ Successfully stored {len(payload['points'])} chunks to Qdrant!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error storing chunks to Qdrant: {e}")

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
    """Get all chunks for a transcript from Qdrant"""
    if not QDRANT_API_URL:
        print("Warning: Qdrant not configured")
        return []
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {QDRANT_API_KEY}"
    }
    
    # Use scroll to get all points for the transcript
    scroll_url = f"https://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points/scroll"
    
    payload = {
        "filter": {
            "must": [
                {
                    "key": "transcript_name",
                    "match": {
                        "value": name
                    }
                }
            ]
        },
        "limit": 100,  # Adjust as needed
        "with_payload": True,
        "with_vectors": False
    }
    
    try:
        response = requests.post(scroll_url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        points = result.get("result", {}).get("points", [])
        
        chunks = []
        for point in points:
            chunk_data = point.get("payload", {})
            chunk_data["id"] = point.get("id")
            chunks.append(chunk_data)
        
        return chunks
    
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving chunks for transcript '{name}': {e}")
        return []


def update_chunk_payload(point_id, payload_update):
    """Update a specific chunk's payload in Qdrant"""
    if not QDRANT_API_URL:
        print("Warning: Qdrant not configured")
        return False
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {QDRANT_API_KEY}"
    }
    
    # Set payload for specific points
    payload_url = f"https://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points/payload"
    
    payload = {
        "payload": payload_update,
        "points": [point_id]
    }
    
    try:
        response = requests.put(payload_url, json=payload, headers=headers)
        response.raise_for_status()
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"Error updating payload for point {point_id}: {e}")
        return False

def search_chunks(query_text, limit=10):
    # Get embedding for the search query
    query_embedding = get_embedding(query_text)
    
    payload = {
        "vector": query_embedding,
        "limit": limit,
        "with_payload": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "api-key": QDRANT_API_KEY
    }
    
    search_url = f"https://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points/search"
    response = requests.post(search_url, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()
