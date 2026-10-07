"""open_clip image/text scoring — the implementation behind the /score route.

Scores one prompt against one image: cosine similarity between normalised
CLIP embeddings. It is not a softmax across prompts, so the number means the
same thing whatever else is asked. B54 measures a threshold per prompt against
this range.

The image arrives as bytes and is decoded in memory. Nothing is written to
disk and nothing is logged.
"""

from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError


class InvalidImageError(ValueError):
    """Raised when the given bytes cannot be decoded as an image."""


class OpenClipScorer:
    def __init__(self, model_name: str, pretrained: str, device: str) -> None:
        self._model_name = model_name
        self._pretrained = pretrained
        self._device = device
        self._model = None
        self._preprocess = None
        self._tokenizer = None

    def load(self) -> None:
        import open_clip

        model, _, preprocess = open_clip.create_model_and_transforms(
            self._model_name, pretrained=self._pretrained, device=self._device
        )
        model.eval()
        self._model = model
        self._preprocess = preprocess
        self._tokenizer = open_clip.get_tokenizer(self._model_name)

    def warm(self) -> None:
        blank = Image.new("RGB", (224, 224), color=(128, 128, 128))
        self.score(_image_to_bytes(blank), "warm-up")

    def score(self, image_bytes: bytes, prompt: str) -> float:
        if self._model is None:
            raise RuntimeError("OpenClipScorer.load() must be called before score()")

        import torch

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except (UnidentifiedImageError, OSError) as exc:
            raise InvalidImageError("Could not decode image bytes") from exc

        image_input = self._preprocess(image).unsqueeze(0).to(self._device)
        text_input = self._tokenizer([prompt]).to(self._device)

        with torch.no_grad():
            image_features = self._model.encode_image(image_input)
            text_features = self._model.encode_text(text_input)

        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        return float((image_features @ text_features.T).item())


def _image_to_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
