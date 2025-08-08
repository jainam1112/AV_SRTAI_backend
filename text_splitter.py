# In text_splitter.py

import re

def split_text_into_chunks(full_text: str, chunk_size: int = 400, chunk_overlap: int = 75) -> list[str]:
    """
    Splits a single block of text into fixed-size chunks with overlap.

    Args:
        full_text: The entire transcript text.
        chunk_size: The target number of words for each chunk.
        chunk_overlap: The number of words to overlap between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    if not full_text:
        return []

    # Use a simple regex to split the text into words
    words = re.split(r'\s+', full_text.strip())
    
    if len(words) <= chunk_size:
        # If the whole text is smaller than the chunk size, return it as a single chunk
        return [" ".join(words)]

    chunks = []
    # The 'step' is the chunk size minus the overlap
    step = chunk_size - chunk_overlap
    
    # Iterate through the words with a sliding window
    for i in range(0, len(words), step):
        # Define the start and end of the window
        start_index = i
        end_index = i + chunk_size
        
        # Get the words for the current chunk
        chunk_words = words[start_index:end_index]
        
        # Join the words back into a string and add to the list
        chunks.append(" ".join(chunk_words))
        
        # If the end of our window has reached the end of the text, stop.
        if end_index >= len(words):
            break
            
    return chunks

def split_subtitles_into_chunks_with_timestamps(
    subtitles: list[dict], 
    chunk_size: int = 400, 
    chunk_overlap: int = 75
) -> list[dict]:
    """
    Splits subtitles into fixed-size chunks with overlap, including timestamps.

    Args:
        subtitles: A list of subtitle dictionaries with 'start', 'end', and 'text' fields.
        chunk_size: The target number of words for each chunk.
        chunk_overlap: The number of words to overlap between consecutive chunks.

    Returns:
        A list of chunk dictionaries with 'start', 'end', and 'text' fields.
    """
    if not subtitles:
        return []

    chunks = []
    current_chunk = []
    current_chunk_word_count = 0
    current_chunk_start_time = None

    for subtitle in subtitles:
        words = subtitle["text"].split()
        if current_chunk_start_time is None:
            current_chunk_start_time = subtitle["start"]

        # Add subtitle to the current chunk
        current_chunk.append(subtitle)
        current_chunk_word_count += len(words)

        # If the chunk reaches the target size, finalize it
        if current_chunk_word_count >= chunk_size:
            chunk_text = " ".join([s["text"] for s in current_chunk])
            chunk_start_time = current_chunk_start_time
            chunk_end_time = current_chunk[-1]["end"]

            chunks.append({
                "start": chunk_start_time,
                "end": chunk_end_time,
                "text": chunk_text
            })

            # Handle overlap
            overlap_words = chunk_overlap
            current_chunk = []
            current_chunk_word_count = 0
            current_chunk_start_time = None

    # Add remaining subtitles as the final chunk
    if current_chunk:
        chunk_text = " ".join([s["text"] for s in current_chunk])
        chunk_start_time = current_chunk_start_time
        chunk_end_time = current_chunk[-1]["end"]
        chunks.append({
            "start": chunk_start_time,
            "end": chunk_end_time,
            "text": chunk_text
        })

    return chunks
