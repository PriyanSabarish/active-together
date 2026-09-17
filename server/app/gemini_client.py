"""
GeminiModelClient (B37) — this iteration's real ModelClient implementation.

Talks to the Gemini API directly over HTTP (no SDK dependency, matching
how app.data.weather calls WeatherAPI) with an explicit timeout, and
returns None on any failure — a bad response, a timeout, a network error,
an unexpected response shape — rather than raising, so every caller only
ever has one failure case to handle, exactly like FixtureModelClient.

Swapping this for a self-hosted HostedModelClient later (once the
inference service exists) only touches this file: nothing importing
ModelClient names Gemini, and B43 is where the swap plan itself gets
written down, not code.

response_schema (B41) turns on Gemini's native structured-output mode:
when set, Gemini is constrained to return JSON matching that schema
instead of free-form prose, so a caller can json.loads() the string
generate_text returns rather than regex-scraping it for fields. What the
schema actually looks like for mission generation specifically is B23's
concern, not this file's — this only wires the mechanism through.

thinking_budget (confirmed during manual verification,
scripts/verify_gemini.py): some Gemini models spend part of max_tokens on
an internal reasoning pass before any visible output, and a small budget
can be consumed entirely by it, leaving generate_text nothing to return
(gemini-3.6-flash does this). Other models reject thinkingConfig outright
with a 400 (gemini-3.5-flash-lite does this). There is no value that
works for every model, so thinking_budget defaults to None — meaning
"don't send thinkingConfig at all," i.e. whatever the current model's own
default is. Pass thinking_budget=0 explicitly for a model confirmed to
support and need disabling it.
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiModelClient:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        response_schema: dict | None = None,
        thinking_budget: int | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._response_schema = response_schema
        self._thinking_budget = thinking_budget

    def generate_text(self, prompt: str, max_tokens: int, timeout_s: int) -> str | None:
        url = f"{self._base_url}/models/{self._model}:generateContent"
        generation_config: dict = {"maxOutputTokens": max_tokens}
        if self._thinking_budget is not None:
            generation_config["thinkingConfig"] = {"thinkingBudget": self._thinking_budget}
        if self._response_schema is not None:
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseSchema"] = self._response_schema

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }

        try:
            response = httpx.post(url, params={"key": self._api_key}, json=payload, timeout=timeout_s)
        except httpx.RequestError as exc:
            logger.warning("Gemini request failed: %s", exc)
            return None

        if response.status_code != 200:
            logger.warning("Gemini returned %s: %s", response.status_code, response.text[:200])
            return None

        try:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, ValueError) as exc:
            logger.warning("Gemini response missing expected text: %s", exc)
            return None
