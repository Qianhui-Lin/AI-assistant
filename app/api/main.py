import os
import logging
from fastapi import FastAPI,Depends,HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Optional
from ..helper.rate_limiter import check_rate_limit
from ..helper.history_store import add_history, get_history

from ..helper.authentication import get_current_token
from ..helper.s3_loader import load_text_from_s3_for_level,load_text_from_s3
from ..helper.rag_engine import chroma_client,build_rag_from_text, search_similar_chunks,get_collection_name

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("AI-assistant-api")

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

class Response(BaseModel):
    answer: str
    context_used: List[str]
    collection_used: str
    history: List[dict]

class ErrorResponse(BaseModel):
    detail: str

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
            print("No documents available. RAG NOT initialised.")               
                
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


@app.post("/ask_handbook",
        summary="Query the student handbook using RAG",
        description="Retrieves relevant handbook text (UG/PGT/PGR) and answers the question using GPT with RAG context.",
        response_model=Response,
        responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def ask_handbook(
    payload: QuestionRequest,
    token: str = Depends(get_current_token),
):
    check_rate_limit(token)
    question = payload.question
    level = payload.level.lower()
    origin = payload.origin
    if level not in ["ug", "pgt", "pgr"]:
        raise HTTPException(status_code=400, detail="level must be one of: 'ug','pgt','pgr'")

    logger.info(f"/ask_handbook request | level={level} | question='{payload.question}'")

    collection_name = get_collection_name("handbook", level)
    try:
    # Retrieve relevant chunks
        context_chunks = search_similar_chunks(question,doc_type="handbook", level=level)
        if not context_chunks:
            logger.warning(f"No context chunks found for level={level}")
            raise HTTPException(status_code=404, detail=f"No handbook content found for level '{level}'.")
        system_prompt = f"You are an assistant using the {level} student handbook context. "
        if origin:
            system_prompt += f"The student is {origin} student, so consider rules relevant to that."
        try: 
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "assistant", "content": "\n".join(context_chunks)},
                    {"role": "user", "content": question},
                ],
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate answer from AI model.")
        
        answer = completion.choices[0].message.content

        add_history(token, question, answer)

        return Response(
            answer=answer,
            context_used=context_chunks,
            collection_used=collection_name,
            history=get_history(token)
        )
    except HTTPException:
        raise

    except Exception as e:
        logger.exception("Unexpected error in /ask_handbook")
        raise HTTPException(status_code=500, detail="Unexpected internal server error.")

@app.post("/ask_academic_integrity",
        summary="Query the Academic Integrity Regulations using RAG",
        description="Retrieves relevant academic integrity text and answers the question using GPT with RAG context.",
        response_model=Response,
        responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def ask_integrity(
    payload: QuestionRequest,
    token: str = Depends(get_current_token),
):

    check_rate_limit(token)

    logger.info(f"/ask_academic_integrity request | question='{payload.question}'")

    question = payload.question
    origin = payload.origin

    collection_name = "academic-integrity"
    try:
        context_chunks = search_similar_chunks(question, doc_type="academic-integrity")
        if not context_chunks:
            logger.warning("No academic integrity chunks found")
            raise HTTPException(status_code=404, detail="No academic integrity content available.")

        system_prompt = "You are an assistant using the Academic Integrity Regulations."
        if origin:
            system_prompt += f" The student is {origin} student."
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "assistant", "content": "\n".join(context_chunks)},
                    {"role": "user", "content": question},
                ]
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate answer from AI model.")
        
        answer = completion.choices[0].message.content
        add_history(token, question, answer)

        return Response(
            answer=answer,
            context_used=context_chunks,
            collection_used=collection_name,
            history=get_history(token)
        )
    except HTTPException:
        raise       
    except Exception as e:
        logger.exception("Unexpected error in /ask_academic_integrity")
        raise HTTPException(status_code=500, detail="Unexpected internal server error.")