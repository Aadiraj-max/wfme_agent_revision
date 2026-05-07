# WFM Agent – System Overview

## 1. Project Goal
Build an enterprise-grade Workforce Management (WFM) AI system that can:
- Understand natural-language questions from business users.
- Query one or more SAP HANA databases safely and accurately.
- Perform analytics (aggregations, comparisons, multi-step analysis).
- Generate structured reports and, later, forecasting and planning outputs.
- Meet strict latency, safety, and cost constraints.

The system is architected so that the **querying agent** is a reusable, self-contained component that can be embedded into a larger multi-agent WFM framework.

---

## 2. High-Level Architecture

### 2.1 Supervisor–Worker Pattern
At the system level, we follow a **hierarchical multi-agent architecture**:

- **Supervisor (Orchestrator) Agent**
  - Single point of contact with the user.
  - Interprets user intent across the whole WFM domain.
  - Decides which specialized workers to invoke (querying, reporting, forecasting, etc.).
  - Owns **conversation memory** (short-term history and task context).

- **Worker Agents (Stateless Tools)**
  - **Query Worker**: our text→JSON→SQL→SAP HANA pipeline (current focus).
  - **Reporting Worker**: turns numeric/query outputs into structured reports.
  - **Forecasting Worker**: runs Python/ML time-series and forecasting.
  - Future workers: ticketing, scheduling, alerting, etc.

Workers are **stateless**. They take structured inputs, perform one job, and return results. All long-lived state and dialogue context live in the Supervisor.

### 2.2 Model Routing
We use multiple LLMs, each for what it does best:

- **Gemini 2.5 Flash**
  - Fast, cheap model for Intent parsing, query decomposition, and generating strict JSON for the query worker.
- **Gemini Pro (optional escalation)**
  - Used only when deeper reasoning is required.

---

## 3. Query Worker – End-to-End Pipeline

1. **Schema Retrieval & Pruning** (Vector + Graph).
2. **Intent Parsing** (LLM → JSON), constrained by a schema.
3. **Semantic Layer Translation** (JSON → SQL via Boring Semantic Layer + Ibis).
4. **Execution** (Run SQL against SAP HANA and return data).

### 3.1 Schema & Metadata Layer
- Extract tables, columns, types, primary/foreign keys from SAP HANA.
- Vector Embeddings to map user questions to relevant tables/columns.
- Schema Graph (NetworkX) to find join paths.

### 3.2 Intent Parsing: LLM → JSON Contract
Use Gemini Flash with **structured output / response schema** so the model produces exact JSON shape for metrics, dimensions, and filters.

### 3.3 Semantic Layer: JSON → SQL (BSL + Ibis)
A lightweight Python semantic layer built on **Ibis**. Defines metrics, dimensions, and joins declaratively, avoiding LLM SQL hallucinations.

### 3.4 Execution: SQL → Data
Wrap SAP HANA access in a function. Use `ibis` execution or direct `hdbcli` connection. Returns structured results back to the Supervisor.
