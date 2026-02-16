import os
import logging
import ollama
from groq import Groq
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- CORS Middleware ---
# For development: allow all origins
# For production: replace with your actual domain
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Configuration — Groq (LLM) + Ollama (embeddings) + Supabase
OLLAMA_EMBED_MODEL = "nomic-embed-text"
GROQ_LLM_MODEL = "openai/gpt-oss-120b"
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_INSTRUCTION = (
    "You are Mithil Ravulapalli's portfolio AI assistant. "
    "Answer questions about Mithil's skills, projects, and Agentic AI work "
    "based ONLY on the context provided in each message. "
    "If the answer isn't in the context, say \"I don't have that info, but you can email Mithil!\" "
    "Be professional, concise, and friendly."
)

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

class ChatRequest(BaseModel):
    message: str
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 1000:
            raise ValueError('Message too long (max 1000 characters)')
        return v.strip()

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "RAG Agent (Groq)"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        logger.info(f"Received query: {request.message[:100]}...")
        
        # A. Embed the User's Query using Ollama
        embed_response = ollama.embed(
            model=OLLAMA_EMBED_MODEL,
            input=request.message,
        )
        query_vector = embed_response["embeddings"][0]

        # B. Search Supabase (Vector Search)
        response = supabase.rpc("match_documents", {
            "query_embedding": query_vector,
            "match_threshold": 0.5,
            "match_count": 3
        }).execute()
        
        logger.info(f"Retrieved {len(response.data) if response.data else 0} documents")

        # C. Handle empty results
        if not response.data:
            logger.warning("No matching documents found")
            return {"reply": "I don't have enough info to answer that. Try emailing Mithil!"}

        # D. Construct Context
        context_text = "\n\n".join([doc['content'] for doc in response.data])

        # E. Generate Answer with Groq
        prompt = f"CONTEXT:\n{context_text}\n\nQUESTION: {request.message}"
        
        chat_response = groq_client.chat.completions.create(
            model=GROQ_LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt},
            ],
        )
        
        reply = chat_response.choices[0].message.content
        logger.info("Generated response successfully")
        return {"reply": reply}

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in /chat endpoint: {type(e).__name__}: {e}")
        return {"reply": "Sorry, something went wrong. Please try again later."}