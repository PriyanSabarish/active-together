from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INFERENCE_", env_file=".env", extra="ignore")

    app_name: str = "Active Together Inference Service"
    environment: str = "local"

    # Pinned model. Changing either value changes every similarity score, so
    # the per-prompt thresholds in server/content/prompts/vocabulary.yaml must
    # be re-measured (B54) before the new pin is used.
    clip_model_name: str = "ViT-B-32"
    clip_pretrained: str = "laion2b_s34b_b79k"

    device: str = "cpu"

    # Shared secret the server sends as "Authorization: Bearer <token>". With
    # no token set, /score refuses every request rather than run open.
    token: str | None = None

    # Set true on the deployed host: /score then rejects anything that did not
    # arrive over HTTPS (directly, or via a proxy sending X-Forwarded-Proto).
    require_https: bool = False

    # Size cap for one photo. The server already sends a capped, EXIF-stripped
    # JPEG; this is a second wall.
    max_image_bytes: int = 5 * 1024 * 1024


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
