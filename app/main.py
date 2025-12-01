from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
import logging

from .helper import get_current_token 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RegulationRequest(BaseModel):
    question: str

class RegulationResponse(BaseModel):
    answer: str
    source_document: str
    confidence_score: float

# Initialize the FastAPI application
app = FastAPI(
    title="Lancaster Regulation Assistant AI",
    description="An AI service to quickly answer student queries based on university regulations.",
    version="1.0.0",
)


## --- Endpoint 1: Health Check ---

@app.get("/health", response_model=dict)
async def health_check():
    """Simple health check for service availability."""
    logger.info("Health check requested.")
    return {"status": "ok", "service": "Lancaster Reg Assistant"}


## --- Endpoint 2: AI Feature (answer question) ---

@app.post(
    "/feature", 
    response_model=RegulationResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_token)]
)
async def ask_regulation_question(request: RegulationRequest):
    """
    Processes a student's question, calls the AI model, and returns a structured answer.
    """
    
    logger.info(f"Authenticated request received. Question: '{request.question[:50]}...'")
    
    # 1. **AI Model Call Logic Goes Here**
    #    (You would implement the RAG/LLM call here)
    
    try:
        # --- MOCK AI RESPONSE (Replace with actual AI call) ---
        ai_answer = (
            "The policy on late submission states that coursework submitted "
            "up to seven calendar days late will be penalised by a reduction of 10 "
            "marks per day, down to a minimum mark of 40 (the passing mark)."
        )
        source = "Academic Regulations, Section 5.3"
        confidence = 0.98
        # -----------------------------------------------------

        logger.info("AI response successfully generated/mocked.")
        
        # 2. Return the structured response
        return RegulationResponse(
            answer=ai_answer,
            source_document=source,
            confidence_score=confidence,
        )

    except Exception as e:
        logger.error(f"Error processing AI request: {e}")
        # 3. Handle errors gracefully
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal AI service error: {str(e)}",
        )