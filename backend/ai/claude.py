from .base import AIProvider, AnalysisResult


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self._api_key = api_key
        self._model = model

    async def analyze_lap(self, lap_data: dict) -> AnalysisResult:
        raise NotImplementedError("ClaudeProvider — implement in Phase 2")
