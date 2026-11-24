import httpx
from anthropic import Anthropic

from app.config import settings

_anthropic_client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None


def _split_system(messages: list[dict]) -> tuple[str, list[dict]]:
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    return "\n\n".join(system_parts), rest


def call_claude(messages: list[dict], max_tokens: int = 1024) -> str:
    if _anthropic_client is None:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured on this gateway")
    system, convo = _split_system(messages)
    resp = _anthropic_client.messages.create(
        model=settings.anthropic_model,
        system=system or None,
        messages=convo,
        max_tokens=max_tokens,
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def call_local(messages: list[dict], max_tokens: int = 1024) -> str:
    resp = httpx.post(
        f"{settings.ollama_base_url}/api/chat",
        json={"model": settings.ollama_model, "messages": messages, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def route(messages: list[dict], backend: str, max_tokens: int = 1024) -> tuple[str, str]:
    """Returns (reply_text, backend_actually_used)."""
    if backend == "local":
        return call_local(messages, max_tokens), "local"
    if backend == "claude":
        return call_claude(messages, max_tokens), "claude"
    if backend == "auto":
        # heuristic: short, simple-looking last user message -> local; else claude
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if len(last_user) < 200 and "```" not in last_user:
            try:
                return call_local(messages, max_tokens), "local"
            except Exception:
                pass
        return call_claude(messages, max_tokens), "claude"
    raise ValueError(f"unknown backend: {backend}")
