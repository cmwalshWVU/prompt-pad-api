from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.dependencies import get_current_user
from app.services import openai_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class OpenAIRequest(BaseModel):
    prompt: str

@router.post("/openai", tags=["OpenAI"])
def openai_endpoint(request: OpenAIRequest, user=Depends(get_current_user)):
    """
    Endpoint that receives a prompt, calls the OpenAI API, and returns the response.
    """
    try:
        response = openai_service.call_openai(request.prompt)
        return response
    except Exception as e:
        logger.info(str(e))

        raise HTTPException(status_code=500, detail=str(e))
