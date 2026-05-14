# Project: AI Query Agent (SAP HANA)

## Project Overview
An enterprise-grade AI Query Agent designed to connect to SAP HANA, utilize SQLAlchemy for query generation, NetworkX for routing, and SAP AI Hub for LLM integration.

## Current Phase: Phase 1 - Project Initialization
**Status**: In Progress
**Current Task**: Integrating full query pipeline and implementing data executor.

## Project Memories & Rules
- **User Real Name**: The app displays the real name on the homepage immediately (parsed from API even on 404/202).
- **Acknowledgment**: Project Supervisor's name to be provided later.
- **Dependency Rule**: Explicitly avoid Ibis.
- **Indian PII Redaction**: Custom recognizers (PAN, Aadhaar) are implemented (related to Redaction System project).

## Key Components
- `src/core/`: Config & `schema.py` (Pydantic execution contract)
- `src/engine/`: `compiler.py` (SQLAlchemy compiler) & `bsl_dictionary.py` (BSL mapping)
- `src/graph/`: NetworkX routing
- `src/llm/`: `query_planner.py` (LLM intent translation)
- `src/retrieval/`: `context_builder.py` & `vector_store.py`

## Last Changes
- Implemented `src/llm/query_planner.py` with multi-provider support (Gemini, OpenRouter), strict Pydantic schema enforcement, and relative time resolution.
- Updated `requirements.txt` with `openai` and `httpx` for OpenRouter integration.
- Configured `.env` with OpenRouter API keys and LLM routing variables.
- Rewrote `src/retrieval/context_builder.py` with a 6-step multi-signal pipeline (Synonym Expansion -> Vector Search -> Anchoring -> Pruning -> Graph Expansion).
- Added `resolve_filter_values()` to `ContextBuilder` for DB code translation.
- Rewrote `src/retrieval/vector_store.py` with high-density document construction and added `rebuild_index()` utility.
- Implemented `export_to_excel.py` at repo root to export all BSL-mapped tables from SAP HANA to a formatted Excel workbook with automated styling and metadata.
- Added `openpyxl` and `hdbcli` to `requirements.txt` to support Excel operations and SAP HANA connectivity.
- Enriched `src/engine/bsl_dictionary.py` with 128+ synonyms, added `filter_value_mappings` for business logic codes, and `domain_keywords` for HR/OPS routing (fixed location signal overlap).
- Generated production-grade `src/engine/bsl_dictionary.py` with 24 tables, 12 metrics, 13 dimensions, and synonyms derived from live schema and business domain knowledge.
- Updated `tests/test_compiler.py` to align with the new BSL dictionary and verified all tests pass using the project venv.
- Created `src/infrastructure/schema_puller.py` to pull metadata, columns, PKs, and logical edges into `src/engine/raw_schema.json`.
- Defined `src/graph/logical_edges.py` with 29 manually verified join relationships (Identity, Location, Roster, Shift, Skills, Contract).
- Created `check_columns.py` in root for manual column verification of key tables.
- Created `src/infrastructure/relationship_inferencer.py` to automatically infer table relationships from live metadata and known PKs.
- Created `src/infrastructure/inspect_hana.py` to list user schemas and table counts.
- Implemented `src/infrastructure/hana_connection.py` for SAP HANA Cloud connectivity using `sqlalchemy-hana`.
- Created `requirements.txt` with pinned dependencies.
- Created standard Python `.gitignore`.
- Created `.env.example` with SAP connectivity keys.
- Initialized directory structure under `src/`.
