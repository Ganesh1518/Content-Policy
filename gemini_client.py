"""
src/llm/gemini_client.py
---------------------------
Thin wrapper around the Google Gemini API (the only approved model provider
per the business case, Section 4). Centralizes:
  - API key loading from the environment (never hard-coded, NFR-01)
  - basic retry-with-backoff so transient provider errors degrade gracefully
    rather than crashing the pipeline (NFR-05)
  - a single call path used by both generation and query transformation, so
    model swaps for the two-model comparison (AC-10) only touch config.
"""

from __future__ import annotations

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import CONFIG


class GeminiUnavailableError(RuntimeError):
    """Raised when the Gemini API cannot be reached after all retries."""


def _client_configured() -> bool:
    api_key = CONFIG.gemini_api_key
    if not api_key:
        return False
    genai.configure(api_key=api_key)
    return True


class GeminiClient:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or CONFIG.model_primary
        self._configured = _client_configured()

    @retry(
        stop=stop_after_attempt(CONFIG.get("generation.retries", 3)),
        wait=wait_exponential(multiplier=CONFIG.get("generation.retry_backoff_seconds", 2)),
        reraise=True,
    )
    def generate(self, prompt: str, response_schema: dict | None = None) -> str:
        """Returns raw text (JSON string when response_schema is provided)."""
        if not self._configured:
            raise GeminiUnavailableError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        model = genai.GenerativeModel(self.model_name)
        generation_config = {
            "temperature": CONFIG.get("generation.temperature", 0.0),
            "max_output_tokens": CONFIG.get("generation.max_output_tokens", 1024),
        }
        if response_schema is not None:
            generation_config["response_mime_type"] = "application/json"
            generation_config["response_schema"] = response_schema

        response = model.generate_content(prompt, generation_config=generation_config)
        return response.text
