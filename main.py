from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from srt_processor import parse_srt
from embedding import embed_and_tag_chunks, get_embedding
from quadrant_client import store_chunks, search_chunks, setup_collection, delete_transcript, list_transcripts, get_chunks_for_transcript, update_chunk_payload, update_chunk_with_bio_data, update_chunk_with_entity_data, scroll_all
from text_splitter import split_subtitles_into_chunks_with_timestamps 
from entity_extraction import extract_entities_from_chunks, get_entity_statistics
from bio_extraction import extract_bio_from_chunks
from models import UploadTranscriptResponse, SearchResponse, ErrorResponse, ChunkPayload, ValidationInfo, BioExtractionRequest, BioExtractionResponse, EntityExtractionRequest, EntityExtractionResponse
from constants import SATSANG_CATEGORIES, LOCATIONS, SPEAKERS, BIOGRAPHICAL_CATEGORY_KEYS
from utils import error_response, success_response
from validation_utils import validate_chunk_coverage, print_validation_summary
import os
import json
import tempfile
from datetime import datetime
from dotenv import load_dotenv
import openai


# Load environment variables
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Internal Helper Function for Chunk Enrichment ---
# In main.py

def enrich_chunk_with_llm(text_chunk: str):
    """
    Takes a single text chunk and calls an LLM to get conceptual tags.
    Summarization has been removed from this process.
    """
    model_name = os.getenv("ANSWER_EXTRACTION_MODEL", "gpt-3.5-turbo")
    
    # --- MODIFIED PROMPT: Only asks for tags ---
    prompt = f"""
    You are an expert in analyzing spiritual and philosophical content.
    For the following text chunk, provide up to 3 relevant conceptual tags.

    TEXT CHUNK:
    "{text_chunk}"

    Your response must be a valid JSON object with a single key "tags", which is a list of strings.
    Example:
    {{
      "tags": ["mindfulness", "self-reflection", "practice"]
    }}
    """
    
    try:
        response = openai.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides conceptual tags for text chunks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        output_text = response.choices[0].message.content.strip()
        return json.loads(output_text)
    except Exception as e:
        print(f"Warning: Could not enrich chunk with LLM. Error: {e}")
        # --- MODIFIED FALLBACK: Only returns tags ---
        return {"tags": []}
    
