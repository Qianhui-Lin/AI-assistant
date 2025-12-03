import os
from fastapi import FastAPI,Depends
from contextlib import asynccontextmanager
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from ..helper.rate_limiter import check_rate_limit
from ..helper.history_store import add_history, get_history

from ..helper.authentication import get_current_token
from ..helper.s3_loader import load_text_from_s3_for_level,load_text_from_s3
from ..helper.rag_engine import chroma_client,build_rag_from_text, search_similar_chunks,get_collection_name

MODE = os.getenv("MODE", "development").lower()
print(f"[MODE] Running in {MODE.upper()} mode")

AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "bucket-name")
AWS_UG_KEY = os.getenv("AWS_UG_KEY")
AWS_PGT_KEY = os.getenv("AWS_PGT_KEY")
AWS_PGR_KEY = os.getenv("AWS_PGR_KEY") 
AWS_ACADEMIC_KEY = os.getenv("AWS_ACADEMIC_KEY") 

client = OpenAI()
class QuestionRequest(BaseModel):
    question: str
    level: str   # "ug" | "pgt" | "pgr"
    origin: str| None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    levels = ["ug", "pgt", "pgr"]
    handbooks = {}
    missing_levels = []
    integrity_text: str | None = None
    from ..helper.rag_engine import chroma_client
    try:
        # Load handbooks from S3
        for lvl in levels:
            try:
                text = load_text_from_s3_for_level(lvl)
                handbooks[lvl] = text
                print(f"[OK] Loaded handbook for level: {lvl.upper()}")
            except Exception as e:
                print(f"[MISSING] No handbook found for level {lvl.upper()}: {e}")
                missing_levels.append(lvl)
        # Load Academic Integrity Regulations
        try:
            integrity_text = load_text_from_s3(AWS_ACADEMIC_KEY)
            print("[OK] Loaded Academic Integrity Regulations")
        except Exception as e:
            print(f"[MISSING] No Academic Integrity file: {e}")
            integrity_text = None
        except Exception as e:
            print(f"[MISSING] No Academic Integrity file: {e}")

        existing_names = {col.name for col in chroma_client.list_collections()}
        if handbooks:
            existing_names = {col.name for col in chroma_client.list_collections()}
            # Build RAG only for levels that actually exist
            for lvl, text in handbooks.items():
                collection_name = get_collection_name(doc_type="handbook",level=lvl)
                already_exists = collection_name in existing_names
                if MODE == "production" and already_exists:
                    print(f"[SKIP] Collection '{collection_name}' exists — skipping embedding.")
                else:
                    print(f"[BUILD] Creating/updating collection '{collection_name}'")
                    build_rag_from_text(text, doc_type="handbook",level=lvl)

        if integrity_text is not None:
            integrity_collection = "academic-integrity"
            already_exists = integrity_collection in existing_names

            if MODE == "production" and already_exists:
                print(f"[SKIP] Collection '{integrity_collection}' exists — skipping embedding.")
            else:
                print(f"[BUILD] Creating/updating collection '{integrity_collection}'")
                build_rag_from_text(integrity_text, doc_type="academic-integrity")

        if handbooks or integrity_text is not None:
            print("[INIT] RAG indexes initialised.")
        else:
            print("⚠️ No documents available. RAG NOT initialised.")               
                
            print(f"RAG index initialised for: {', '.join([lvl.upper() for lvl in handbooks])}")

    except Exception as e:
        print(f"Error during startup initialisation: {e}")
        raise

    yield  # <-- the app runs between startup and shutdown
    try:
        if MODE == "development":
            for col in chroma_client.list_collections():
                chroma_client.delete_collection(col.name)
            print("Cleaned up ChromaDB collection on shutdown.")
        else:
            print("[CLEANUP] Production mode — skipping ChromaDB cleanup.")
        print("Shutting down AI assistant service.")
    except Exception as e:
        print(f"Error during cleanup: {e}")    


# Create app with lifespan handler
app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ask_handbook")
def ask_handbook(
    payload: QuestionRequest,
    token: str = Depends(get_current_token),
):
    check_rate_limit(token)
    question = payload.question
    level = payload.level
    origin = payload.origin

    collection_name = get_collection_name("handbook", level)

    # Retrieve relevant chunks
    context_chunks = search_similar_chunks(question,doc_type="handbook", level=level)
    system_prompt = f"You are an assistant using the {level} student handbook context. "
    if origin:
        system_prompt += f"The student is {origin} student, so consider rules relevant to that."
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": "\n".join(context_chunks)},
            {"role": "user", "content": question},
        ],
    )

    answer = completion.choices[0].message.content

    add_history(token, question, answer)

    return {
        "answer": answer,
        "context_used": context_chunks,
        "collection_used": collection_name,
        "history": get_history(token)
    }


@app.post("/ask_academic_integrity")
def ask_integrity(
    payload: QuestionRequest,
    token: str = Depends(get_current_token),
):

    check_rate_limit(token)

    question = payload.question
    origin = payload.origin

    collection_name = "academic-integrity"
    context_chunks = search_similar_chunks(question, doc_type="academic-integrity")

    system_prompt = "You are an assistant using the Academic Integrity Regulations."
    if origin:
        system_prompt += f" The student is from {origin}."

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": "\n".join(context_chunks)},
            {"role": "user", "content": question},
        ]
    )

    answer = completion.choices[0].message.content
    add_history(token, question, answer)

    return {
        "type": "academic_integrity",
        "answer": answer,
        "context_used": context_chunks,
        "collection_used": collection_name,
        "history": get_history(token),
    }