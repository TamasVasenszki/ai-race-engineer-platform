from .base import AIProvider, AnalysisResult


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self._api_key = api_key
        self._model = model

    async def analyze_lap(self, lap_data: dict) -> AnalysisResult:
        raise NotImplementedError("OpenAIProvider — implement in Phase 2")