# Document Processing
@app.post("/upload-transcript")
async def upload_transcript(
    file: UploadFile = File(...),  # Define the file parameter correctly
    category: str = Form(default="Miscellaneous"),
    location: str = Form(default="Unknown"),
    speaker: str = Form(default="Gurudev"),
    satsang_name: str = Form(default=""),
    satsang_code: str = Form(default=""),
    misc_tags: str = Form(default=""),
    date: str = Form(default="")
):
    try:
        # Read the file content
        content = await file.read()
        text = content.decode("utf-8")  # Ensure the file is UTF-8 encoded

        # Parse subtitles
        subtitles = parse_srt(text)
        print(f"Subtitles: {subtitles}")  # Debug: Print parsed subtitles

        # Perform timestamp-aware chunking
        chunks = split_subtitles_into_chunks_with_timestamps(
            subtitles=subtitles,
            chunk_size=400,  # Adjust chunk size as needed
            chunk_overlap=75  # Adjust overlap as needed
        )
        print(f"Chunks created: {chunks}")  # Debug: Print created chunks

        # Enrich each chunk with metadata
        enriched_chunks = []
        transcript_name = satsang_name or file.filename.rsplit('.', 1)[0]
        date_str = date or datetime.now().strftime('%Y-%m-%d')
        tags_list = [t.strip() for t in misc_tags.split(",") if t.strip()]

        for i, chunk in enumerate(chunks):
            chunk_text = chunk["text"]
            enrichment_data = enrich_chunk_with_llm(chunk_text)
            embedding_vector = get_embedding(chunk_text)

            if not embedding_vector:
                print(f"Warning: Skipping chunk {i+1} due to failed embedding generation.")
                continue

            # Prepare the final payload for this chunk
            chunk_payload = {
                "transcript_name": transcript_name,
                "satsang_name": satsang_name,
                "text": chunk_text,
                "start_time": chunk["start"],  # Include start timestamp
                "end_time": chunk["end"],      # Include end timestamp
                "summary": enrichment_data.get("summary", ""),
                "tags": enrichment_data.get("tags", []),
                "date": date_str,
                "category": category,
                "location": location,
                "speaker": speaker,
                "misc_tags": tags_list
            }

            enriched_chunks.append({
                "embedding": embedding_vector,
                "payload": chunk_payload
            })

        # Store the final list of enriched chunks in Qdrant
        chunks_uploaded_count = store_chunks(enriched_chunks)

        # Return a simplified success response
        return {
            "status": "success",
            "message": f"Successfully processed and stored {chunks_uploaded_count} chunks.",
            "chunks_uploaded": chunks_uploaded_count
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing transcript: {str(e)}")
    

@app.post("/transcripts/{transcript_name}/extract-entities", response_model=EntityExtractionResponse)
async def extract_entities(
    transcript_name: str,
    request: EntityExtractionRequest = None
):
    """
    Extract entities from all chunks of a specific transcript.
    This will update the chunks in Qdrant with entity extractions.
    """
    try:
        # Get parameters from request
        use_ai = True
        include_statistics = True
        if request:
            use_ai = request.use_ai if request.use_ai is not None else True
            include_statistics = request.include_statistics if request.include_statistics is not None else True
        
        # Get all chunks for the transcript
        print(f"Retrieving chunks for transcript: {transcript_name}")
        chunks = get_chunks_for_transcript(transcript_name)
        
        if not chunks:
            raise HTTPException(
                status_code=404, 
                detail=f"No chunks found for transcript '{transcript_name}'"
            )
        
        print(f"Found {len(chunks)} chunks for '{transcript_name}'")
        
        # Extract entities from chunks
        entity_results = extract_entities_from_chunks(
            chunks=chunks,
            transcript_name=transcript_name,
            use_ai=use_ai
        )
        
        # Count successful extractions and update Qdrant
        chunks_updated = 0
        method_used = "AI" if use_ai else "rule-based"
        
        for i, (chunk, entity_result) in enumerate(zip(chunks, entity_results)):
            if entity_result:
                # Update the chunk in Qdrant with entity data
                point_id = chunk.get('id')
                if point_id:
                    success = update_chunk_with_entity_data(point_id, entity_result)
                    if success:
                        chunks_updated += 1
                        print(f"✅ Updated chunk {i+1}/{len(chunks)} with entity data")
                    else:
                        print(f"❌ Failed to update chunk {i+1}/{len(chunks)} in Qdrant")
                else:
                    print(f"⚠️ Chunk {i+1}/{len(chunks)} missing point ID, skipping Qdrant update")
            else:
                print(f"⚠️ Chunk {i+1}/{len(chunks)} has no entity data, skipping")
        
        # Calculate statistics if requested
        entity_statistics = None
        if include_statistics:
            entity_statistics = get_entity_statistics(entity_results)
        
        return EntityExtractionResponse(
            status="success",
            transcript_name=transcript_name,
            chunks_processed=len(chunks),
            chunks_updated=chunks_updated,
            method_used=method_used,
            entity_statistics=entity_statistics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during entity extraction: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error extracting entities: {str(e)}"
        )

@app.post("/extract-bio/{name}")
async def extract_bio(name: str):
    chunks = get_chunks_for_transcript(name)
    bio = extract_bio_from_chunks(chunks, name)
    # Update DB with bio info (not implemented)
    return success_response({"biographical_extractions": bio})

# Search & Retrieval
@app.post("/search")
async def search(query: dict):
    search_text = query.get("query", "")
    results = search_chunks(search_text)
    chunks = results.get("result", results)
    # Simplify output
    simplified_chunks = [
        {
            "id": chunk.get("id"),
            "score": chunk.get("score"),
            "transcript_name": chunk["payload"].get("transcript_name"),
            "timestamp": chunk["payload"].get("timestamp"),
            "text": chunk["payload"].get("original_text") or chunk["payload"].get("text")
        }
        for chunk in chunks
    ]
    return {"chunks": simplified_chunks, "total": len(simplified_chunks)}

@app.post("/search-transcripts")
async def search_transcripts(query: dict):
    search_text = query.get("query", "")
    results = search_chunks(search_text)
    transcript_names = set()
    for chunk in results.get("result", []):
        payload = chunk.get("payload", {})
        name = payload.get("transcript_name") or payload.get("satsang_name")
        if name:
            transcript_names.add(name)
    return {"transcripts": list(transcript_names)}

@app.get("/transcripts")
async def get_transcripts():
    transcripts = list_transcripts()
    return success_response({"transcripts": transcripts})

@app.get("/transcripts/{transcript_name}/chunks")
def get_transcript_chunks(transcript_name: str = Path(..., description="The URL-encoded name of the transcript")):
    """
    Retrieves all chunks for a specific transcript from the database.
    """
    try:
        # This calls the function you've already defined in quadrant_client.py
        chunks = get_chunks_for_transcript(name=transcript_name)
        
        if not chunks:
            # It's not an error if no chunks are found, just return an empty list.
            print(f"No chunks found for transcript: '{transcript_name}'")
        
        # The frontend expects the data in a dictionary with a "chunks" key.
        return {"chunks": chunks}
        
    except Exception as e:
        print(f"Error retrieving chunks for '{transcript_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chunks for transcript.")

from pydantic import BaseModel
from typing import List, Optional

# --- DEFINE THE PYDANTIC MODELS FOR THIS ENDPOINT ---
# (It's good practice to have these defined in one place, like near the top of the file)
class TranscriptStatus(BaseModel):
    transcript_name: str
    is_bio_extracted: bool

class AllTranscriptsStatusResponse(BaseModel):
    transcripts: List[TranscriptStatus]


# --- THIS IS THE MISSING ENDPOINT ---
@app.get("/transcripts/status", response_model=AllTranscriptsStatusResponse)
def get_all_transcripts_status():
    """
    Fetches all unique transcript names and indicates whether their
    bio-extraction is complete.
    """
    try:
        # Call the helper function from your quadrant_client
        all_points = scroll_all()
        
        all_transcripts = {}
        for point in all_points:
            payload = point.get("payload", {})
            # Use 'satsang_name' or 'transcript_name' depending on what you store
            name = payload.get("satsang_name") or payload.get("transcript_name")
            
            if name:
                if name not in all_transcripts:
                    all_transcripts[name] = {"total": 0, "with_bio": 0}
                all_transcripts[name]["total"] += 1
                # Check for the key that your bio_extraction process adds to the payload
                if payload.get("biographical_extractions"):
                    all_transcripts[name]["with_bio"] += 1
        
        status_list = []
        for name, counts in all_transcripts.items():
            # A transcript is fully extracted if all its chunks have the bio data
            is_complete = counts["with_bio"] >= counts["total"] and counts["total"] > 0
            status_list.append(
                TranscriptStatus(
                    transcript_name=name,
                    is_bio_extracted=is_complete
                )
            )
            
        return {"transcripts": sorted(status_list, key=lambda x: x.transcript_name)}

    except Exception as e:
        print(f"Error fetching all transcripts status: {e}")
        # Return a 500 error if something goes wrong
        raise HTTPException(status_code=500, detail="Could not retrieve transcript statuses from database")
# Management
@app.delete("/transcripts/{name}")
async def delete_transcript_endpoint(name: str):
    result = delete_transcript(name)
    return success_response({"deleted": result})

@app.get("/health")
async def health():
    return success_response({"status": "ok"})


# --- THIS IS THE NEW ENDPOINT ---

@app.get("/chunks/all")
def get_all_chunks():
    """
    Retrieves ALL chunks from the Qdrant collection using the scroll API.
    Warning: This can be a large and slow request if you have many chunks.
    """
    try:
        # This calls the helper function from your quadrant_client.py file
        all_chunks = scroll_all()
        
        # The frontend expects the data to be in a dictionary with a "chunks" key
        return {"chunks": all_chunks}
        
    except Exception as e:
        print(f"Error retrieving all chunks: {e}")
        # If something goes wrong, return a 500 Internal Server Error
        raise HTTPException(status_code=500, detail="Failed to retrieve all chunks from the database.")

@app.get("/collections/setup")
async def setup_collections():
    setup_collection()
    return success_response({"setup": "done"})

@app.post("/transcripts/{transcript_name}/extract-bio", response_model=BioExtractionResponse)
async def extract_biographical_info(
    transcript_name: str,
    request: BioExtractionRequest = None
):
    """
    Extract biographical information from all chunks of a specific transcript.
    This will update the chunks in Qdrant with biographical extractions.
    """
    try:
        # Get the fine-tuned model ID from request or environment
        ft_model_id = None
        if request and request.ft_model_id:
            ft_model_id = request.ft_model_id
        
        # Get all chunks for the transcript
        print(f"Retrieving chunks for transcript: {transcript_name}")
        chunks = get_chunks_for_transcript(transcript_name)
        
        if not chunks:
            raise HTTPException(
                status_code=404, 
                detail=f"No chunks found for transcript '{transcript_name}'"
            )
        
        print(f"Found {len(chunks)} chunks for '{transcript_name}'")
        
        # Extract biographical information from chunks
        bio_results = extract_bio_from_chunks(
            chunks=chunks,
            transcript_name=transcript_name,
            ft_model_id=ft_model_id
        )
        
        # Count successful extractions and update Qdrant
        chunks_updated = 0
        extraction_summary = {}
        model_used = ft_model_id or os.getenv("FINE_TUNED_BIO_MODEL") or os.getenv("ANSWER_EXTRACTION_MODEL", "gpt-3.5-turbo")
        
        for i, (chunk, bio_result) in enumerate(zip(chunks, bio_results)):
            if bio_result and 'biographical_extractions' in bio_result:
                # Update the chunk in Qdrant with biographical data merged into payload
                point_id = chunk.get('id')
                if point_id:
                    success = update_chunk_with_bio_data(point_id, bio_result)
                    if success:
                        chunks_updated += 1
                        
                        # Count extractions by category
                        bio_data = bio_result.get('biographical_extractions', {})
                        for category, quotes in bio_data.items():
                            if quotes:  # Only count non-empty categories
                                extraction_summary[category] = extraction_summary.get(category, 0) + 1
                        
                        print(f"✅ Updated chunk {i+1}/{len(chunks)} with bio data")
                    else:
                        print(f"❌ Failed to update chunk {i+1}/{len(chunks)} in Qdrant")
                else:
                    print(f"⚠️ Chunk {i+1}/{len(chunks)} missing point ID, skipping Qdrant update")
            else:
                print(f"⚠️ Chunk {i+1}/{len(chunks)} has no bio extraction data, skipping")
                
                print(f"Processed chunk {i+1}/{len(chunks)}")
        
        return BioExtractionResponse(
            status="success",
            transcript_name=transcript_name,
            chunks_processed=len(chunks),
            chunks_updated=chunks_updated,
            model_used=model_used,
            extraction_summary=extraction_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during biographical extraction: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error extracting biographical information: {str(e)}"
        )

@app.get("/transcripts/{transcript_name}/bio-status")
async def get_bio_extraction_status(transcript_name: str):
    """Check biographical extraction status for a transcript"""
    try:
        chunks = get_chunks_for_transcript(transcript_name)
        
        if not chunks:
            raise HTTPException(
                status_code=404,
                detail=f"No chunks found for transcript '{transcript_name}'"
            )
        
        # Analyze bio extraction status
        total_chunks = len(chunks)
        chunks_with_bio = 0
        category_counts = {}
        
        for chunk in chunks:
            if chunk.get('biographical_extractions'):
                chunks_with_bio += 1
                
                # Count categories
                bio_data = chunk.get('biographical_extractions', {})
                for category, quotes in bio_data.items():
                    if quotes:  # Only count non-empty categories
                        category_counts[category] = category_counts.get(category, 0) + 1
        
        return success_response({
            "transcript_name": transcript_name,
            "total_chunks": total_chunks,
            "chunks_with_bio": chunks_with_bio,
            "bio_coverage_percentage": round((chunks_with_bio / total_chunks) * 100, 1) if total_chunks > 0 else 0,
            "category_summary": category_counts,
            "needs_extraction": chunks_with_bio < total_chunks
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error checking bio status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error checking biographical status: {str(e)}"
        )

