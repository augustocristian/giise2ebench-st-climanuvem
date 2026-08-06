import asyncio
from dataclasses import dataclass

@dataclass
class AnalysisTask:
    analysis_id: int
    file_path: str
    fcm_token: str
    explainability: bool = False

# Global queue to hold analysis tasks
analysis_queue: asyncio.Queue = asyncio.Queue()
