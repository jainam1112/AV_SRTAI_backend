from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from srt_processor import parse_srt
from embedding import embed_and_tag_chunks
from quadrant_client import store_chunks, search_chunks, setup_collection, delete_transcript, list_transcripts, get_chunks_for_transcript
from entity_extraction import extract_entities_from_chunks
from bio_extraction import extract_bio_from_chunks
from models import UploadTranscriptResponse, SearchResponse, ErrorResponse, ChunkPayload, ValidationInfo
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

@app.get("/transcripts/{name}/chunks")
async def get_transcript_chunks(name: str):
    chunks = get_chunks_for_transcript(name)
    return success_response({"chunks": chunks})

# Management
@app.delete("/transcripts/{name}")
async def delete_transcript_endpoint(name: str):
    result = delete_transcript(name)
    return success_response({"deleted": result})

@app.get("/health")
async def health():
    return success_response({"status": "ok"})

@app.get("/collections/setup")
async def setup_collections():
    setup_collection()
    return success_response({"setup": "done"})

def process_transcript_with_llm(subtitles, prompt):
    import json
    input_json = json.dumps(subtitles, ensure_ascii=False)
    full_prompt = f"{prompt}\n\nINPUT:\n{input_json}\n\nOUTPUT:"

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for transcript chunking."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.2,
        max_tokens=4096
    )
    output_text = response.choices[0].message.content.strip()
    try:
        result = json.loads(output_text)
    except Exception:
        result = {"raw_output": output_text}
    return result
