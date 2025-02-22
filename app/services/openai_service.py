import requests
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def call_openai(prompt: str) -> dict:
    """
    Calls the OpenAI API using the provided prompt.
    """
    logger.info(str(prompt))
    logger.info(str(settings.OPENAI_API_KEY))
    url = f"https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 10000,
        "temperature": 0.7,
    }
    response = requests.post(url, headers=headers, json=payload)
    full_response = response.json()
    print(full_response)
    response.raise_for_status()  # simple error handling
    return response.json()
