from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    target_form_url: str = "https://mendrika-alma.github.io/form-submission/"
    upload_dir: str = str(Path(__file__).parent / "uploads")
    max_file_size_mb: int = 20
    allowed_extensions: list[str] = [".pdf", ".jpg", ".jpeg", ".png"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
