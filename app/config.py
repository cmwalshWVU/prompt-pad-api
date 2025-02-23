from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_PROJECT_ID: str | None = None  # Optional if needed
    ALGORITHM: str = "HS256"
    OPENAI_API_KEY: str
    OPENAI_API_BASE_URL: str = "https://api.openai.com"

    model_config = {
        "env_file": ".env",            # Specifies the .env file to load
        "env_file_encoding": "utf-8",    # Ensures correct file encoding
        "extra": "allow"  # This will ignore extra variables such as SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
    }

settings = Settings()