from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from srt_processor import parse_srt
from embedding import embed_and_tag_chunks
from quadrant_client import store_chunks, search_chunks, setup_collection, delete_transcript, list_transcripts, get_chunks_for_transcript, update_chunk_payload, scroll_all
from entity_extraction import extract_entities_from_chunks
from bio_extraction import extract_bio_from_chunks
from models import UploadTranscriptResponse, SearchResponse, ErrorResponse, ChunkPayload, ValidationInfo, BioExtractionRequest, BioExtractionResponse
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

# Document Processing
@app.post("/upload-transcript", response_model=UploadTranscriptResponse)
async def upload_transcript(
    file: UploadFile = File(...),
    category: str = Form(default="Miscellaneous"),
    location: str = Form(default="Unknown"),
    speaker: str = Form(default="Gurudev"),
    satsang_name: str = Form(default=""),
    satsang_code: str = Form(default=""),
    misc_tags: str = Form(default=""),  # Comma-separated string
    date: str = Form(default="")  # Date in YYYY-MM-DD format, defaults to today
):

    # 1. Validate file type and encoding
    if not file.filename.endswith('.srt'):
        raise HTTPException(status_code=400, detail="Only .srt files are supported.")
    try:
        content = await file.read()
        text = content.decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    # 2. Parse SRT
    chunks = parse_srt(text)
    transcript_name = file.filename.rsplit('.', 1)[0]

    # 3. Prepare subtitles for LLM prompt
    subtitles = [
        {"start": c["start"], "end": c["end"], "text": c["text"]}
        for c in chunks
    ]

    # 4. Load transcript processing prompt
    with open("transcript_processing_prompt", "r", encoding="utf-8") as f:
        prompt = f.read()

    # 5. Call LLM to get smart chunks, summaries, tags
    llm_result = process_transcript_with_llm(subtitles, prompt)
    print("Chunks from LLM:", llm_result.get("chunks"))  # <-- Add this line
    global_tags = llm_result.get("global_tags", [])
    processed_chunks = llm_result.get("chunks", [])

    # 6. Add metadata to each chunk
    if date:
        # Use user-provided date
        date_str = date
    else:
        # Default to today's date
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    tags_list = [t.strip() for t in misc_tags.split(",") if t.strip()] if misc_tags else []
    for chunk in processed_chunks:
        chunk["transcript_name"] = transcript_name
        chunk["date"] = date_str
        chunk["category"] = category
        chunk["location"] = location
        chunk["speaker"] = speaker
        chunk["satsang_name"] = satsang_name
        chunk["satsang_code"] = satsang_code
        chunk["misc_tags"] = tags_list
        chunk["global_tags"] = global_tags

    # 7. Generate embeddings and tags
    enriched_chunks = embed_and_tag_chunks(processed_chunks)
    
    # 8. VALIDATION - Ensure all subtitles are covered
    print("\n🔍 Validating chunk coverage...")
    validation_report = validate_chunk_coverage(subtitles, processed_chunks)
    print_validation_summary(validation_report)
    
    # Check validation mode from environment variable
    validation_mode = os.getenv("VALIDATION_MODE", "warn")  # "strict", "warn", or "detailed"
    
    if validation_mode == "strict" and not validation_report["coverage_complete"]:
        print("❌ Strict validation mode: Upload failed due to validation errors")
        error_details = {
            "validation_failed": True,
            "errors": validation_report["errors"],
            "warnings": validation_report["warnings"],
            "text_coverage": validation_report["text_coverage_percentage"],
            "timeline_coverage": validation_report["timeline_coverage_percentage"],
            "missing_subtitles": len(validation_report["missing_subtitles"]),
            "detailed_report": validation_report["detailed_report"]
        }
        raise HTTPException(
            status_code=422, 
            detail=f"Transcript validation failed: {validation_report['errors']}"
        )
    elif not validation_report["coverage_complete"]:
        print("⚠️ Validation issues detected!")
        print(validation_report["detailed_report"])
        print("⚠️ Continuing with warnings - check temp file for details")
    else:
        print("✅ Validation passed - all subtitles covered!")

    # 9. Create Qdrant payloads (add has_{category} flags, etc.)
    from constants import BIOGRAPHICAL_CATEGORY_KEYS
    def create_payload(chunk):
        payload = {
            "original_text": chunk.get("text"),
            "timestamp": f"{chunk.get('start')} - {chunk.get('end')}",
            "transcript_name": chunk.get("transcript_name"),
            "date": chunk.get("date"),
            "category": chunk.get("category"),
            "location": chunk.get("location"),
            "speaker": chunk.get("speaker"),
            "satsang_name": chunk.get("satsang_name"),
            "satsang_code": chunk.get("satsang_code"),
            "misc_tags": chunk.get("misc_tags", []),
            "summary": chunk.get("summary", ""),
            "tags": chunk.get("tags", []),
            "global_tags": chunk.get("global_tags", []),
            "entities": chunk.get("entities", {}),
            "biographical_extractions": chunk.get("biographical_extractions", {}),
        }
        # Add has_{category} flags
        for cat in BIOGRAPHICAL_CATEGORY_KEYS:
            payload[f"has_{cat}"] = bool(chunk.get("biographical_extractions", {}).get(cat))
        return payload

    # 10. Store chunks in Qdrant
    qdrant_chunks = []
    for chunk in enriched_chunks:
        payload = create_payload(chunk)
        chunk["payload"] = payload
        qdrant_chunks.append(chunk)
    
    # 11. Save chunks and validation report to temporary file for debugging
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filename = f"chunks_{transcript_name}_{timestamp}.json"
    temp_filepath = os.path.join(temp_dir, temp_filename)
    
    try:
        # Create a simplified version for JSON serialization
        chunks_for_file = []
        for chunk in qdrant_chunks:
            chunk_copy = chunk.copy()
            # Remove the embedding vector as it's too large for text file
            if 'embedding' in chunk_copy:
                chunk_copy['embedding'] = f"[Vector of length {len(chunk_copy['embedding'])}]"
            chunks_for_file.append(chunk_copy)
        
        with open(temp_filepath, 'w', encoding='utf-8') as temp_file:
            json.dump({
                "transcript_info": {
                    "filename": file.filename,
                    "transcript_name": transcript_name,
                    "upload_time": datetime.now().isoformat(),
                    "metadata": {
                        "category": category,
                        "location": location,
                        "speaker": speaker,
                        "satsang_name": satsang_name,
                        "satsang_code": satsang_code,
                        "misc_tags": tags_list,
                        "date": date_str
                    },
                    "total_chunks": len(chunks_for_file)
                },
                "validation_report": validation_report,
                "chunks": chunks_for_file
            }, temp_file, indent=2, ensure_ascii=False)
        
        print(f"✅ Chunks saved to temporary file: {temp_filepath}")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not save chunks to temp file: {str(e)}")
        # Continue execution even if temp file save fails
    
    store_chunks(qdrant_chunks)

    # 12. Prepare validation info for response
    validation_mode = os.getenv("VALIDATION_MODE", "warn")
    include_validation = validation_mode in ["detailed", "strict"] or not validation_report["coverage_complete"]
    
    validation_info = None
    if include_validation:
        validation_info = ValidationInfo(
            coverage_complete=validation_report["coverage_complete"],
            text_coverage_percentage=validation_report["text_coverage_percentage"],
            timeline_coverage_percentage=validation_report["timeline_coverage_percentage"],
            missing_subtitles_count=len(validation_report["missing_subtitles"]),
            timeline_gaps_count=len(validation_report["gaps_in_timeline"]),
            overlapping_chunks_count=len(validation_report["overlapping_chunks"]),
            errors=validation_report["errors"],
            warnings=validation_report["warnings"],
            detailed_report=validation_report["detailed_report"] if validation_mode == "detailed" else None
        )

    return UploadTranscriptResponse(
        status="success", 
        chunks_uploaded=len(qdrant_chunks),
        validation=validation_info
    )

