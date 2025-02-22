from fastapi import Header, HTTPException, Depends
import jwt  # PyJWT
from jwt import PyJWTError

from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_current_user(authorization: str = Header(...)):
    """
    Dependency to extract and verify the JWT token from the Authorization header.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(
            token,
            "1uU2DCUqICTiHvHT0zSGtu7orzOQ9T/U12b8CvsawK+ovTwZaqgHBJt/2Qgrk6zOD2ktyIFBt8BIKwmnhyNmyA==",
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False}
        )
    except PyJWTError as e:
        logger.info(str(e))

        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    return payload
