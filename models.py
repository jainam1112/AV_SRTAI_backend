from pydantic import BaseModel
from typing import List, Dict, Optional, Any

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

class BioExtractionRequest(BaseModel):
    transcript_name: str
    ft_model_id: Optional[str] = None

class BioExtractionResponse(BaseModel):
    status: str
    transcript_name: str
    chunks_processed: int
    chunks_updated: int
    model_used: str
    extraction_summary: Dict[str, int]  # Category -> count of chunks with that category

class EntityExtractionRequest(BaseModel):
    use_ai: Optional[bool] = True
    include_statistics: Optional[bool] = True

class EntityExtractionResponse(BaseModel):
    status: str
    transcript_name: str
    chunks_processed: int
    chunks_updated: int
    method_used: str  # "AI" or "rule-based"
    entity_statistics: Optional[Dict[str, Any]] = None
