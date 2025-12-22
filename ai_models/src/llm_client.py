"""Gemini LLM client wrapper for Finbot."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence

import google.generativeai as genai

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-1.5-flash"


class LLMClient:
    """Asynchronous Gemini client for text generation and chat."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        *,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set. Please add it to your environment.")

        genai.configure(api_key=self.api_key)
        self.model_name = model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL
        self._generation_config = generation_config or {}
        self._model = genai.GenerativeModel(self.model_name)

    async def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Generate text from a single prompt string."""

        return await asyncio.to_thread(self._generate_sync, prompt, system, temperature)

    async def chat(
        self,
        messages: Sequence[Dict[str, str]],
        *,
        temperature: float = 0.2,
    ) -> str:
        """Chat-style interaction using a list of role/content messages."""

        return await asyncio.to_thread(self._chat_sync, messages, temperature)

    def _generate_sync(self, prompt: str, system: Optional[str], temperature: float) -> str:
        contents: List[Dict[str, Any]] = []
        if system:
            contents.append({"role": "system", "parts": [system]})
        contents.append({"role": "user", "parts": [prompt]})
        try:
            response = self._model.generate_content(
                contents,
                generation_config={"temperature": temperature, **self._generation_config},
            )
        except Exception as exc:  # pragma: no cover - network error
            logger.exception("Gemini generate_content failed")
            raise RuntimeError("Gemini generation failed") from exc
        return (response.text or "").strip()

    def _chat_sync(self, messages: Sequence[Dict[str, str]], temperature: float) -> str:
        contents = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content")
            if not content:
                continue
            contents.append({"role": role, "parts": [content]})
        if not contents:
            raise ValueError("messages must contain at least one entry with content")
        try:
            response = self._model.generate_content(
                contents,
                generation_config={"temperature": temperature, **self._generation_config},
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("Gemini chat failed")
            raise RuntimeError("Gemini chat failed") from exc
        return (response.text or "").strip()
