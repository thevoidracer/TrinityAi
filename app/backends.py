from anthropic import Anthropic
from llama_cpp import Llama

from app.config import settings

_anthropic_client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None

_local_llm: Llama | None = None


def _get_local_llm() -> Llama:
    global _local_llm
    if _local_llm is None:
        _local_llm = Llama(
            model_path=settings.local_model_path,
            n_ctx=settings.local_model_ctx,
            n_threads=settings.local_model_threads,
            verbose=False,
        )
    return _local_llm


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
    llm = _get_local_llm()
    resp = llm.create_chat_completion(messages=messages, max_tokens=max_tokens)
    return resp["choices"][0]["message"]["content"]


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
