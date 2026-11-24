from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # auth for YOUR gateway (your other apps send this, not any upstream key)
    gateway_api_key: str = "change-me"

    # upstream backends
    anthropic_api_key: str = ""  # optional; leave blank to run fully free/local
    anthropic_model: str = "claude-sonnet-5-5"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

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
