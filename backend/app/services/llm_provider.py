from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx
from loguru import logger

from app.core.config import settings


class LLMProviderError(Exception):
    """Raised when a language model provider fails."""


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system_prompt: str) -> str:
        raise NotImplementedError


class RuleBasedLLMProvider(LLMProvider):
    async def complete(self, prompt: str, system_prompt: str) -> str:
        del system_prompt
        return prompt.strip()


class _OpenAICompatibleProvider(LLMProvider):
    provider_name = "openai"

    def __init__(
        self,
        api_key: str,
        model_name: str,
        base_url: str,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    async def complete(self, prompt: str, system_prompt: str) -> str:
        if not self.api_key:
            raise LLMProviderError(f"{self.provider_name} API key is not configured.")

        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.exception("LLM provider call failed")
            raise LLMProviderError("Language model request failed.") from exc


class OpenAILLMProvider(_OpenAICompatibleProvider):
    provider_name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        super().__init__(
            api_key=api_key or settings.openai_api_key,
            model_name=model_name or settings.llm_model_name,
            base_url="https://api.openai.com/v1",
        )


class GroqLLMProvider(_OpenAICompatibleProvider):
    provider_name = "groq"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        super().__init__(
            api_key=api_key or settings.groq_api_key,
            model_name=model_name or settings.llm_model_name,
            base_url="https://api.groq.com/openai/v1",
        )


def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider.lower().strip()
    if provider == "openai":
        return OpenAILLMProvider()
    if provider == "groq":
        return GroqLLMProvider()

    return RuleBasedLLMProvider()
