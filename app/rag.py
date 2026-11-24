import chromadb
from chromadb.utils import embedding_functions

from app.config import settings

_client = chromadb.PersistentClient(path=settings.chroma_path)
_embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
_collection = _client.get_or_create_collection(
    name=settings.rag_collection, embedding_function=_embedder
)


def ingest(doc_id: str, text: str, metadata: dict | None = None) -> None:
    _collection.upsert(ids=[doc_id], documents=[text], metadatas=[metadata or {}])


def retrieve(query: str, top_k: int | None = None) -> list[str]:
    k = top_k or settings.rag_top_k
    if _collection.count() == 0:
        return []
    results = _collection.query(query_texts=[query], n_results=min(k, _collection.count()))
    return results["documents"][0] if results["documents"] else []


def build_context_block(query: str) -> str:
    chunks = retrieve(query)
    if not chunks:
        return ""
    joined = "\n\n".join(f"- {c}" for c in chunks)
    return f"\n\nRelevant context from your knowledge base:\n{joined}"
