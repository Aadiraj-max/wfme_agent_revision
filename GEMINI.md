# Project: AI Query Agent (SAP HANA)

## Project Overview
An enterprise-grade AI Query Agent designed to connect to SAP HANA, utilize SQLAlchemy for query generation, NetworkX for routing, and SAP AI Hub for LLM integration.

## Current Phase: Phase 1 - Project Initialization
**Status**: In Progress
**Current Task**: Setting up project structure, dependencies, and environment configuration.

## Project Memories & Rules
- **User Real Name**: The app displays the real name on the homepage immediately (parsed from API even on 404/202).
- **Acknowledgment**: Project Supervisor's name to be provided later.
- **Dependency Rule**: Explicitly avoid Ibis.
- **Indian PII Redaction**: Custom recognizers (PAN, Aadhaar) are implemented (related to Redaction System project).

## Key Components
- `src/core/`: Config & `schema.py` (Pydantic execution contract)
- `src/engine/`: `compiler.py` (SQLAlchemy compiler) & `bsl_dictionary.py` (BSL mapping)
- `src/graph/`: NetworkX routing
- `src/llm/`: SAP AI Hub integration

## Last Changes
- Created `src/infrastructure/inspect_hana.py` to list user schemas and table counts.
- Implemented `src/infrastructure/hana_connection.py` for SAP HANA Cloud connectivity using `sqlalchemy-hana`.
- Created `src/engine/bsl_dictionary.py` with `BSL_MAPPING` (Tables, Metrics, Dimensions).
- Created `requirements.txt` with pinned dependencies.
- Created standard Python `.gitignore`.
- Created `.env.example` with SAP connectivity keys.
- Initialized directory structure under `src/`.
