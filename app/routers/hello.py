from fastapi import APIRouter, Depends
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/hello", tags=["Hello"])
def hello_world(user=Depends(get_current_user)):
    """
    Returns a greeting along with the token payload for testing token authorization.
    """
    return {"message": "Hello, world!", "user": user}
