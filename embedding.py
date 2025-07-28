import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_embedding(text):
    """Get embedding for a single text string"""
    embedding_resp = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return embedding_resp.data[0].embedding


def embed_and_tag_chunks(chunks):
    enriched = []
    for chunk in chunks:
        embedding_resp = openai.embeddings.create(
            model="text-embedding-3-small",
            input=chunk["text"]
        )
        embedding = embedding_resp.data[0].embedding
        enriched_chunk = chunk.copy()
        enriched_chunk["embedding"] = embedding
        enriched.append(enriched_chunk)
    return enriched
