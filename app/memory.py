import time
import uuid

from app.rag import ingest, retrieve


def save_fact(text: str, verified: bool, confidence: str, sources: list[str]) -> str:
    fact_id = uuid.uuid4().hex
    ingest(
        fact_id,
        text,
        {
            "type": "fact",
            "verified": verified,
            "confidence": confidence,
            "sources": ", ".join(sources) if sources else "",
            "saved_at": int(time.time()),
        },
    )
    return fact_id


def recall(query: str, top_k: int = 4) -> list[str]:
    return retrieve(query, top_k)
