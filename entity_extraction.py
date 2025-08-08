# Enhanced Entity Extraction for Spiritual Transcripts
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
from constants import LOCATIONS, SPEAKERS

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logger = logging.getLogger("entity_extraction")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Entity categories for spiritual transcripts
ENTITY_CATEGORIES = {
    "people": {
        "description": "Names of people mentioned including devotees, disciples, spiritual figures, historical personalities",
        "examples": ["Shrimad Rajchandra", "Kavi", "Lalluji", "Ambalalbhai", "Gopal Kaka"]
    },
    "places": {
        "description": "Locations mentioned including cities, villages, ashrams, temples, countries",
        "examples": ["Sayla", "Surat", "Shrimad Rajchandra Mission", "Dharampur", "Virpur"]
    },
    "spiritual_concepts": {
        "description": "Spiritual and philosophical concepts, practices, states of being",
        "examples": ["moksha", "dharma", "karma", "samadhi", "vairagya", "bhakti", "meditation"]
    },
    "scriptures_texts": {
        "description": "Religious texts, books, scriptures, writings mentioned",
        "examples": ["Atmasiddhi", "Bhagavad Gita", "Patrank", "Vachanamrut", "Shrimad Bhagavatam"]
    },
    "organizations_institutions": {
        "description": "Organizations, institutions, missions, trusts mentioned",
        "examples": ["Shrimad Rajchandra Mission", "Dharampur Ashram", "Koba Ashram"]
    },
    "events_occasions": {
        "description": "Specific events, festivals, ceremonies, occasions mentioned",
        "examples": ["Guru Purnima", "Mahavir Jayanti", "Annual Function", "Diksha Ceremony"]
    },
    "time_references": {
        "description": "Specific dates, years, time periods mentioned",
        "examples": ["1867", "Samvat 1924", "Chaitra Sud 5", "morning time", "evening"]
    },
    "self_references": {
        "description": "References to Gurudev himself (first person statements)",
        "type": "boolean",
        "examples": ["I experienced", "My childhood", "When I was young"]
    }
}

def extract_entities_from_chunks(chunks: List[Dict[str, Any]], transcript_name: str, use_ai: bool = True) -> List[Dict[str, Any]]:
    """
    Extract entities from transcript chunks using AI or rule-based methods.
    
    Args:
        chunks: List of chunk dictionaries containing text and metadata
        transcript_name: Name of the transcript being processed
        use_ai: Whether to use AI for extraction (True) or rule-based methods (False)
        
    Returns:
        List of dictionaries with entity extractions for each chunk
    """
    if not chunks:
        logger.info("No chunks provided for entity extraction.")
        return []
    
    logger.info(f"Starting entity extraction for {len(chunks)} chunks from '{transcript_name}' using {'AI' if use_ai else 'rule-based'} method")
    
    extracted_entities = []
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)} for entity extraction")
        
        # Extract text from chunk (handle different formats)
        chunk_text = extract_text_from_chunk(chunk)
        
        if not chunk_text.strip():
            logger.warning(f"Chunk {i+1} has empty text content")
            extracted_entities.append(create_empty_entity_structure())
            continue
        
        if use_ai:
            entities = extract_entities_with_ai(chunk_text, i+1)
        else:
            entities = extract_entities_rule_based(chunk_text, i+1)
        
        extracted_entities.append(entities)
    
    successful_extractions = sum(1 for entities in extracted_entities if entities.get('people') or entities.get('places'))
    logger.info(f"Entity extraction completed: {successful_extractions}/{len(chunks)} chunks with entities found")
    
    return extracted_entities

def extract_text_from_chunk(chunk: Dict[str, Any]) -> str:
    """Extract text from chunk handling different formats"""
    if isinstance(chunk, dict):
        # Check for Qdrant format
        if 'payload' in chunk and isinstance(chunk['payload'], dict):
            return chunk['payload'].get('original_text', '')
        else:
            # Direct format
            return chunk.get('text', '') or chunk.get('original_text', '') or chunk.get('content', '')
    elif isinstance(chunk, str):
        return chunk
    else:
        return ""

