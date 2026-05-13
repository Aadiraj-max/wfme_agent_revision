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
        tables = bsl_mapping.get("tables", {})
        synonyms_dict = bsl_mapping.get("synonyms", {})

        # CATEGORY 1 — TABLE DOCUMENTS
        for key, info in tables.items():
            physical_name = info.get("physical_name", "")
            domain = info.get("domain", "")
            description = info.get("description", "")
            columns = list(info.get("columns", {}).keys())
            columns_str = ", ".join(columns)
            pks = info.get("primary_keys", [])
            pks_str = ", ".join(pks)
            
            # Construct use_case_string
            col_descriptions = []
            for col_info in info.get("columns", {}).values():
                desc = col_info.get("description", "").strip()
                if desc:
                    if not desc.endswith('.'):
                        desc += "."
                    col_descriptions.append(desc)
            
            use_case_parts = [description] if description.endswith('.') else [f"{description}."]
            use_case_parts.extend(col_descriptions)
            
            if domain == "HR":
                use_case_parts.append("HR domain: employee data, workforce, personnel.")
            elif domain == "OPS":
                use_case_parts.append("OPS domain: scheduling, operations, attendance, shifts.")
            
            use_case_string = " ".join(use_case_parts)

            warnings = info.get("warnings", [])
            warnings_str = " ".join(warnings) if warnings else "None"

            text = (
                f"Table: {key}\n"
                f"Physical name: {physical_name}\n"
                f"Domain: {domain}\n"
                f"Description: {description}\n"
                f"Columns: {columns_str}\n"
                f"Key columns: {pks_str}\n"
                f"Use this table to answer questions about: {use_case_string}\n"
                f"Warnings: {warnings_str}"
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

        # CATEGORY 2 — METRIC DOCUMENTS
        for key, info in bsl_mapping.get("metrics", {}).items():
            description = info.get("description", "")
            table_key = info.get("table", "")
            column = info.get("column", "")
            aggregation = info.get("aggregation", "")
            
            # Domain lookup
            domain = tables.get(table_key, {}).get("domain", "Unknown")
            
            # Synonym lookup
            synonyms = [s for s, m in synonyms_dict.items() if m == key]
            synonyms_str = ", ".join(synonyms) if synonyms else "none"
            
            # Generate 3 example questions
            q_term = synonyms[0] if synonyms else key.replace("_", " ")
            q1 = f"How many {q_term} are in the company?"
            q2 = f"What is the total {key.replace('_', ' ')}?"
            q3 = f"Can you show the {synonyms[1] if len(synonyms) > 1 else q_term} for our staff?"
            questions_str = f"{q1} {q2} {q3}"

            text = (
                f"Metric: {key}\n"
                f"Description: {description}\n"
                f"Source table: {table_key}\n"
                f"Source column: {column}\n"
                f"Aggregation: {aggregation}\n"
                f"Domain: {domain}\n"
                f"Synonyms: {synonyms_str}\n"
                f"Use this metric to answer questions about: {description} Questions like: {questions_str}"
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

        # CATEGORY 3 — DIMENSION DOCUMENTS
        for key, info in bsl_mapping.get("dimensions", {}).items():
            description = info.get("description", "")
            table_key = info.get("table", "")
            column = info.get("column", "")
            
            # Domain lookup
            domain = tables.get(table_key, {}).get("domain", "Unknown")
            
            # Synonym lookup
            synonyms = [s for s, d in synonyms_dict.items() if d == key]
            synonyms_str = ", ".join(synonyms) if synonyms else "none"

            text = (
                f"Dimension: {key}\n"
                f"Description: {description}\n"
                f"Source table: {table_key}\n"
                f"Source column: {column}\n"
                f"Domain: {domain}\n"
                f"Synonyms: {synonyms_str}\n"
                f"Use this dimension to group or filter by: {description} Group queries by {key} to break down results. Example: \"headcount by {key}\", \"leave balance per {key}\""
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

    def rebuild_index(self, bsl_mapping: dict) -> int:
        """
        Deletes the existing ChromaDB collection and rebuilds from scratch.
        Use this when BSL mapping has changed and a clean re-index is needed.
        """
        print("Rebuilding index from scratch...")
        try:
            self.client.delete_collection("bsl_concepts")
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(name="bsl_concepts")
        total = self.build_index(bsl_mapping)
        print("Index rebuilt successfully.")
        return total

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
    print("Starting full index rebuild...")
    total = store.rebuild_index(BSL_MAPPING)
    print(f"Total documents indexed: {total}")
    print("Testing search...")
    test_query = "total headcount by employee role and location"
    results = store.search(test_query)
    for res in results:
        print(f"[{res['similarity']:.4f}] {res['type'].upper()}: {res['key']}")
