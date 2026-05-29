"""
ChromaDB retrieval for Vera's RAG context.
"""
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from app.config import get_settings

_COLLECTION = "billie_jean_law"


def retrieve(query: str, n_results: int = 4) -> tuple[str, list[str]]:
    settings = get_settings()
    try:
        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        client = chromadb.PersistentClient(path=settings.chroma_path)
        col = client.get_collection(_COLLECTION, embedding_function=ef)
        count = col.count()
        if count == 0:
            return "", []
        results = col.query(query_texts=[query], n_results=min(n_results, count))
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        sources = list({m.get("source", "knowledge_base") for m in metas})
        return "\n\n---\n\n".join(docs), sources
    except Exception:
        return "", []
