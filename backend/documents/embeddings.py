from __future__ import annotations
import logging
import requests as http_requests
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from django.conf import settings

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        model_name = getattr(settings, 'EMBEDDING_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')
        logger.info(f"Ładowanie modelu embeddingów: {model_name}")
        _model = SentenceTransformer(model_name)
        logger.info("Model załadowany.")
    return _model





def get_chroma_client() -> chromadb.HttpClient:
    host = getattr(settings, 'CHROMA_HOST', 'chromadb')
    port = int(getattr(settings, 'CHROMA_PORT', 8000))
    return chromadb.HttpClient(
        host=host,
        port=port,
        settings=Settings(anonymized_telemetry=False),
    )

def get_or_create_collection(client: chromadb.HttpClient, name: str = 'documents'):
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_model()
    vectors = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return vectors.tolist()


def store_chunks_in_chroma(
    document_id: str,
    chunk_ids: list[str],
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
) -> None:
    client     = get_chroma_client()
    collection = get_or_create_collection(client)

    try:
        existing = collection.get(where={"document_id": document_id})
        if existing['ids']:
            collection.delete(ids=existing['ids'])
    except Exception:
        pass

    collection.add(
        ids=chunk_ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    logger.info(f"Zapisano {len(chunk_ids)} chunków w ChromaDB dla dokumentu {document_id}")


def query_similar_chunks(
    query_text: str,
    project_id: int | None = None,
    n_results: int = 5,
) -> list[dict]:
    query_embedding = embed_texts([query_text])[0]
    client          = get_chroma_client()
    collection      = get_or_create_collection(client)

    where = {"project_id": str(project_id)} if project_id else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=['documents', 'metadatas', 'distances'],
    )

    return [
        {
            'text':     doc,
            'distance': results['distances'][0][i],
            'metadata': results['metadatas'][0][i],
        }
        for i, doc in enumerate(results['documents'][0])
    ]