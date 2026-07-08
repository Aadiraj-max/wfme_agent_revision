# Project: AI Query Agent (SAP HANA)

## Project Overview
An enterprise-grade AI Query Agent designed to connect to SAP HANA, utilizing dynamic schema reflection via Cube.js, NetworkX for dynamic path validation, and structured LLM outputs to query the Cube REST API.

## Current Phase: Phase 1 - Project Initialization
**Status**: Completed
**Current Task**: Fully integrated and verified the unified single-payload query pipeline.

## Project Memories & Rules
- **User Real Name**: The app displays the real name on the homepage immediately (parsed from API even on 404/202).
- **Acknowledgment**: Project Supervisor's name to be provided later.
- **Dependency Rule**: Explicitly avoid Ibis.
- **Indian PII Redaction**: Custom recognizers (PAN, Aadhaar) are implemented (related to Redaction System project).
- **Core 10 Tables**: Enforced allowlist containing `UserDetails`, `RosterItem`, `VacationBalance`, `EmpRequests`, `Locations`, `ViewsUserDetail`, `ViewsVMasterOrg`, `ViewsVPlannedEmp`, `ViewsVRosterPlannedEmp`, and `Position`.

## Key Components
- `src/core/`: Config & `schema.py` (Pydantic execution contract with CubeQuery & UnifiedCubeQueryPlan)
- `src/engine/`: `schema_reflector.py` (Dynamic reflection of cubes, measures, dimensions & parsing of model joins) & `cube_integration.py` (Execution orchestrator)
- `src/graph/`: `schema_graph.py` (NetworkX routing and path validation)
- `src/llm/`: `query_planner.py` (Gemini single-payload structured output generation)
- `src/retrieval/`: `vector_store.py` (Dynamic ChromaDB embedding & retrieval)

## Last Changes
- **2026-06-15 Updates**:
  - **Roster Join Path & Roster Shift Queries**: Added join between `ViewsVRosterPlannedEmp` and `ViewsUserDetail` on `LOCATIONID` and `JOB_CODE`/`JOBCODE` to resolve compilation path errors. Updated Rule 4 of the prompt in `query_planner.py` to instruct the LLM to filter by `ViewsUserDetail.userid` for roster/shift queries.
  - **5 Queries Validation**: Verified all 5 test queries successfully return 200 OK.
  - **SAP AI Core Provider Switch**: Set `LLM_PROVIDER=aicore` in `.env` to route completions through the SAP AI Core Amazon Nova Pro model.
  - **Contract Field Mapping on ViewsUserDetail**: Added `CONTRACTENDDATE` and `CONTRACTSTARTDATE` columns to the `views_user_detail` table definition in `src/engine/bsl_dictionary.py`.
  - **Contracts Metric and Dimensions**: Defined `contracts_count` metric and `contract_end_date` / `contract_start_date` dimensions in `bsl_dictionary.py`.
  - **Custom BSL Synonyms**: Added synonyms mapping `'store' -> 'location'` to ensure "store 1201" resolves to `locationid`, and mapped contract-ending vocabulary terms to `contracts_count` and `contract_end_date`.
  - **ViewsUserDetail Join Connection**: Modified `query_agent/workforce-semantic-layer/model/ViewsUserDetail.js` to add a `joins` relationship to `UserDetails` on `USERID`. This connects the previously isolated `ViewsUserDetail` node to the global schema graph, preventing the path validator from dropping it when other employee-related tables are retrieved.
  - **Dynamic Filter Value Mapping**: Added a post-processing step in `cube_integration.py` to map verbal filter inputs (like `"Leave"`) to their physical DB representation (like `"L"`), resolving queries returning zero records due to literal string mismatch.
