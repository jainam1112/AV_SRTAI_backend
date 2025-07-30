# Biographical extraction using fine-tuned OpenAI model
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
from constants import BIOGRAPHICAL_CATEGORY_KEYS

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logger = logging.getLogger(__name__)

def extract_bio_from_chunks(chunks: List[Dict[str, Any]], transcript_name: str, ft_model_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract biographical information from transcript chunks using OpenAI fine-tuned model.
    
    Args:
        chunks: List of chunk dictionaries containing text and metadata
        transcript_name: Name of the transcript being processed
        ft_model_id: Fine-tuned model ID to use for extraction. If None, uses FINE_TUNED_BIO_MODEL from env
        
    Returns:
        List of dictionaries with biographical extractions for each chunk
    """
    # Use environment fine-tuned model if no specific model provided
    if not ft_model_id:
        ft_model_id = os.getenv("FINE_TUNED_BIO_MODEL")
        if not ft_model_id:
            logger.warning("No fine-tuned model ID provided and FINE_TUNED_BIO_MODEL not set in environment. Using default model.")
            ft_model_id = os.getenv("ANSWER_EXTRACTION_MODEL", "gpt-3.5-turbo")
        else:
            logger.info(f"Using fine-tuned model from environment: {ft_model_id}")
    
    if not chunks:
        logger.info("No chunks provided for biographical extraction.")
        return []
    
    logger.info(f"Starting biographical extraction for {len(chunks)} chunks from '{transcript_name}' using model '{ft_model_id}'")
    
    extracted_bios = []
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)} for biographical extraction")
        
        # Extract text from chunk
        chunk_text = ""
        if isinstance(chunk, dict):
            chunk_text = chunk.get('text', '') or chunk.get('original_text', '') or chunk.get('content', '')
        elif isinstance(chunk, str):
            chunk_text = chunk
        else:
            logger.warning(f"Chunk {i+1} has unexpected format: {type(chunk)}")
            extracted_bios.append({})
            continue
            
        if not chunk_text.strip():
            logger.warning(f"Chunk {i+1} has empty text content")
            extracted_bios.append({})
            continue
        
        # Extract biographical information using fine-tuned model
        try:
            logger.info(f"Calling fine-tuned model '{ft_model_id}' for chunk {i+1}")
            
            ft_response = client.chat.completions.create(
                model=ft_model_id,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at extracting specific biographical information about Gurudev from transcripts, outputting a JSON object with predefined keys like early_life_childhood, education_learning, etc. Only include verbatim quotes. If no information for a category, use an empty list []."
                    },
                    {
                        "role": "user", 
                        "content": f"Transcript Chunk: \"{chunk_text}\""
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=4096,
                temperature=0.0
            )
            
            extracted_json_str = ft_response.choices[0].message.content
            
            # Clean up JSON response
            if extracted_json_str.startswith("```json"):
                extracted_json_str = extracted_json_str[7:]
            if extracted_json_str.endswith("```"):
                extracted_json_str = extracted_json_str[:-3]
            extracted_json_str = extracted_json_str.strip()
            
            # Parse JSON response
            parsed_bio_data = json.loads(extracted_json_str)
            
            # Create biographical extraction with category flags
            bio_extraction = {
                'biographical_extractions': parsed_bio_data
            }
            
            # Add boolean flags for each biographical category
            for cat_key in BIOGRAPHICAL_CATEGORY_KEYS:
                flag_field_name = f"has_{cat_key}"
                bio_extraction[flag_field_name] = bool(parsed_bio_data.get(cat_key))
            
            extracted_bios.append(bio_extraction)
            logger.info(f"Successfully extracted biographical data for chunk {i+1}")
            
        except json.JSONDecodeError as e_json:
            logger.error(f"JSON parse error for chunk {i+1}: {e_json}. Response: {extracted_json_str[:300] if 'extracted_json_str' in locals() else 'N/A'}")
            extracted_bios.append({})
            
        except OpenAIError as e_openai:
            logger.error(f"OpenAI API error for chunk {i+1}: {e_openai}")
            extracted_bios.append({})
            
        except Exception as e_general:
            logger.error(f"Unexpected error during bio-extraction for chunk {i+1}: {e_general}")
            extracted_bios.append({})
    
    successful_extractions = sum(1 for bio in extracted_bios if bio)
    logger.info(f"Biographical extraction completed: {successful_extractions}/{len(chunks)} chunks processed successfully")
    
    return extracted_bios


def get_biographical_categories() -> List[str]:
    """Return list of available biographical category keys."""
    return BIOGRAPHICAL_CATEGORY_KEYS.copy()


def validate_biographical_extraction(bio_data: Dict[str, Any]) -> bool:
    """
    Validate that biographical extraction contains expected structure.
    
    Args:
        bio_data: Dictionary containing biographical extraction
        
    Returns:
        True if valid structure, False otherwise
    """
    if not isinstance(bio_data, dict):
        return False
        
    if 'biographical_extractions' not in bio_data:
        return False
        
    extractions = bio_data['biographical_extractions']
    if not isinstance(extractions, dict):
        return False
        
    # Check that all values are lists (as expected for biographical quotes)
    for key, value in extractions.items():
        if not isinstance(value, list):
            return False
            
    return True
