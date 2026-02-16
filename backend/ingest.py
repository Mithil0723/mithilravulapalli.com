import os
import logging
import ollama
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config — Ollama (local) + Supabase
OLLAMA_EMBED_MODEL = "nomic-embed-text"

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

def split_text(text, max_chars=1000, overlap=200):
    """
    Splits text into chunks by paragraphs with smart overlap.
    Overlap preserves sentence boundaries to avoid cutting mid-sentence.
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) < max_chars:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Find a good overlap point (last sentence boundary)
            if len(current_chunk) > overlap:
                # Look for last period within overlap region
                overlap_start = len(current_chunk) - overlap
                last_period = current_chunk.rfind('.', overlap_start)
                if last_period != -1:
                    overlap_text = current_chunk[last_period + 1:].strip()
                else:
                    overlap_text = current_chunk[-overlap:].strip()
            else:
                overlap_text = current_chunk.strip()
            
            current_chunk = overlap_text + "\n\n" + para + "\n\n"
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def main():
    # 1. Load File
    file_path = "../About_me.md"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        logger.info(f"Loaded {len(text)} characters from {file_path}")
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        logger.info("Make sure About_me.md exists in the parent directory")
        return

    # 2. Clear old data to prevent duplicates on re-runs
    logger.info("Clearing existing documents from About_me.md...")
    supabase.table("documents").delete().eq(
        "metadata->>source", "About_me.md"
    ).execute()

    # 3. Split into Chunks
    chunks = split_text(text)
    logger.info(f"Split into {len(chunks)} chunks")

    # 4. Embed & Upload using Ollama (no rate limiting needed — local model)
    successful = 0
    failed = 0
    
    for i, chunk in enumerate(chunks):
        try:
            logger.info(f"Processing chunk {i+1}/{len(chunks)}...")

            # Generate Embedding using Ollama
            result = ollama.embed(
                model=OLLAMA_EMBED_MODEL,
                input=chunk,
            )
            embedding = result["embeddings"][0]

            # Insert into Supabase
            data = {
                "content": chunk,
                "metadata": {"source": "About_me.md", "chunk_index": i},
                "embedding": embedding
            }
            supabase.table("documents").insert(data).execute()
            successful += 1
                
        except Exception as e:
            logger.error(f"Failed to process chunk {i+1}: {e}")
            failed += 1
            continue

    logger.info(f"Ingestion complete! {successful} successful, {failed} failed")

if __name__ == "__main__":
    main()
