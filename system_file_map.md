# System File Map: AI Query Agent (SAP HANA)

This document provides an exhaustive inventory of the files constituting the Query Agent and its Execution Layer, including technical summaries and a trace of the system's data flow.

## 1. Context Layer
*Focus: Embeddings, vector store logic, and retrieval scripts.*

| File Path | Technical Summary |
| :--- | :--- |
| `src/retrieval/vector_store.py` | Manages a ChromaDB vector store to index and search BSL concepts such as tables, metrics, and dimensions using Gemini embeddings. It provides methods to build, rebuild, and query the index, converting search results into similarity-ranked metadata for context retrieval. |
| `src/retrieval/embedder.py` | A wrapper for the Google Gemini embedding API that provides functionality to generate vector representations of text. It supports single-string and batch processing, including rate-limiting management for API stability. |
| `src/retrieval/context_builder.py` | Implements a 6-step retrieval pipeline that filters and expands BSL metadata into a concise context for the LLM. It combines deterministic synonym matching, vector search, domain detection, and graph-based table bridging to ensure all necessary schema elements are included. |

## 2. Execution Layer
*Focus: SQL generation logic, JSON parsing, and BSL dictionaries.*

| File Path | Technical Summary |
| :--- | :--- |
| `src/engine/compiler.py` | A core execution component that translates a high-level `QueryPlan` into executable SAP HANA SQL using SQLAlchemy. It automatically resolves complex join chains between multiple tables by consulting the schema graph and applies filters, aggregations, and time-range constraints. |
| `src/engine/bsl_dictionary.py` | The central Business Semantic Layer (BSL) repository that maps natural language concepts to physical SAP HANA database structures. It contains detailed definitions for tables, metrics, and dimensions, including physical names, column types, join rules, and a rich synonym dictionary. |
| `src/llm/query_planner.py` | Converts natural language user queries into structured `MultiQueryPlan` JSON objects by leveraging LLMs (Gemini or OpenRouter). It uses the pruned BSL context to constrain the model's choices, enforces strict Pydantic schema validation, and handles relative time resolution. |
| `src/core/schema.py` | Defines the Pydantic-based data structures that serve as the execution contract between the LLM planner and the SQL compiler. It specifies the schema for `FilterCondition`, `TimeRange`, `QueryPlan`, and `MultiQueryPlan`, ensuring consistent data transfer. |
| `src/graph/schema_graph.py` | Constructs and traverses a NetworkX MultiGraph representing the database schema and its relationships. It provides functionality to find the shortest join path between tables and extract the specific column-level join details required for SQL generation. |
| `src/graph/logical_edges.py` | Contains a manually verified list of join relationships (edges) between tables, specifying the `from_table`, `to_table`, and their respective join columns. This static data acts as the primary source for building the `SchemaGraph`. |

## 3. Database Connectivity
*Focus: HANA drivers, connection pools, and environment handling.*

| File Path | Technical Summary |
| :--- | :--- |
| `src/infrastructure/hana_connection.py` | Initializes and manages the SQLAlchemy engine for SAP HANA connectivity using credentials from environment variables. It configures mandatory SSL parameters for cloud connections and includes a utility function to verify the connection status. |
| `.env` | Stores sensitive environment variables including database credentials (`HANA_HOST`, `HANA_USER`, etc.) and API keys for LLM providers. It is the primary configuration source for all connectivity and model-related parameters. |
| `src/infrastructure/schema_puller.py` | Automates the extraction of table metadata, column definitions, and primary keys from a live SAP HANA schema. It outputs this data into a raw JSON format used for initial schema mapping and relationship inference. |
| `src/infrastructure/inspect_hana.py` | A diagnostic tool that connects to SAP HANA to list user-accessible schemas and provides a count of tables within each schema. It is used to verify permissions and identify the correct schema for the agent. |

## 4. Query Data Flow Trace
The following steps outline the lifecycle of a single natural language query (e.g., *"What is the headcount by department?"*):

1.  **Input Receipt**: The user string is first received by `src/retrieval/context_builder.py`.
2.  **Context Construction**: `context_builder.py` performs synonym matching and queries `src/retrieval/vector_store.py` (which uses `src/retrieval/embedder.py`) to find relevant tables, metrics, and dimensions from the `BSL_MAPPING` in `src/engine/bsl_dictionary.py`.
3.  **Graph Expansion**: If multiple tables are found, `context_builder.py` uses `src/graph/schema_graph.py` to identify any "bridge" tables needed to join them, ensuring a valid SQL path.
4.  **Intent Translation**: The pruned schema context and the user query are passed to `src/llm/query_planner.py`. The LLM translates the query into a `MultiQueryPlan` (defined in `src/core/schema.py`) which contains metrics, dimensions, filters, and time ranges.
5.  **SQL Compilation**: The `QueryPlan` is passed to `src/engine/compiler.py`. It uses the `SchemaGraph` to resolve physical join details and leverages `src/infrastructure/hana_connection.py` (SQLAlchemy dialect) to generate a final, executable SAP HANA SQL string.
6.  **Output Generation**: The final output is the generated SQL string (and subsequently the JSON-parsed intent from the planner).

## 5. BSL (Business Semantic Layer) Identification
The Business Semantic Layer mappings live in:
*   **File**: `src/engine/bsl_dictionary.py`
*   **Primary Variable**: `BSL_MAPPING` (a `dict` containing `tables`, `metrics`, `dimensions`, `synonyms`, `filter_value_mappings`, and `domain_keywords`).
*   **Supporting Variable**: `LOGICAL_EDGES` in `src/graph/logical_edges.py` (defines the relationship rules used to connect BSL entities).

---
*Note: This map is exhaustive based on the current repository deep-scan.*
