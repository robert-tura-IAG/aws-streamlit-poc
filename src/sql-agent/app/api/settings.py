# app/api/settings.py
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/aero")

    # Langfuse
    langfuse_public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    langfuse_host: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # Comet
    comet_api_key: str = os.getenv("COMET_API_KEY", "hjpbWz2UUH7JgWCtQjg4AbV1v")
    comet_workspace: str = os.getenv("COMET_WORKSPACE", "lourdes-rojana")
    comet_project_name: str = os.getenv("COMET_PROJECT_NAME", "simple-llm-bot")

    # Prompt versioning
    prompt_name: str = os.getenv("PROMPT_NAME", "aero-sql-agent-sql")
    prompt_version: str = os.getenv("PROMPT_VERSION", "1.0.0")

    opik_api_key: str | None = os.getenv("OPIK_API_KEY")
    opik_workspace: str | None = os.getenv("OPIK_WORKSPACE")
    opik_project_name: str | None = os.getenv("OPIK_PROJECT_NAME")
    opik_url_override: str | None = os.getenv("OPIK_URL_OVERRIDE")

settings = Settings()