@app.post("/process-entities/{name}")
async def process_entities(name: str):
    # Dummy: fetch chunks, extract entities, update DB
    chunks = get_chunks_for_transcript(name)
    entities = extract_entities_from_chunks(chunks, name)
    # Update DB with entities (not implemented)
    return success_response({"entities": entities})

@app.post("/extract-bio/{name}")
async def extract_bio(name: str):
    chunks = get_chunks_for_transcript(name)
    bio = extract_bio_from_chunks(chunks, name)
    # Update DB with bio info (not implemented)
    return success_response({"biographical_extractions": bio})

# Search & Retrieval
@app.post("/search", response_model=SearchResponse)
async def search(query: dict):
    search_text = query.get("query", "")
    results = search_chunks(search_text)
    return SearchResponse(results=results, total=len(results), page=1, page_size=len(results))

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
                # Update the chunk in Qdrant with biographical data
                point_id = chunk.get('id')
                if point_id:
                    success = update_chunk_payload(point_id, bio_result)
                    if success:
                        chunks_updated += 1
                        
                        # Count extractions by category
                        bio_data = bio_result.get('biographical_extractions', {})
                        for category, quotes in bio_data.items():
                            if quotes:  # Only count non-empty categories
                                extraction_summary[category] = extraction_summary.get(category, 0) + 1
                
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

def process_transcript_with_llm(subtitles, prompt):
    import json
    import os

    input_json = json.dumps(subtitles, ensure_ascii=False)
    full_prompt = f"{prompt}\n\nINPUT:\n{input_json}\n\nOUTPUT:"

    model_name = os.getenv("ANSWER_EXTRACTION_MODEL", "gpt-4o")

    response = openai.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant for transcript chunking."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.2,
        max_tokens=16384
    )
    output_text = response.choices[0].message.content.strip()
    print("=== LLM Raw Output ===")
    print(output_text)

    # Fallback: Remove markdown code block if present
    if output_text.startswith("```"):
        output_text = output_text.split("```")[1]
        if output_text.strip().startswith("json"):
            output_text = output_text.strip()[4:]
        output_text = output_text.strip()

    try:
        result = json.loads(output_text)
    except Exception:
        result = {"raw_output": output_text}
    ##print("=== Parsed Chunks ===")
    ##print(result.get("chunks"))
    return result
