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

# In quadrant_client.py

# In quadrant_client.py

def get_chunks_for_transcript(name: str):
    """
    Fetches ALL chunks for a specific transcript from Qdrant by handling pagination.
    Returns data in the standard Point format: {"id": "...", "payload": {...}}
    """
    if not all([QDRANT_HOST, QDRANT_API_KEY, COLLECTION_NAME]):
        print("Warning: Qdrant not configured")
        return []
    
    headers = {"Content-Type": "application/json", "api-key": QDRANT_API_KEY}
    scroll_url = f"https://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points/scroll"
    
    # --- THIS IS THE CRITICAL FIX ---
    # The filter key is changed back to "transcript_name" to match what is in your data.
    scroll_filter = {
        "must": [
            {
                "key": "transcript_name", # <-- CORRECTED KEY
                "match": {
                    "value": name
                }
            }
        ]
    }

    all_points = []
    next_page_offset = None

    print(f"Scrolling for chunks with transcript_name: '{name}'")

    while True:
        payload = {
            "filter": scroll_filter,
            "limit": 250,
            "with_payload": True,
            "with_vectors": False
        }
        if next_page_offset:
            payload["offset"] = next_page_offset
        
        try:
            response = requests.post(scroll_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json().get("result", {})
            points_on_page = result.get("points", [])
            
            if not points_on_page:
                break
            
            # This part is correct: extend the list with the raw point objects.
            all_points.extend(points_on_page)
            
            next_page_offset = result.get("next_page_offset")
            if not next_page_offset:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving chunks for transcript '{name}': {e}")
            if e.response:
                print(f"Qdrant Error Body: {e.response.text}")
            return [] # Return empty list on error
            
    print(f"✅ Found a total of {len(all_points)} chunks for '{name}'.")
    return all_points

def update_chunk_payload(point_id, payload_update):
    """Update a specific chunk's payload in Qdrant using set operation for partial updates"""
    if not QDRANT_API_URL:
        print("Warning: Qdrant not configured")
        return False
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {QDRANT_API_KEY}"
    }
    
    # Use the set payload endpoint for partial updates
    payload_url = f"https://{QDRANT_HOST}:{QDRANT_PORT}/collections/{COLLECTION_NAME}/points/payload"
    
    # Use POST with "set" operation for partial update
    payload = {
        "payload": payload_update,
        "points": [point_id]
    }
    
    try:
        # Use POST for set operation (partial update)
        response = requests.post(payload_url, json=payload, headers=headers)
        response.raise_for_status()
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"Error updating payload for point {point_id}: {e}")
        return False

def update_chunk_with_bio_data(point_id, bio_extraction, chunk_payload=None):
    """
    Update a chunk's payload with biographical extraction data.
    This merges bio data into the existing payload structure.
    
    Args:
        point_id: The Qdrant point ID
        bio_extraction: Dictionary containing biographical_extractions and has_{category} flags
        chunk_payload: Optional current payload to merge with (if not provided, will fetch from Qdrant)
    
    Returns:
        bool: Success status
    """
    if not QDRANT_API_URL:
        print("Warning: Qdrant not configured")
        return False
    
    from constants import BIOGRAPHICAL_CATEGORY_KEYS
    
    # If no current payload provided, we'll do a partial update
    if chunk_payload is None:
        # Clean bio data - only include categories with content
        bio_data = bio_extraction.get("biographical_extractions", {})
        cleaned_bio_data = {cat: quotes for cat, quotes in bio_data.items() if quotes}
        
        # Just update the bio-related fields
        payload_update = {
            "biographical_extractions": cleaned_bio_data,
        }
        
        # Create bio_tags array from categories that have data (non-empty arrays)
        bio_tags = list(cleaned_bio_data.keys())
        payload_update["bio_tags"] = bio_tags
        
    else:
        # Merge with existing payload
        payload_update = chunk_payload.copy()
        
        # Clean bio data - only include categories with content
        bio_data = bio_extraction.get("biographical_extractions", {})
        cleaned_bio_data = {cat: quotes for cat, quotes in bio_data.items() if quotes}
        
        payload_update["biographical_extractions"] = cleaned_bio_data
        
        # Create bio_tags array from categories that have data (non-empty arrays)
        bio_tags = list(cleaned_bio_data.keys())
        payload_update["bio_tags"] = bio_tags
    
    return update_chunk_payload(point_id, payload_update)

