import os

from config import settings

from .base import AIProvider, AnalysisResult, Incident, IncidentReport
from .claude import ClaudeProvider
from .mock import MockProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider


def get_provider() -> AIProvider:
    provider = os.getenv("AI_PROVIDER", "mock").lower()
    match provider:
        case "mock":
            return MockProvider()
        case "claude":
            return ClaudeProvider(api_key=os.environ["ANTHROPIC_API_KEY"])
        case "openai":
            return OpenAIProvider(api_key=os.environ["OPENAI_API_KEY"])
        case "ollama":
            return OllamaProvider(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
            )
        case _:
            raise ValueError(f"Unknown AI_PROVIDER: {provider}")


__all__ = [
    "AIProvider",
    "AnalysisResult",
    "Incident",
    "IncidentReport",
    "get_provider",
]
