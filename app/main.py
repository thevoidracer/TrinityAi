import time
import uuid

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.backends import route
from app.rag import build_context_block, ingest

app = FastAPI(title="Trinity AI Gateway")


def check_auth(authorization: str | None) -> None:
    expected = f"Bearer {settings.gateway_api_key}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid or missing API key")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None  # "local" to force the local model, otherwise default_backend
    messages: list[ChatMessage]
    max_tokens: int = 1024


class IngestRequest(BaseModel):
    doc_id: str | None = None
    text: str
    metadata: dict | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequest, authorization: str | None = Header(default=None)):
    check_auth(authorization)

    backend = "local" if req.model == "local" else settings.default_backend
    messages = [m.model_dump() for m in req.messages]

    if settings.rag_enabled:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        context_block = build_context_block(last_user) if last_user else ""
    else:
        context_block = ""

    system_prefix = settings.persona + context_block
    messages = [{"role": "system", "content": system_prefix}] + messages

    try:
        reply, used = route(messages, backend, req.max_tokens)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "backend_used": used,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": reply},
                "finish_reason": "stop",
            }
        ],
    }


@app.post("/v1/ingest")
def ingest_doc(req: IngestRequest, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    doc_id = req.doc_id or uuid.uuid4().hex
    ingest(doc_id, req.text, req.metadata)
    return {"status": "ingested", "doc_id": doc_id}
