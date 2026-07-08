import sys
import os
import time
from typing import List, Dict, Any, Optional
import chromadb
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.retrieval.embedder import GeminiEmbedder
from src.engine.schema_reflector import SchemaReflector

load_dotenv()

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
CHROMA_PERSIST_DIR = os.path.join(base_dir, "chroma_store")

class BSLVectorStore:
    """
    Builds and queries a ChromaDB vector store for dynamic Cube metadata
    (cubes, measures, and dimensions).
    """

    def __init__(self, embedder: Optional[GeminiEmbedder] = None, persist_dir: str = CHROMA_PERSIST_DIR):
        """Initializes the vector store and its persistent ChromaDB client."""
        if not os.path.exists(persist_dir):
            os.makedirs(persist_dir)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name="dynamic_cube_meta")
        self.embedder = embedder or GeminiEmbedder()

    def build_index(self, filtered_meta: Dict[str, Any]) -> int:
        """
        Indexes all live measures, dimensions, and cubes into ChromaDB.
        Uses upsert so re-indexing is safe.
        Returns total number of items indexed.
        """
        cubes = filtered_meta.get("cubes", [])

        ids = []
        documents = []
        metadatas = []

        for cube in cubes:
            cube_name = cube["name"]
            cube_title = cube["title"]

            # 1. Cube Document
            cube_text = (
                f"Cube: {cube_name}\n"
                f"Title: {cube_title}\n"
                f"Description: Use this cube/table to answer questions about {cube_title} and its metrics."
            )
            ids.append(f"cube::{cube_name}")
            documents.append(cube_text)
            metadatas.append({"type": "cube", "key": cube_name, "cube": cube_name})

            # 2. Measure Documents
            for measure in cube.get("measures", []):
                m_name = measure["name"]
                m_title = measure["title"]
                m_type = measure.get("type", "number")
                
                measure_text = (
                    f"Measure: {m_name}\n"
                    f"Title: {m_title}\n"
                    f"Type: {m_type}\n"
                    f"Cube: {cube_name}\n"
                    f"Description: Use this metric/measure to calculate or aggregate {m_title} from {cube_name}."
                )
                ids.append(f"measure::{m_name}")
                documents.append(measure_text)
                metadatas.append({"type": "measure", "key": m_name, "cube": cube_name})

            # 3. Dimension Documents
            for dim in cube.get("dimensions", []):
                d_name = dim["name"]
                d_title = dim["title"]
                d_type = dim.get("type", "string")

                dim_text = (
                    f"Dimension: {d_name}\n"
                    f"Title: {d_title}\n"
                    f"Type: {d_type}\n"
                    f"Cube: {cube_name}\n"
                    f"Description: Use this dimension to group, break down, or filter by {d_title} in {cube_name}."
                )
                ids.append(f"dimension::{d_name}")
                documents.append(dim_text)
                metadatas.append({"type": "dimension", "key": d_name, "cube": cube_name})

        # Generate embeddings in batch
        print(f"[VectorStore] Generating embeddings for {len(documents)} documents in batch...")
        embeddings = self.embedder.embed_batch(documents)

        # Upsert in chunks of 100
        chunk_size = 100
        total_indexed = 0
        for i in range(0, len(ids), chunk_size):
            chunk_ids = ids[i:i + chunk_size]
            chunk_embeddings = embeddings[i:i + chunk_size]
            chunk_documents = documents[i:i + chunk_size]
            chunk_metadatas = metadatas[i:i + chunk_size]

            self.collection.upsert(
                ids=chunk_ids,
                embeddings=chunk_embeddings,
                documents=chunk_documents,
                metadatas=chunk_metadatas
            )
            total_indexed += len(chunk_ids)

        return total_indexed

    def rebuild_index(self, filtered_meta: Dict[str, Any]) -> int:
        """
        Deletes the existing collection and rebuilds from scratch.
        """
        print("[VectorStore] Rebuilding index from scratch...")
        try:
            self.client.delete_collection("dynamic_cube_meta")
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(name="dynamic_cube_meta")
        total = self.build_index(filtered_meta)
        print(f"[VectorStore] Index rebuilt successfully with {total} items.")
        return total

    def search(self, query: str, top_k: int = 10, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Embeds query, searches ChromaDB, converts L2 distance to cosine
        similarity, filters by threshold, returns sorted results.
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
                    "cube": results["metadatas"][0][i]["cube"],
                    "similarity": similarity,
                    "document": results["documents"][0][i]
                })

        formatted.sort(key=lambda x: x["similarity"], reverse=True)
        return formatted

    def get_collection_count(self) -> int:
        """Returns total number of documents in the collection."""
        return self.collection.count()

if __name__ == "__main__":
    reflector = SchemaReflector()
    meta = reflector.fetch_and_filter()
    store = BSLVectorStore()
    total = store.rebuild_index(meta)
    print(f"Total documents indexed: {total}")
    
    test_query = "total headcount by gender"
    results = store.search(test_query)
    print(f"\nSearch results for '{test_query}':")
    for res in results:
        print(f"[{res['similarity']:.4f}] {res['type'].upper()} ({res['cube']}): {res['key']}")
