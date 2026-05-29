"""
Ingest knowledge base documents into ChromaDB.
"""
from pathlib import Path
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from app.config import get_settings

_KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"
_COLLECTION = "billie_jean_law"


def ingest_knowledge_base():
    settings = get_settings()
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=settings.chroma_path)

    try:
        col = client.get_collection(_COLLECTION, embedding_function=ef)
        if col.count() > 0:
            return
    except Exception:
        pass

    col = client.get_or_create_collection(_COLLECTION, embedding_function=ef)

    docs, ids, metas = [], [], []
    for kb_file in sorted(_KB_DIR.glob("*.txt")):
        text = kb_file.read_text(encoding="utf-8")
        chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 60]
        for i, chunk in enumerate(chunks):
            docs.append(chunk)
            ids.append(f"{kb_file.stem}_{i:04d}")
            metas.append({"source": kb_file.name, "stem": kb_file.stem})

    if docs:
        col.add(documents=docs, ids=ids, metadatas=metas)
