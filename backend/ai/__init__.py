import os

from .base import AIProvider, AnalysisResult
from .mock import MockProvider
from .claude import ClaudeProvider
from .openai import OpenAIProvider
from .ollama import OllamaProvider


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
            return OllamaProvider(base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        case _:
            raise ValueError(f"Unknown AI_PROVIDER: {provider}")


__all__ = ["AIProvider", "AnalysisResult", "get_provider"]
