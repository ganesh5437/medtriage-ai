"""
rag.py — RAG (Retrieval-Augmented Generation) engine using ChromaDB.
Loads medical knowledge from JSON, embeds it, stores in local ChromaDB for Phase 1-5 dev.
Phase 6+ can swap to Pinecone via PINECONE_API_KEY env var.

Embeddings: OpenAI's text-embedding-3-small via openai package (free tier).
Falls back to mock embeddings if API not available (gap-fix: graceful degradation).
"""
import json
import logging
import os
from pathlib import Path

import chromadb

from app.config import settings

logger = logging.getLogger("medtriage.rag")

# ChromaDB client (persistent local storage) — new API
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

# Collection name
COLLECTION_NAME = "medical_knowledge"


def _get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for texts. Falls back to mock if API unavailable
    (gap-fix: error handling).
    Mock embeddings: simple hash-based 384-dim vector for demo.
    """
    try:
        # Try real OpenAI embeddings (Phase 2+)
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY or "")
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [item.embedding for item in response.data]
    except Exception as exc:
        logger.warning("OpenAI embeddings failed, using mock: %s", exc)
        # Mock: hash-based deterministic vectors (384 dims for compat)
        return [_mock_embedding(t) for t in texts]


def _mock_embedding(text: str, dim: int = 384) -> list[float]:
    """Mock embedding: hash text into a vector. Deterministic for testing."""
    import hashlib
    text_hash = hashlib.md5(text.encode()).hexdigest()
    seed = int(text_hash, 16)
    import random
    random.seed(seed)
    return [random.gauss(0, 1) for _ in range(dim)]


def load_knowledge_base() -> None:
    """
    Load symptoms_conditions.json into ChromaDB.
    Idempotent: if collection exists, skips loading.
    """
    knowledge_path = Path(__file__).parent.parent / "knowledge_base" / "symptoms_conditions.json"
    
    if not knowledge_path.exists():
        logger.error("Knowledge base file not found at %s", knowledge_path)
        return

    try:
        collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Check if already loaded (if collection has documents, skip)
        if collection.count() > 0:
            logger.info("Knowledge base already loaded (%d docs)", collection.count())
            return

        with open(knowledge_path) as f:
            data = json.load(f)

        # Prepare documents, embeddings, metadatas for ChromaDB
        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for entry in data:
            doc_id = entry["id"]
            # Embedding input: concat symptoms, condition, description
            embed_text = f"{' '.join(entry['symptoms'])} {entry['condition']} {entry['description']}"
            documents.append(embed_text)
            ids.append(doc_id)
            metadatas.append({
                "condition": entry["condition"],
                "symptoms": ",".join(entry["symptoms"]),
                "description": entry["description"],
                "recommended_tests": ",".join(entry.get("recommended_tests", [])),
                "red_flags": ",".join(entry.get("red_flags", [])),
            })

        # Generate embeddings in batch
        logger.info("Generating embeddings for %d knowledge entries...", len(documents))
        embeddings = _get_embeddings(documents)

        # Add to ChromaDB
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Knowledge base loaded: %d documents in ChromaDB", len(ids))

    except Exception as exc:
        logger.error("Failed to load knowledge base: %s", exc)


def retrieve_relevant_knowledge(symptoms: list[str], top_k: int = 5) -> list[dict]:
    """
    Query ChromaDB for relevant medical knowledge given symptoms.
    Returns top_k most relevant entries with scores.
    """
    try:
        if not symptoms:
            return []

        collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Ensure KB is loaded
        if collection.count() == 0:
            load_knowledge_base()
            if collection.count() == 0:
                logger.warning("Knowledge base empty, returning empty results")
                return []

        # Query text: just the symptoms
        query_text = " ".join(symptoms)
        query_embedding = _get_embeddings([query_text])[0]

        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        retrieved = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                # ChromaDB returns L2 distance; convert to similarity (1 - normalized distance)
                similarity = max(0, 1 - distance)  # clamp to 0-1
                metadata = results["metadatas"][0][i]
                retrieved.append({
                    "id": doc_id,
                    "condition": metadata.get("condition", "Unknown"),
                    "description": metadata.get("description", ""),
                    "symptoms": metadata.get("symptoms", "").split(","),
                    "recommended_tests": metadata.get("recommended_tests", "").split(","),
                    "red_flags": metadata.get("red_flags", "").split(","),
                    "similarity": round(similarity, 2),
                })

        return retrieved

    except Exception as exc:
        logger.error("RAG retrieval failed: %s", exc)
        return []
