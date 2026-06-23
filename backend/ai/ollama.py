from .base import AIProvider, AnalysisResult


class OllamaProvider(AIProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3") -> None:
        self._base_url = base_url
        self._model = model

    async def analyze_lap(self, lap_data: dict) -> AnalysisResult:
        raise NotImplementedError("OllamaProvider — implement in Phase 5")
