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

# Configure logging for this module
logger = logging.getLogger("bio_extraction")
if not logger.handlers:
    # Only add handler if none exist to avoid duplicates
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

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
        
        # Extract text from chunk (handle Qdrant format)
        chunk_text = ""
        if isinstance(chunk, dict):
            # First check if it's a Qdrant format with payload
            if 'payload' in chunk and isinstance(chunk['payload'], dict):
                chunk_text = chunk['payload'].get('original_text', '')
                logger.debug(f"Chunk {i+1}: Using text from payload.original_text")
            else:
                # Fallback to direct text fields
                chunk_text = chunk.get('text', '') or chunk.get('original_text', '') or chunk.get('content', '')
                logger.debug(f"Chunk {i+1}: Using text from direct fields")
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
                        "content": "You are an expert at extracting specific biographical information about Gurudev from transcripts. Return a JSON object with predefined keys like early_life_childhood, education_learning, spiritual_journey, health_wellness, family_relationships, career_work, personal_interests, philosophical_views, experiences_travels, challenges_obstacles. Only include verbatim quotes from the text. If no information for a category, use an empty list []."
                    },
                    {
                        "role": "user", 
                        "content": f"Extract biographical information from this transcript chunk:\n\n{chunk_text}\n\nReturn only a JSON object with the biographical categories as keys and arrays of verbatim quotes as values."
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=3000,  # Reduced to prevent overly long responses
                temperature=0.0
            )
            
            extracted_json_str = ft_response.choices[0].message.content
            
            # Clean up JSON response
            if extracted_json_str.startswith("```json"):
                extracted_json_str = extracted_json_str[7:]
            if extracted_json_str.endswith("```"):
                extracted_json_str = extracted_json_str[:-3]
            extracted_json_str = extracted_json_str.strip()
            
            # Enhanced JSON cleanup for malformed responses
            if not extracted_json_str.startswith('{'):
                # Find the first { character
                start_idx = extracted_json_str.find('{')
                if start_idx != -1:
                    extracted_json_str = extracted_json_str[start_idx:]
            
            # Try to fix unterminated strings at the end
            if extracted_json_str.count('"') % 2 != 0:
                # Odd number of quotes - likely unterminated string
                logger.warning(f"Chunk {i+1}: Detected potential unterminated string, attempting to fix")
                # Find the last quote and see if we need to close it
                last_quote_idx = extracted_json_str.rfind('"')
                if last_quote_idx != -1:
                    # Check if this quote is properly closed
                    remaining = extracted_json_str[last_quote_idx+1:].strip()
                    if remaining and not remaining.startswith((':', ',', '}', ']')):
                        # Likely an unterminated string, truncate at the quote
                        extracted_json_str = extracted_json_str[:last_quote_idx+1] + '"]}'
                        logger.warning(f"Chunk {i+1}: Truncated unterminated string")
            
            # Parse JSON response with better error handling
            try:
                parsed_bio_data = json.loads(extracted_json_str)
            except json.JSONDecodeError as json_err:
                # If parsing fails, try to extract a valid JSON object
                logger.warning(f"Chunk {i+1}: Initial JSON parse failed, attempting recovery")
                
                # Try to find the largest valid JSON object
                for end_pos in range(len(extracted_json_str), 0, -1):
                    test_str = extracted_json_str[:end_pos]
                    # Ensure it ends properly
                    if not test_str.endswith('}'):
                        test_str += '}'
                    try:
                        parsed_bio_data = json.loads(test_str)
                        logger.info(f"Chunk {i+1}: Successfully recovered JSON by truncating to {end_pos} characters")
                        break
                    except json.JSONDecodeError:
                        continue
                else:
                    # If all attempts fail, raise the original error
                    raise json_err
            
            # Validate the parsed data structure
            if not isinstance(parsed_bio_data, dict):
                logger.warning(f"Chunk {i+1}: Parsed data is not a dictionary, creating empty structure")
                parsed_bio_data = {cat: [] for cat in BIOGRAPHICAL_CATEGORY_KEYS}
            
            # Ensure all expected categories exist and are lists
            for cat_key in BIOGRAPHICAL_CATEGORY_KEYS:
                if cat_key not in parsed_bio_data:
                    parsed_bio_data[cat_key] = []
                elif not isinstance(parsed_bio_data[cat_key], list):
                    # Convert non-list values to lists
                    if isinstance(parsed_bio_data[cat_key], str):
                        parsed_bio_data[cat_key] = [parsed_bio_data[cat_key]] if parsed_bio_data[cat_key].strip() else []
                    else:
                        parsed_bio_data[cat_key] = []
                        logger.warning(f"Chunk {i+1}: Converted non-list value in category '{cat_key}' to empty list")
            
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
            
            # Log summary of what was extracted
            categories_with_data = [cat for cat, quotes in parsed_bio_data.items() if quotes]
            if categories_with_data:
                logger.info(f"Chunk {i+1}: Found data in categories: {', '.join(categories_with_data)}")
            else:
                logger.info(f"Chunk {i+1}: No biographical data found in this chunk")
            
        except json.JSONDecodeError as e_json:
            logger.error(f"JSON parse error for chunk {i+1}: {e_json}")
            logger.error(f"Chunk {i+1} problematic response (first 500 chars): {extracted_json_str[:500] if 'extracted_json_str' in locals() else 'N/A'}")
            logger.error(f"Chunk {i+1} problematic response (last 200 chars): {extracted_json_str[-200:] if 'extracted_json_str' in locals() and len(extracted_json_str) > 200 else 'N/A'}")
            # Try to create a minimal valid response
            fallback_bio = {
                'biographical_extractions': {cat: [] for cat in BIOGRAPHICAL_CATEGORY_KEYS}
            }
            for cat_key in BIOGRAPHICAL_CATEGORY_KEYS:
                fallback_bio[f"has_{cat_key}"] = False
            extracted_bios.append(fallback_bio)
            logger.info(f"Chunk {i+1}: Created fallback bio extraction due to JSON error")
            
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
