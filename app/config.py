from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase configuration
    SUPABASE_PUBLIC_KEY: str
    ALGORITHM: str = "HS256"  # Typically RS256 for Supabase JWTs

    # OpenAI configuration
    OPENAI_API_KEY: str
    OPENAI_API_BASE_URL: str = "https://api.openai.com"

    model_config = {
        "env_file": ".env",            # Specifies the .env file to load
        "env_file_encoding": "utf-8",    # Ensures correct file encoding
    }

settings = Settings()