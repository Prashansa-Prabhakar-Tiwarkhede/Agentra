"""
AI provider abstraction. The rest of the app only ever imports
`get_ai_provider()` and calls `.complete_json(...)` — swapping Groq for
another provider means writing one new class here, nothing else changes.
"""
import json
from abc import ABC, abstractmethod

from app.config import get_settings

settings = get_settings()


class AIProvider(ABC):
    @abstractmethod
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Return a parsed JSON dict from the model. Must never raise on malformed JSON —
        callers get a structured error dict instead so a bad AI response can't crash checkout."""
        raise NotImplementedError


class GroqProvider(AIProvider):
    def __init__(self):
        from groq import Groq
        if not settings.groq_api_key:
            self._client = None
        else:
            self._client = Groq(api_key=settings.groq_api_key)

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if self._client is None:
            return {"error": "AI_UNAVAILABLE", "detail": "GROQ_API_KEY is not configured."}
        try:
            resp = self._client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            raw = resp.choices[0].message.content
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": "AI_MALFORMED_RESPONSE", "detail": "Model did not return valid JSON."}
        except Exception as e:  # network errors, rate limits, etc.
            return {"error": "AI_UNAVAILABLE", "detail": str(e)}


_provider_instance: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    global _provider_instance
    if _provider_instance is None:
        if settings.ai_provider == "groq":
            _provider_instance = GroqProvider()
        else:
            raise ValueError(f"Unknown AI_PROVIDER: {settings.ai_provider}")
    return _provider_instance