def update_chunk_with_entity_data(point_id, entity_extraction, chunk_payload=None):
    """
    Update a chunk's payload with entity extraction data.
    This merges entity data into the existing payload structure.
    
    Args:
        point_id: The Qdrant point ID
        entity_extraction: Dictionary containing extracted entities
        chunk_payload: Optional current payload to merge with (if not provided, will fetch from Qdrant)
    
    Returns:
        bool: Success status
    """
    if not QDRANT_API_URL:
        print("Warning: Qdrant not configured")
        return False
    
    # Clean entity data - only include categories with content
    cleaned_entities = {}
    for category, data in entity_extraction.items():
        if category == "self_references":
            # Always include boolean field
            cleaned_entities[category] = bool(data)
        elif isinstance(data, list) and data:
            # Only include non-empty lists
            cleaned_entities[category] = data
    
    # Create entity_tags array from categories that have data
    entity_tags = []
    for category, data in cleaned_entities.items():
        if category == "self_references" and data:
            entity_tags.append("self_references")
        elif isinstance(data, list) and data:
            entity_tags.append(category)
    
    # Just update the entity-related fields
    payload_update = {
        "entities": cleaned_entities,
        "entity_tags": entity_tags
    }
    
    return update_chunk_payload(point_id, payload_update)

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

def qdrant_url(path):
    """Helper function to construct the full Qdrant URL."""
    return f"https://{QDRANT_HOST}:{QDRANT_PORT}{path}"

# --- THIS IS THE FUNCTION YOU ASKED FOR ---

def scroll_all(collection_name: str = None):
    """
    Scrolls through and retrieves ALL points (chunks) from a Qdrant collection.
    This function handles pagination automatically.

    Args:
        collection_name (str, optional): The name of the collection to scroll. 
                                         Defaults to COLLECTION_NAME from .env.

    Returns:
        A list of all point dictionaries found in the collection.
    """
    target_collection = collection_name or COLLECTION_NAME
    if not all([QDRANT_HOST, QDRANT_API_KEY, target_collection]):
        print("Qdrant not configured, cannot scroll.")
        return []

    headers = {"Content-Type": "application/json", "api-key": QDRANT_API_KEY}

    scroll_url = qdrant_url(f"/collections/AV_srt_recognization/points/scroll")
    
    all_points = []
    # This offset will be updated with the value from the API response to get the next page
    next_page_offset = None

    print(f"Starting to scroll all chunks from collection '{target_collection}'...")

    while True:
        # Prepare the request body for the current page
        payload = {
            "limit": 250,           # Fetch 250 points per API call (a good balance)
            "with_payload": True,   # We need the metadata (text, tags, etc.)
            "with_vectors": False   # We don't need the large vector data for this
        }
        
        # If we have an offset from the previous page, add it to the request
        if next_page_offset:
            payload["offset"] = next_page_offset
        
        try:
            response = requests.post(scroll_url, json=payload, headers=headers)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
            result = response.json().get("result", {})
            points_on_page = result.get("points", [])
            
            if not points_on_page:
                # This can happen if the last page was exactly the limit size
                break
                
            all_points.extend(points_on_page)

            # Check if there is a next page
            next_page_offset = result.get("next_page_offset")
            if not next_page_offset:
                # This was the last page, so we exit the loop
                break
            
            print(f"Fetched {len(all_points)} points so far, getting next page...")
        
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while scrolling: {e}")
            if e.response:
                print(f"Error Body: {e.response.text}")
            break # Exit the loop on an error

    print(f"✅ Finished scrolling. Total chunks retrieved: {len(all_points)}")
    return all_points