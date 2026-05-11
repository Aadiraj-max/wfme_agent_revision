import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import time
from typing import List, Dict
import chromadb
from dotenv import load_dotenv

from src.retrieval.embedder import GeminiEmbedder
from src.engine.bsl_dictionary import BSL_MAPPING

load_dotenv()

CHROMA_PERSIST_DIR = "data/chroma_store"


class BSLVectorStore:
    """
    Builds and queries a ChromaDB vector store for BSL concepts
    (tables, metrics, dimensions).
    """

    def __init__(self, embedder: GeminiEmbedder = None, persist_dir: str = CHROMA_PERSIST_DIR):
        """Initializes the vector store and its persistent ChromaDB client."""
        if not os.path.exists(persist_dir):
            os.makedirs(persist_dir)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name="bsl_concepts")
        self.embedder = embedder or GeminiEmbedder()

    def build_index(self, bsl_mapping: dict) -> int:
        """
        Indexes all BSL concepts into ChromaDB.
        One document per table, metric, and dimension.
        Uses upsert so re-indexing is safe.
        Returns total number of documents indexed.
        """
        total_indexed = 0

        for key, info in bsl_mapping.get("tables", {}).items():
            text = (
                f"Table: {key}. "
                f"Physical name: {info.get('physical_name', '')}. "
                f"Description: {info.get('description', '')}. "
                f"Domain: {info.get('domain', '')}."
            )
            vector = self.embedder.embed(text)
            self.collection.upsert(
                ids=[f"table::{key}"],
                embeddings=[vector],
                documents=[text],
                metadatas=[{"type": "table", "key": key}]
            )
            total_indexed += 1
            time.sleep(0.6)
            if total_indexed % 10 == 0:
                print(f"Indexed {total_indexed} items...")

        for key, info in bsl_mapping.get("metrics", {}).items():
            synonyms_str = ", ".join(info.get("synonyms", [])) or "none"
            text = (
                f"Metric: {key}. "
                f"Description: {info.get('description', '')}. "
                f"Synonyms: {synonyms_str}."
            )
            vector = self.embedder.embed(text)
            self.collection.upsert(
                ids=[f"metric::{key}"],
                embeddings=[vector],
                documents=[text],
                metadatas=[{"type": "metric", "key": key}]
            )
            total_indexed += 1
            time.sleep(0.6)
            if total_indexed % 10 == 0:
                print(f"Indexed {total_indexed} items...")

        for key, info in bsl_mapping.get("dimensions", {}).items():
            synonyms_str = ", ".join(info.get("synonyms", [])) or "none"
            text = (
                f"Dimension: {key}. "
                f"Description: {info.get('description', '')}. "
                f"Synonyms: {synonyms_str}."
            )
            vector = self.embedder.embed(text)
            self.collection.upsert(
                ids=[f"dimension::{key}"],
                embeddings=[vector],
                documents=[text],
                metadatas=[{"type": "dimension", "key": key}]
            )
            total_indexed += 1
            time.sleep(0.6)
            if total_indexed % 10 == 0:
                print(f"Indexed {total_indexed} items...")

        return total_indexed

    def search(self, query: str, top_k: int = 10, threshold: float = 0.75) -> list[dict]:
        """
        Embeds query, searches ChromaDB, converts L2 distance to cosine
        similarity, filters by threshold, returns sorted results.

        Args:
            query: Natural language search query.
            top_k: Max results to retrieve before threshold filtering.
            threshold: Minimum cosine similarity to include a result.

        Returns:
            List of dicts with keys: id, type, key, similarity, document.
        """
        vector = self.embedder.embed(query)
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        if not results["ids"] or not results["ids"][0]:
            return []

        formatted = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            similarity = 1 - (distance / 2)
            if similarity >= threshold:
                formatted.append({
                    "id": results["ids"][0][i],
                    "type": results["metadatas"][0][i]["type"],
                    "key": results["metadatas"][0][i]["key"],
                    "similarity": similarity,
                    "document": results["documents"][0][i]
                })

        formatted.sort(key=lambda x: x["similarity"], reverse=True)
        return formatted

    def get_collection_count(self) -> int:
        """Returns total number of documents in the collection."""
        return self.collection.count()


if __name__ == "__main__":
    store = BSLVectorStore()
    test_query = "total headcount by employee role and location"
    print(f"Testing search for: '{test_query}'")
    results = store.search(test_query)
    for res in results:
        print(f"[{res['similarity']:.4f}] {res['type'].upper()}: {res['key']}")
