# app/core/vector_store.py

import uuid

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

embedding_model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
client = QdrantClient(path="./qdrant_storage")

COLLECTION_NAME = "cv_chunks"
VECTOR_SIZE = 384


def init_collection():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def embed(text: str) -> list[float]:
    return list(embedding_model.embed([text]))[0].tolist()


def store_cv_chunks(chunks: list[dict], cv_owner: str, session_id: str) -> int:
    init_collection()
    clear_session_data(session_id)

    points = []
    for chunk in chunks:
        vector = embed(chunk["text"])
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk["text"],
                    "section": chunk["section"],
                    "cv_owner": cv_owner,
                    "session_id": session_id,
                },
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def search_cv(query: str, session_id: str, top_k: int = 3) -> list[dict]:
    """
    Axtarış yalnız bu session_id-yə aid chunk-lar arasında gedir.
    Digər session-ların data-sı görünmür.
    """
    query_vector = embed(query)

    # Yalnız bu session-ın data-sını gör
    session_filter = Filter(
        must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
    )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=session_filter,
        limit=top_k,
    ).points

    return [
        {
            "text": r.payload["text"],
            "section": r.payload["section"],
            "score": round(r.score, 3),
        }
        for r in results
    ]


def clear_session_data(session_id: str) -> None:
    """
    Bu session-a aid bütün chunk-ları Qdrant-dan silir.
    Yeni CV yükləndikdə çağırılır.
    """
    if not client.collection_exists(COLLECTION_NAME):
        return

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
        ),
    )
