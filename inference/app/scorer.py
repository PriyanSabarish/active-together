"""CLIP-based image/text scoring — the implementation behind the /score route.

Scores each prompt independently against the image (cosine similarity between
normalised CLIP embeddings), not a softmax distribution across prompts, so a
photo can score well on more than one prompt at once. B25 measures real
thresholds against whatever range these scores fall in.
"""

from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError


class InvalidImageError(ValueError):
    """Raised when the given bytes cannot be decoded as an image."""


class ClipScorer:
    def __init__(self, model_name: str, device: str) -> None:
        self._model_name = model_name
        self._device = device
        self._model = None
        self._processor = None

    def load(self) -> None:
        from transformers import CLIPModel, CLIPProcessor

        self._model = CLIPModel.from_pretrained(self._model_name).to(self._device)
        self._model.eval()
        self._processor = CLIPProcessor.from_pretrained(self._model_name)

    def warm(self) -> None:
        blank = Image.new("RGB", (224, 224), color=(128, 128, 128))
        self.score(_image_to_bytes(blank), ["warm-up"])

    def score(self, image_bytes: bytes, prompts: list[str]) -> list[float]:
        if self._model is None or self._processor is None:
            raise RuntimeError("ClipScorer.load() must be called before score()")

        import torch

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except UnidentifiedImageError as exc:
            raise InvalidImageError("Could not decode image bytes") from exc

        inputs = self._processor(text=prompts, images=image, return_tensors="pt", padding=True)
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            image_features = self._model.get_image_features(pixel_values=inputs["pixel_values"])
            text_features = self._model.get_text_features(
                input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"]
            )

        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        similarities = (image_features @ text_features.T).squeeze(0)

        return similarities.tolist()


def _image_to_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