- Completed **Phase 4: The Runtime Query Pipeline** inside [cube_integration.py](file:///c:/Users/SUEA/Downloads/revised/src/engine/cube_integration.py) to orchestrate Vector Search -> NetworkX Graph Validation -> Pydantic Structured Query Planning -> Cube.js `/load` execution -> Final LLM response synthesis.
- Fixed a test-pollution bug in [test_compiler.py](file:///c:/Users/SUEA/Downloads/revised/tests/test_compiler.py) by isolating ChromaDB test indexes in a temp directory so they don't overwrite the main dev database.
- Successfully verified the entire pipeline against live database queries (e.g., "What is the total headcount by gender?").
- Re-architected and upgraded pipeline to **Dynamic Schema Reflection (Single-Agent BI)**:
  - Implemented [schema_reflector.py](file:///c:/Users/SUEA/Downloads/revised/src/engine/schema_reflector.py) to dynamically fetch, filter, and cache metadata from Cube's `/meta` API against a strict 10-table allowlist. It dynamically parses JS model definitions from `workforce-semantic-layer/model` to build actual schema join paths.
  - Rewrote [schema_graph.py](file:///c:/Users/SUEA/Downloads/revised/src/graph/schema_graph.py) to build the NetworkX graph dynamically from reflector data and act as a dynamic Path Validator.
  - Rewrote [vector_store.py](file:///c:/Users/SUEA/Downloads/revised/src/retrieval/vector_store.py) to dynamically ingest, embed (`title` + `name`), and index live measures, dimensions, and cubes on startup.
  - Updated [schema.py](file:///c:/Users/SUEA/Downloads/revised/src/core/schema.py) with `CubeQuery` and `UnifiedCubeQueryPlan` models enforcing a structured contract aligned with Cube's `/load` endpoint.
  - Rewrote [query_planner.py](file:///c:/Users/SUEA/Downloads/revised/src/llm/query_planner.py) with the `plan_unified` method which forces Gemini to output a structured JSON plan matching the target Cube REST API.
  - Rewrote [cube_integration.py](file:///c:/Users/SUEA/Downloads/revised/src/engine/cube_integration.py) to orchestrate the dynamic pipeline: vector search -> path validation -> unified planning -> REST execution.
  - Cleaned up obsolete legacy files: deactivated `compiler.py`, `logical_edges.py`, `hana_connection.py`, and `schema_puller.py` to prevent split-brain issues.
  - Updated [test_compiler.py](file:///c:/Users/SUEA/Downloads/revised/tests/test_compiler.py) to test the new dynamic reflection, path validation, and embedding layers.
  - Fixed an issue where the NetworkX `SchemaGraph` was only registering cubes with active join relationships. Updated [schema_graph.py](file:///c:/Users/SUEA/Downloads/revised/src/graph/schema_graph.py) and [cube_integration.py](file:///c:/Users/SUEA/Downloads/revised/src/engine/cube_integration.py) to load all 10 allowed tables from the metadata allowlist into the graph as nodes first, ensuring isolated tables (such as `ViewsUserDetail`, `ViewsVMasterOrg`, and `ViewsVPlannedEmp`) are recognized.
  - Fixed authentication in [find_parameters.py](file:///c:/Users/SUEA/Downloads/revised/find_parameters.py) and discovered that the parameterized SAP HANA view `views::V_ROSTER_PLANNED_EMP` requires `IN_STARTDATE` and `IN_ENDDATE` date parameters.
  - Updated [ViewsVRosterPlannedEmp.js](file:///C:/Users/SUEA/workforce-semantic-layer/model/ViewsVRosterPlannedEmp.js) to query `views::V_ROSTER_PLANNED_EMP` with standard SAP HANA parameter syntax (`PLACEHOLDER."IN_STARTDATE" => '2026-05-01'`, etc.), enabling the Cube.js service to successfully query the view.
  - Updated both [ViewsVRosterPlannedEmp.js](file:///C:/Users/SUEA/workforce-semantic-layer/model/ViewsVRosterPlannedEmp.js) and [RosterItem.js](file:///C:/Users/SUEA/workforce-semantic-layer/model/RosterItem.js).
- Integrated **SAP BTP AI Core / GenAI Hub Service Connectivity** using Bedrock `amazon--nova-pro` model:
  - Refactored [query_planner.py](file:///c:/Users/SUEA/Downloads/revised/src/llm/query_planner.py) and [cube_integration.py](file:///c:/Users/SUEA/Downloads/revised/src/engine/cube_integration.py) to use direct REST API connectivity via the `/converse` endpoint instead of relying on the native `OpenAI` client wrapper in `gen_ai_hub`, which was causing `400 Bad Request` exceptions for AWS Bedrock models.
  - Implemented structured output validation using `requests` and manual JSON schema validation payloads to match Pydantic execution models (`UnifiedCubeQueryPlan`).
  - Added full fallback mechanisms for other provider types (like OpenAI-compatible endpoint structures).
  - Verified and executed the end-to-end WFM pipeline against a live Cube.js instance via the virtualenv environment.
- **BSL Dictionary Cleanup**:
  - Pruned `src/engine/bsl_dictionary.py` to match the exact 10-table `CORE_TABLE_ALLOWLIST`.
  - Removed definitions for the 14 un-allowed tables.
  - Purged 5 metrics referencing deleted tables: `overtime_entries`, `planned_hours`, `average_shift_hours`, `total_vacation_days_taken`, and `employee_skills_count`.
  - Purged 9 dimensions referencing deleted tables: `manager`, `shift_code`, `workday_type`, `contract_type`, `skill_type`, `team`, `store`, `year`, and `workdate`.
  - Removed all synonyms mapping to those deleted metrics/dimensions (e.g., `overtime hours`, `skills count`, `vacation days`, `store manager`, etc.).
  - Purged `OVERTIME` from `filter_value_mappings` and cleaned up `domain_keywords` to align with the core 10 tables.


