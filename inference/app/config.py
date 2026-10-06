from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INFERENCE_", env_file=".env", extra="ignore")

    app_name: str = "Active Together Inference Service"
    environment: str = "local"

    # CPU-only defaults — both are small enough to load and run on a free/hobby
    # CPU tier. Swap via env vars if GPU hosting becomes available; nothing
    # outside this service needs to know the model names.
    clip_model_name: str = "openai/clip-vit-base-patch32"
    text_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"

    device: str = "cpu"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
