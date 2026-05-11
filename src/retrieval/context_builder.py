import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import copy
import itertools
from src.retrieval.vector_store import BSLVectorStore
from src.graph.schema_graph import SchemaGraph
from src.engine.bsl_dictionary import BSL_MAPPING


class ContextBuilder:
    """
    Governor layer that combines vector search with graph traversal
    to produce a focused, pruned BSL context dict for LLM consumption.
    """

    def __init__(
        self,
        bsl_mapping: dict = None,
        vector_store: BSLVectorStore = None,
        schema_graph: SchemaGraph = None
    ):
        """Initializes ContextBuilder with injected dependencies."""
        self.bsl_mapping = bsl_mapping if bsl_mapping is not None else BSL_MAPPING
        self.vector_store = vector_store if vector_store is not None else BSLVectorStore()
        self.schema_graph = schema_graph if schema_graph is not None else SchemaGraph()

    def build_context(self, query: str, top_k: int = 10, threshold: float = 0.82) -> dict:
        """
        Builds a pruned BSL context from a natural language query.

        Step 1: Vector search — find relevant tables, metrics, dimensions.
        Step 2: Resolve parent tables from matched metrics and dimensions.
        Step 3: Graph expansion — add bridge tables needed for JOIN completeness.
        Step 4: Build and return pruned BSL context dict.

        Args:
            query: Natural language query string.
            top_k: Max candidates from vector search.
            threshold: Minimum cosine similarity threshold.

        Returns:
            Pruned dict with keys: tables, metrics, dimensions.
        """
        # Step 1 — Vector search
        results = self.vector_store.search(query, top_k, threshold)
        matched_table_keys = {r["key"] for r in results if r["type"] == "table"}
        matched_metric_keys = {r["key"] for r in results if r["type"] == "metric"}
        matched_dimension_keys = {r["key"] for r in results if r["type"] == "dimension"}

        # Step 2 — Resolve parent tables from metrics and dimensions
        for key in matched_metric_keys:
            if key in self.bsl_mapping["metrics"]:
                matched_table_keys.add(self.bsl_mapping["metrics"][key]["table"])
        for key in matched_dimension_keys:
            if key in self.bsl_mapping["dimensions"]:
                matched_table_keys.add(self.bsl_mapping["dimensions"][key]["table"])
        matched_table_keys = {k for k in matched_table_keys if k in self.bsl_mapping["tables"]}

        # Step 3 — Graph expansion for JOIN completeness
        physical_to_key = {
            info["physical_name"]: k
            for k, info in self.bsl_mapping["tables"].items()
        }
        physical_tables = [
            self.bsl_mapping["tables"][k]["physical_name"]
            for k in matched_table_keys
            if k in self.bsl_mapping["tables"]
        ]
        for table_a, table_b in itertools.combinations(physical_tables, 2):
            path = self.schema_graph.get_join_path(table_a, table_b)
            if path and len(path) == 3:
                for physical_name in path[1:-1]:
                    if physical_name in physical_to_key:
                        matched_table_keys.add(physical_to_key[physical_name])
        matched_table_keys = {k for k in matched_table_keys if k in self.bsl_mapping["tables"]}

        # Step 4 — Build pruned context
        return {
            "tables": {
                k: copy.deepcopy(self.bsl_mapping["tables"][k])
                for k in matched_table_keys
                if k in self.bsl_mapping["tables"]
            },
            "metrics": {
                k: copy.deepcopy(self.bsl_mapping["metrics"][k])
                for k in matched_metric_keys
                if k in self.bsl_mapping["metrics"]
            },
            "dimensions": {
                k: copy.deepcopy(self.bsl_mapping["dimensions"][k])
                for k in matched_dimension_keys
                if k in self.bsl_mapping["dimensions"]
            }
        }

    def get_context_summary(self, context: dict) -> str:
        """
        Returns a human-readable summary of the pruned context.

        Returns:
            String in format:
            "Tables (n): k1, k2 | Metrics (n): k1, k2 | Dimensions (n): k1, k2"
        """
        t_keys = sorted(context["tables"].keys())
        m_keys = sorted(context["metrics"].keys())
        d_keys = sorted(context["dimensions"].keys())
        return (
            f"Tables ({len(t_keys)}): {', '.join(t_keys)} | "
            f"Metrics ({len(m_keys)}): {', '.join(m_keys)} | "
            f"Dimensions ({len(d_keys)}): {', '.join(d_keys)}"
        )


if __name__ == "__main__":
    builder = ContextBuilder()
    test_query = "total headcount by employee role and location"
    print(f"Building context for: '{test_query}'")
    context = builder.build_context(test_query)
    print(builder.get_context_summary(context))
    print(f"Tables: {sorted(list(context['tables'].keys()))}")
    print(f"Metrics: {sorted(list(context['metrics'].keys()))}")
    print(f"Dimensions: {sorted(list(context['dimensions'].keys()))}")