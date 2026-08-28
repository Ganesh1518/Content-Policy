"""
src/config.py
--------------
Single source of truth for configuration. Loads config/config.yaml plus
environment variables from .env (NFR-01: no secrets committed; NFR-04:
retrieval parameters externalized).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "config.yaml"

load_dotenv(ROOT_DIR / ".env")


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (ROOT_DIR / p)


class Config:
    """Thin wrapper exposing dotted access over the YAML config tree."""

    def __init__(self, raw: dict[str, Any]):
        self._raw = raw

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return cls(raw)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        node = self._raw
        for part in dotted_key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    # Convenience resolved paths -------------------------------------------------
    @property
    def corpus_dir(self) -> Path:
        return _resolve(self.get("corpus.path", "data/corpus"))

    @property
    def vector_store_dir(self) -> Path:
        return _resolve(self.get("vector_store.persist_dir", "data/vector_store/chroma"))

    @property
    def gemini_api_key(self) -> str | None:
        return os.getenv("GEMINI_API_KEY")

    @property
    def model_primary(self) -> str:
        return os.getenv("GEMINI_MODEL_PRIMARY", self.get("generation.model_primary"))

    @property
    def model_challenger(self) -> str:
        return os.getenv("GEMINI_MODEL_CHALLENGER", self.get("generation.model_challenger"))


CONFIG = Config.load()
