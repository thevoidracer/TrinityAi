from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # auth for YOUR gateway (your other apps send this, not any upstream key)
    gateway_api_key: str = "change-me"

    # upstream backends
    anthropic_api_key: str = ""  # optional; leave blank to run fully free/local
    anthropic_model: str = "claude-sonnet-5-5"

    local_model_path: str = "models/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
    local_model_ctx: int = 4096
    local_model_threads: int = 4

    # routing: "local" (free, default), "claude" (paid, optional), "auto" (simple -> local, else claude)
    default_backend: str = "local"

    # persona injected into every request as the system prompt prefix
    persona: str = (
        "You are Trinity, a general-purpose AI assistant built for this app. "
        "Be direct, helpful, and concise."
    )

    # RAG
    rag_enabled: bool = True
    rag_collection: str = "trinity_knowledge"
    rag_top_k: int = 4
    chroma_path: str = "./data/chroma"

    class Config:
        env_file = ".env"


settings = Settings()
