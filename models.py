from pydantic import BaseModel
from typing import List, Dict, Optional

class Entities(BaseModel):
    people: Optional[List[str]] = None
    places: Optional[List[str]] = None
    self_references: Optional[bool] = None

class BiographicalExtractions(BaseModel):
    # Only non-empty categories will be present
    pass

class ChunkPayload(BaseModel):
    original_text: str
    timestamp: str
    transcript_name: str
    date: str
    category: str
    location: str
    speaker: str
    satsang_name: str
    satsang_code: str
    misc_tags: Optional[List[str]] = None
    entities: Optional[Entities] = None
    biographical_extractions: Optional[Dict[str, List[str]]] = None
    # has_{category} will be added dynamically

class ValidationInfo(BaseModel):
    coverage_complete: bool
    text_coverage_percentage: float
    timeline_coverage_percentage: float
    missing_subtitles_count: int
    timeline_gaps_count: int
    overlapping_chunks_count: int
    errors: List[str]
    warnings: List[str]
    detailed_report: Optional[str] = None

class UploadTranscriptResponse(BaseModel):
    status: str
    chunks_uploaded: int
    validation: Optional[ValidationInfo] = None

class SearchResponse(BaseModel):
    results: List[ChunkPayload]
    total: int
    page: int
    page_size: int

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
