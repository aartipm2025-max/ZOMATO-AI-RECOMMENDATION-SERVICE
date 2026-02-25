from __future__ import annotations

import os
from dataclasses import dataclass

from groq import Groq


@dataclass(frozen=True)
class GroqConfig:
    api_key: str
    model: str


def load_groq_config_from_env() -> GroqConfig:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY in environment (.env)")

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile"
    return GroqConfig(api_key=api_key, model=model)


class GroqLLMClient:
    def __init__(self, config: GroqConfig) -> None:
        self._config = config
        self._client = Groq(api_key=config.api_key)

    @property
    def model(self) -> str:
        return self._config.model

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        """
        Call Groq chat completions and return the raw response content.
        """
        resp = self._client.chat.completions.create(
            model=self._config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""

