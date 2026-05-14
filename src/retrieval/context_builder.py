import sys
import os
import re
import copy
import itertools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.retrieval.vector_store import BSLVectorStore
from src.graph.schema_graph import SchemaGraph
from src.engine.bsl_dictionary import BSL_MAPPING


class ContextBuilder:
    """
    Governor layer that produces a bounded, recall-optimized BSL context
    using a 6-step pipeline with priority-based pruning and hard caps.
    """

    def __init__(
        self,
        bsl_mapping: dict = None,
        vector_store: BSLVectorStore = None,
        schema_graph: SchemaGraph = None
    ):
        self.bsl_mapping = bsl_mapping if bsl_mapping is not None else BSL_MAPPING
        self.vector_store = vector_store if vector_store is not None else BSLVectorStore()
        self.schema_graph = schema_graph if schema_graph is not None else SchemaGraph()

    def build_context(self, query: str, top_k: int = 15, threshold: float = 0.78, include_debug: bool = False) -> dict:
        """
        Builds a pruned BSL context using the bounded refinement strategy.
        Decouples thresholds, enforces priority buckets, and applies hard caps.
        """
        query_lower = query.lower()

        def strip_schema(name):
            return name.split('.')[-1] if '.' in name else name

        # Step 1 — Synonym & Canonical Matching (Deterministic)
        synonym_metrics = set()
        synonym_dimensions = set()
        
        # 1.1 Synonym Dictionary Match
        for syn_key, mapped_val in self.bsl_mapping.get("synonyms", {}).items():
            if re.search(r'\b' + re.escape(syn_key.lower()) + r'\b', query_lower):
                if mapped_val in self.bsl_mapping.get("metrics", {}):
                    synonym_metrics.add(mapped_val)
                elif mapped_val in self.bsl_mapping.get("dimensions", {}):
                    synonym_dimensions.add(mapped_val)

        # 1.2 Canonical Key Match
        for m_key in self.bsl_mapping.get("metrics", {}).keys():
            if re.search(r'\b' + re.escape(m_key.lower().replace("_", " ")) + r'\b', query_lower):
                synonym_metrics.add(m_key)
        for d_key in self.bsl_mapping.get("dimensions", {}).keys():
            if re.search(r'\b' + re.escape(d_key.lower().replace("_", " ")) + r'\b', query_lower):
                synonym_dimensions.add(d_key)

        # 1.3 Domain Detection
        hr_count = sum(1 for w in self.bsl_mapping.get("domain_keywords", {}).get("HR", []) if re.search(r'\b' + re.escape(w.lower()) + r'\b', query_lower))
        ops_count = sum(1 for w in self.bsl_mapping.get("domain_keywords", {}).get("OPS", []) if re.search(r'\b' + re.escape(w.lower()) + r'\b', query_lower))
        detected_domain = "HR" if hr_count > ops_count else ("OPS" if ops_count > hr_count else None)

        # Step 2 — Vector Search
        scored_results = self.vector_store.search(query, top_k, threshold=0.70)
        raw_vector_tables = [r for r in scored_results if r["type"] == "table"]
        raw_vector_metrics = [r for r in scored_results if r["type"] == "metric"]
        raw_vector_dimensions = [r for r in scored_results if r["type"] == "dimension"]

        # Step 3 — Strict Metric/Dimension Pruning & Anchoring
        # Rules: Synonym always survives. Vector survives if >= threshold + 0.04
        final_metrics_list = [] # Store as (key, score, is_synonym)
        final_dimensions_list = []
        
        # Add synonyms first (priority 1)
        for m in synonym_metrics: final_metrics_list.append((m, 1.0, True))
        for d in synonym_dimensions: final_dimensions_list.append((d, 1.0, True))
        
        # Add pruned vector matches
        for rm in raw_vector_metrics:
            if rm["key"] not in synonym_metrics and rm["similarity"] >= (threshold + 0.04):
                final_metrics_list.append((rm["key"], rm["similarity"], False))
        for rd in raw_vector_dimensions:
            if rd["key"] not in synonym_dimensions and rd["similarity"] >= (threshold + 0.04):
                final_dimensions_list.append((rd["key"], rd["similarity"], False))

        # Anchor tables from selected metrics/dims
        anchored_tables = set()
        for m_key, _, _ in final_metrics_list:
            if m_key in self.bsl_mapping["metrics"]: anchored_tables.add(self.bsl_mapping["metrics"][m_key]["table"])
        for d_key, _, _ in final_dimensions_list:
            if d_key in self.bsl_mapping["dimensions"]: anchored_tables.add(self.bsl_mapping["dimensions"][d_key]["table"])
        anchored_tables = {t for t in anchored_tables if t in self.bsl_mapping["tables"]}

        # Step 4 — Relaxed Table Selection
        # Rules: Anchored survive. Pure-vector survives if >= threshold - 0.04
        pruned_vector_tables = [] # (key, score)
        for rt in raw_vector_tables:
            if rt["key"] in anchored_tables: continue
            table_domain = self.bsl_mapping["tables"].get(rt["key"], {}).get("domain")
            if detected_domain and table_domain and table_domain != detected_domain: continue
            if rt["similarity"] >= (threshold - 0.04):
                pruned_vector_tables.append((rt["key"], rt["similarity"]))

        # Step 5 — Identity Fallback, Bridging, and Priority Capping
        
        # 5.1 Identity Fallback (user_details)
        fallback_tables = set()
        id_trigger_keywords = ["name", "names", "manager", "managers", "employee name", "employee names", "who reports to", "reporting manager"]
        if "user_details" in self.bsl_mapping["tables"] and "user_details" not in anchored_tables:
            has_trigger = any(re.search(r'\b' + re.escape(kw) + r'\b', query_lower) for kw in id_trigger_keywords)
            # Relationship tables: emp_manager, emp_requests, emp_hr, etc.
            current_set = anchored_tables | {t[0] for t in pruned_vector_tables}
            has_rel_table = any(k in current_set for k in ["emp_manager", "emp_requests", "emp_hr", "emp_contract_details", "emp_workslot", "emp_planning"])
            if has_trigger and has_rel_table:
                fallback_tables.add("user_details")

        # 5.2 Bridge Calculation (One Pass)
        bridge_tables = set()
        stripped_to_bsl = {strip_schema(info["physical_name"]): k for k, info in self.bsl_mapping["tables"].items()}
        current_tables = list(anchored_tables | fallback_tables | {t[0] for t in pruned_vector_tables})
        
        for t_a, t_b in itertools.combinations(current_tables, 2):
            phys_a = strip_schema(self.bsl_mapping["tables"][t_a]["physical_name"])
            phys_b = strip_schema(self.bsl_mapping["tables"][t_b]["physical_name"])
            path = self.schema_graph.get_join_path(phys_a, phys_b)
            if path:
                for node in path[1:-1]: # Just the intermediate nodes
                    if node in stripped_to_bsl:
                        b_key = stripped_to_bsl[node]
                        if b_key not in current_tables: bridge_tables.add(b_key)

        # 5.3 Priority Table Capping (max_tables = 6)
        # Priority: 1. Anchored, 2. Fallback, 3. Bridge, 4. Vector (by score)
        final_table_keys = set()
        for t in sorted(anchored_tables):
            if len(final_table_keys) < 6: final_table_keys.add(t)
        for t in sorted(fallback_tables):
            if len(final_table_keys) < 6: final_table_keys.add(t)
        for t in sorted(bridge_tables):
            if len(final_table_keys) < 6: final_table_keys.add(t)
        
        sorted_vector_tables = sorted(pruned_vector_tables, key=lambda x: x[1], reverse=True)
        for t_key, _ in sorted_vector_tables:
            if len(final_table_keys) < 6: final_table_keys.add(t_key)

        # 5.4 Metric/Dimension Capping (max_metrics = 4, max_dimensions = 5)
        # Priority: 1. Synonym, 2. High-confidence (>= threshold + 0.08), 3. Remainder
        def cap_concepts(concepts_list, limit, high_conf_thresh):
            priority_list = []
            for k, score, is_syn in concepts_list:
                priority = 0 if is_syn else (1 if score >= high_conf_thresh else 2)
                priority_list.append((k, priority, score))
            # Sort by priority, then by score descending
            sorted_concepts = sorted(priority_list, key=lambda x: (x[1], -x[2]))
            return {k for k, p, s in sorted_concepts[:limit]}

        final_metrics = cap_concepts(final_metrics_list, 4, threshold + 0.08)
        final_dimensions = cap_concepts(final_dimensions_list, 5, threshold + 0.08)

        # Step 6 — Final Context Assembly
        context = {
            "tables": {k: copy.deepcopy(self.bsl_mapping["tables"][k]) for k in sorted(final_table_keys)},
            "metrics": {k: copy.deepcopy(self.bsl_mapping["metrics"][k]) for k in sorted(final_metrics)},
            "dimensions": {k: copy.deepcopy(self.bsl_mapping["dimensions"][k]) for k in sorted(final_dimensions)}
        }

        if include_debug:
            print(f"\n[DEBUG] Query: '{query}'")
            print(f"  - Vector Metrics: {len(raw_vector_metrics)} raw -> {len([m for m in final_metrics_list if not m[2]])} pruned")
            print(f"  - Vector Dimensions: {len(raw_vector_dimensions)} raw -> {len([d for d in final_dimensions_list if not d[2]])} pruned")
            print(f"  - Anchored Tables: {', '.join(sorted(anchored_tables)) or 'None'}")
            print(f"  - Identity Fallback: {'Triggered (user_details added)' if 'user_details' in fallback_tables else 'No'}")
            print(f"  - Bridge Tables: {', '.join(sorted(bridge_tables)) or 'None'}")
            print(f"  - Final Capped: Tables({len(final_table_keys)}), Metrics({len(final_metrics)}), Dims({len(final_dimensions)})")

        return context

    def get_context_summary(self, context: dict) -> str:
        t_keys = sorted(context["tables"].keys())
        m_keys = sorted(context["metrics"].keys())
        d_keys = sorted(context["dimensions"].keys())
        return f"Tables ({len(t_keys)}): {', '.join(t_keys)} | Metrics ({len(m_keys)}): {', '.join(m_keys)} | Dimensions ({len(d_keys)}): {', '.join(d_keys)}"

    def resolve_filter_values(self, filters: list[dict]) -> list[dict]:
        mappings = self.bsl_mapping.get("filter_value_mappings", {})
        processed = copy.deepcopy(filters)
        for f in processed:
            field = f.get("field", "").upper()
            if field in mappings:
                val_lower = str(f.get("value", "")).lower()
                if val_lower in mappings[field]: f["value"] = mappings[field][val_lower]
        return processed


if __name__ == "__main__":
    builder = ContextBuilder()
    test_queries = [
        "total headcount by employee role and location",
        "show me all active employees",
        "how many staff are on leave this year",
        "which employees worked overtime last week",
        "show vacation balance for all staff",
        "list all pending leave requests",
        "how many employees have certifications",
        "show me the roster shifts for this week",
        "which store has the most employees",
        "show me employee names and their managers",
    ]
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        # For testing we can use include_debug=True
        context = builder.build_context(query, include_debug=False)
        print(f"  → {builder.get_context_summary(context)}")