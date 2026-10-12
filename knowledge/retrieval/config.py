import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalConfig:
    default_top_k: int = 5
    max_top_k: int = 10
    min_score: float = 0.50

    @classmethod
    def from_env(cls) -> "RetrievalConfig":
        return cls(
            default_top_k=int(
                os.getenv("RAG_TOP_K", "5")
            ),
            max_top_k=int(
                os.getenv("RAG_MAX_TOP_K", "10")
            ),
            min_score=float(
                os.getenv("RAG_MIN_SCORE", "0.50")
            ),
        )


retrieval_config = RetrievalConfig.from_env()