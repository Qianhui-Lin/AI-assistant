from fastapi import FastAPI,Depends
from contextlib import asynccontextmanager
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

from ..helper.authentication import get_current_token
from ..helper.s3_loader import load_text_from_s3
from ..helper.rag_engine import build_rag_from_text, search_similar_chunks


client = OpenAI()
class QuestionRequest(BaseModel):
    question: str
    level: str   # "UG" | "PGT" | "PGR"
    origin: str  # "home" | "international"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup logic ---
    try:
        text = load_text_from_s3()
        build_rag_from_text(text)
        print("RAG index initialised from handbook text.")
    except Exception as e:
        # If you want, you can log and re-raise
        print(f"Error during startup initialisation: {e}")
        raise

    yield  # <-- the app runs between startup and shutdown
    try:
        from ..helper.rag_engine import collection, chroma_client
        
        # Option 1: Delete the collection
        chroma_client.delete_collection("handbook")
        print("Cleaned up ChromaDB collection on shutdown.")
        # --- Shutdown logic (optional) ---
        # e.g. close DB connections, clean temp files, etc.
        print("Shutting down AI assistant service.")
    except Exception as e:
        print(f"Error during cleanup: {e}")    


# Create app with lifespan handler
app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/feature")
def feature_endpoint(
    payload: QuestionRequest,
    token: str = Depends(get_current_token),
):
    question = payload.question

    # Retrieve relevant chunks from your Chroma / RAG engine
    context_chunks = search_similar_chunks(question)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer using the student handbook context."},
            {"role": "assistant", "content": "\n".join(context_chunks)},
            {"role": "user", "content": question},
        ],
    )

    answer = completion.choices[0].message.content

    return {
        "answer": answer,
        "context_used": context_chunks,
    }