def extract_entities_with_ai(text: str, chunk_number: int) -> Dict[str, Any]:
    """Extract entities using OpenAI API"""
    
    try:
        model_name = os.getenv("ANSWER_EXTRACTION_MODEL", "gpt-3.5-turbo")
        
        system_prompt = f"""You are an expert at extracting entities from spiritual discourse transcripts. 
        Extract the following types of entities from the text and return them as a JSON object:

        {json.dumps(ENTITY_CATEGORIES, indent=2)}

        Rules:
        1. Only extract entities that are explicitly mentioned in the text
        2. For self_references, return true if the speaker refers to themselves (I, me, my, etc.)
        3. Return empty arrays for categories with no entities found
        4. Use exact names/terms as they appear in the text
        5. For places, prioritize spiritual locations and Indian cities/regions
        """
        
        user_prompt = f"Extract entities from this spiritual discourse text:\n\n{text}"
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Clean up JSON response
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # Parse and validate JSON
        entities = json.loads(result_text)
        
        # Clean and validate the entities
        cleaned_entities = clean_entity_structure(entities)
        
        logger.info(f"Successfully extracted entities for chunk {chunk_number}")
        return cleaned_entities
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error for chunk {chunk_number}: {e}")
        return create_empty_entity_structure()
        
    except OpenAIError as e:
        logger.error(f"OpenAI API error for chunk {chunk_number}: {e}")
        return create_empty_entity_structure()
        
    except Exception as e:
        logger.error(f"Unexpected error during entity extraction for chunk {chunk_number}: {e}")
        return create_empty_entity_structure()

def extract_entities_rule_based(text: str, chunk_number: int) -> Dict[str, Any]:
    """Extract entities using rule-based methods"""
    
    entities = create_empty_entity_structure()
    text_lower = text.lower()
    
    # Extract people (look for capitalized names)
    import re
    people_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:bhai|ben|ji|sir|madam|saheb))?'
    potential_people = re.findall(people_pattern, text)
    # Filter out common false positives
    common_words = {'The', 'This', 'That', 'What', 'When', 'Where', 'How', 'Why', 'And', 'But', 'Or', 'So', 'If'}
    entities['people'] = [p for p in potential_people if p not in common_words]
    
    # Extract places from known locations
    for location in LOCATIONS:
        if location.lower() in text_lower:
            entities['places'].append(location)
    
    # Look for spiritual concepts (basic keywords)
    spiritual_keywords = ['moksha', 'dharma', 'karma', 'samadhi', 'meditation', 'bhakti', 'vairagya', 'atman', 'brahman']
    for keyword in spiritual_keywords:
        if keyword in text_lower:
            entities['spiritual_concepts'].append(keyword)
    
    # Check for self-references
    self_indicators = ['i ', 'my ', 'me ', 'myself', 'i\'', 'when i']
    entities['self_references'] = any(indicator in text_lower for indicator in self_indicators)
    
    # Remove duplicates
    for key in entities:
        if isinstance(entities[key], list):
            entities[key] = list(set(entities[key]))
    
    logger.info(f"Rule-based entity extraction completed for chunk {chunk_number}")
    return entities

def create_empty_entity_structure() -> Dict[str, Any]:
    """Create empty entity structure"""
    return {
        "people": [],
        "places": [],
        "spiritual_concepts": [],
        "scriptures_texts": [],
        "organizations_institutions": [],
        "events_occasions": [],
        "time_references": [],
        "self_references": False
    }

def clean_entity_structure(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and validate entity structure"""
    cleaned = create_empty_entity_structure()
    
    for category in cleaned.keys():
        if category in entities:
            if category == "self_references":
                # Ensure boolean
                cleaned[category] = bool(entities[category])
            else:
                # Ensure list and remove empty strings
                if isinstance(entities[category], list):
                    cleaned[category] = [item for item in entities[category] if item and str(item).strip()]
                elif entities[category]:  # Single item
                    cleaned[category] = [str(entities[category]).strip()]
    
    return cleaned

def get_entity_statistics(entity_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics for entity extraction results"""
    
    stats = {
        "total_chunks": len(entity_results),
        "chunks_with_entities": 0,
        "entity_counts": {},
        "unique_entities": {},
        "self_reference_chunks": 0
    }
    
    # Initialize counters
    for category in create_empty_entity_structure().keys():
        stats["entity_counts"][category] = 0
        if category != "self_references":
            stats["unique_entities"][category] = set()
    
    # Count entities
    for entities in entity_results:
        has_entities = False
        
        for category, items in entities.items():
            if category == "self_references":
                if items:
                    stats["self_reference_chunks"] += 1
                    has_entities = True
            else:
                if items:
                    stats["entity_counts"][category] += len(items)
                    stats["unique_entities"][category].update(items)
                    has_entities = True
        
        if has_entities:
            stats["chunks_with_entities"] += 1
    
    # Convert sets to lists for JSON serialization
    for category in stats["unique_entities"]:
        stats["unique_entities"][category] = list(stats["unique_entities"][category])
    
    return stats

def validate_entity_extraction(entities: Dict[str, Any]) -> bool:
    """Validate entity extraction structure"""
    expected_structure = create_empty_entity_structure()
    
    if not isinstance(entities, dict):
        return False
    
    for key in expected_structure:
        if key not in entities:
            return False
        
        if key == "self_references":
            if not isinstance(entities[key], bool):
                return False
        else:
            if not isinstance(entities[key], list):
                return False
    
    return True
