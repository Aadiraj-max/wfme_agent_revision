import os
import sys
import json
import re
import datetime
import logging
from typing import Optional, Any, List

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
from src.core.schema import QueryPlan, FilterCondition, TimeRange, MultiQueryPlan
from src.engine.bsl_dictionary import BSL_MAPPING

load_dotenv()

logger = logging.getLogger("query_agent.planner")

# ── Provider constants ─────────────────────────────────────────────────────────
PROVIDER_GEMINI     = "gemini"
PROVIDER_OPENROUTER = "openrouter"
PROVIDER_AICORE     = "aicore"

GEMINI_MODEL        = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
OPENROUTER_MODEL    = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GENAI_MODEL         = os.getenv("GENAI_MODEL", "amazon--nova-pro")

class EmptyQueryPlanError(Exception):
    pass

def _build_prompt(query: str, context: dict, debug: bool = False) -> str:
    """
    Formats the pruned BSL context dict into a compact LLM prompt.
    Injects the current system date for relative time resolution.
    """
    current_date = datetime.date.today().isoformat()
    
    if "tables" not in context:
        context["tables"] = {}
    
    # Inject mandatory HR tables
    for mandatory_table in ["user_details", "views_user_detail"]:
        if mandatory_table not in context["tables"] and mandatory_table in BSL_MAPPING.get("tables", {}):
            context["tables"][mandatory_table] = BSL_MAPPING["tables"][mandatory_table]
    
    tables_block = ""
    for key, info in context.get("tables", {}).items():
        cols = ", ".join(info.get("columns", {}).keys())
        tables_block += f"  - {key} (physical: {info.get('physical_name', '')}) | columns: {cols}\n"

    metrics_block = ""
    for key, info in context.get("metrics", {}).items():
        metrics_block += (
            f"  - {key}: {info.get('description', '')} "
            f"[{info.get('aggregation', '')} of {info.get('column', '')}]\n"
        )

    dimensions_block = ""
    for key, info in context.get("dimensions", {}).items():
        dimensions_block += (
            f"  - {key}: {info.get('description', '')} "
            f"[column: {info.get('column', '')}]\n"
        )

    # If context is empty, warn explicitly
    if not context.get("metrics") and not context.get("dimensions"):
        tables_block = tables_block or "  (none matched)\n"
        metrics_block = "  (none matched — check vector store index)\n"
        dimensions_block = "  (none matched — check vector store index)\n"

    if debug:
        print("\n===== CONTEXT =====")
        print(f"Tables ({len(context.get('tables', {}))}): {list(context.get('tables', {}).keys())}")
        print(f"Metrics ({len(context.get('metrics', {}))}): {list(context.get('metrics', {}).keys())}")
        print(f"Dimensions ({len(context.get('dimensions', {}))}): {list(context.get('dimensions', {}).keys())}")
        if not context.get('tables', {}):
            print("WARNING: Context tables are empty.")
        if not context.get('metrics', {}):
            print("WARNING: Context metrics are empty.")
        if not context.get('dimensions', {}):
            print("WARNING: Context dimensions are empty.")
        print("===================")

    prompt = f"""You are a SAP HANA WFM query planning assistant.
Your job is to translate a natural language workforce management question into a structured QueryPlan JSON.

CURRENT SYSTEM DATE: {current_date}

The available metrics and dimensions below have already been pre-selected as relevant to the user question.
You must ONLY use the exact metric and dimension names listed. Never invent names not in these lists.

AVAILABLE TABLES:
{tables_block}

AVAILABLE METRICS (pick from these exact names only):
{metrics_block}

AVAILABLE DIMENSIONS (pick from these exact names only):
{dimensions_block}

RULES:
1. Only use metric and dimension names exactly as shown above. Do not paraphrase.
2. filters is a list of objects: {{"field": "column_name", "operator": "eq|neq|gt|lt|gte|lte|in", "value": val}}.
3. time_range: if dates are mentioned, use ISO format YYYY-MM-DD. Use CURRENT SYSTEM DATE to resolve relative terms like "last month".
4. limit is an integer, default 100.
5. If the user asks an analytical question, each query object must contain at least one metric or one dimension that directly answers the question.
6. If the user asks "by X", include X as a dimension when available.
7. If the user asks for multiple distinct requests, return multiple QueryPlan objects in queries.
8. Do not return empty arrays for metrics and dimensions unless the query is genuinely unanswerable from the provided context.
9. If context is insufficient, do not silently emit a blank plan; instead emit the closest valid plan possible using the provided metrics/dimensions.
10. STRICTLY output valid JSON matching the format below. Do not include ANY text outside of the JSON block. Do not use markdown formatting (e.g., ```json). Your output must be directly parsable by Python's json.loads().

REQUIRED OUTPUT FORMAT:
{{"queries": [
  {{"metrics": ["metric_name"], "dimensions": ["dimension_name"], "filters": [], "time_range": null, "limit": 100}}
]}}

USER QUESTION: {query}"""
    return prompt.strip()

def _parse_response(raw: str, context: dict, debug: bool = False) -> MultiQueryPlan:
    """
    Parses raw LLM string output into a validated MultiQueryPlan.
    Strips hallucinated metrics/dimensions from each sub-query.
    """
    if debug:
        print("\n===== RAW MODEL OUTPUT =====")
        print(f"Type: {type(raw).__name__}")
        if not raw or not raw.strip():
            print("WARNING: Raw response is empty or whitespace.")
        print(raw)
        print("============================")

    cleaned = re.sub(r'```(?:json)?\s*|\s*```', '', raw).strip()
    try:
        data = json.loads(cleaned)
        if debug:
            print("\n===== PARSED PLAN =====")
            print("JSON parsing: SUCCESS")
    except json.JSONDecodeError as e:
        if debug:
            print("\n===== ERROR =====")
            print(f"Stage: JSON parse")
            print(f"Exception: {type(e).__name__}")
            print(f"Message: {e}")
            print("=================")
        raise ValueError(
            f"LLM returned non-JSON response.\nParse error: {e}\nRaw output:\n{raw}"
        )

    valid_metrics = set(context.get("metrics", {}).keys())
    valid_dims = set(context.get("dimensions", {}).keys())

    queries_data = data.get("queries", [])
    if not isinstance(queries_data, list):
        # Fallback if LLM returned a single object instead of a list
        queries_data = [data]

    if debug:
        print(f"Query objects found: {len(queries_data)}")

    validated_queries = []
    for i, q_data in enumerate(queries_data):
        metrics = [m for m in q_data.get("metrics", []) if m in valid_metrics]
        dimensions = [d for d in q_data.get("dimensions", []) if d in valid_dims]

        filters = []
        for f in q_data.get("filters", []):
            filters.append(FilterCondition(
                field=f.get("field"),
                operator=f.get("operator", "eq"),
                value=f.get("value")
            ))

        tr_data = q_data.get("time_range")
        time_range = None
        if tr_data and isinstance(tr_data, dict):
            time_range = TimeRange(
                start_date=tr_data.get("start_date"),
                end_date=tr_data.get("end_date")
            )

        limit = q_data.get("limit", 100)

        # Semantic validation
        is_empty = not metrics and not dimensions and not filters and time_range is None
        
        if debug:
            print(f"  Query {i}:")
            print(f"    Metrics: {metrics}")
            print(f"    Dimensions: {dimensions}")
            print(f"    Filters: {len(filters)}")
            print(f"    Time Range: {time_range}")
            print(f"    Limit: {limit}")
            if is_empty:
                print(f"    -> Warning: Query {i} is semantically empty (no metrics, dimensions, filters, or time_range)")

        validated_queries.append(QueryPlan(
            metrics=metrics,
            dimensions=dimensions,
            filters=filters,
            time_range=time_range,
            limit=limit
        ))

    if debug:
        print("Pydantic validation: SUCCESS")
        print(f"Parsed object type: {MultiQueryPlan.__name__}")
        print("=======================")

    all_empty = all(not q.metrics and not q.dimensions and not q.filters and q.time_range is None for q in validated_queries)
    if not validated_queries or all_empty:
        if debug:
            print("\n===== ERROR =====")
            print("SEMANTIC FAILURE: planner returned schema-valid but execution-empty output")
            print("Stage: Semantic validation")
            print("Exception: EmptyQueryPlanError")
            print("=================")
        raise EmptyQueryPlanError("LLM returned a semantically empty MultiQueryPlan.")

    return MultiQueryPlan(queries=validated_queries)

class QueryPlanner:
    """
    Converts a natural language WFM query + pruned BSL context dict into a validated QueryPlan.
    """
    def __init__(self, enforce_schema: bool = True, debug: bool = False):
        self.provider = os.getenv("LLM_PROVIDER", PROVIDER_GEMINI).lower().strip()
        self.enforce_schema = enforce_schema
        self.debug = debug
        self._validate_env()

    def _validate_env(self):
        if not os.getenv("GEMINI_API_KEY"):
            raise EnvironmentError("GEMINI_API_KEY is not set.")
        if self.provider == PROVIDER_OPENROUTER and not os.getenv("OPENROUTER_API_KEY"):
            raise EnvironmentError("OPENROUTER_API_KEY is not set for OpenRouter mode.")

    def plan(self, query: str, context: dict) -> MultiQueryPlan:
        prompt = _build_prompt(query, context, debug=self.debug)
        
        if self.debug:
            print("\n===== FINAL PROMPT =====")
            print(f"Provider path: {self.provider}")
            print(f"Structured schema mode: {self.enforce_schema}")
            print(f"Prompt character length: {len(prompt)}")
            print(f"Prompt token estimate: {len(prompt) // 4}")
            print("------------------------")
            print(prompt)
            print("========================")

        try:
            if self.provider == PROVIDER_GEMINI:
                raw = self._call_gemini(prompt, use_schema=self.enforce_schema)
            else:
                raw = self._call_openrouter(prompt, use_schema=self.enforce_schema)
        except Exception as e:
            if self.debug:
                print("\n===== ERROR =====")
                print(f"Stage: Provider call ({self.provider})")
                print(f"Exception: {type(e).__name__}")
                print(f"Message: {e}")
                import traceback
                traceback.print_exc()
                print("=================")
            # Fallback to basic JSON mode if structured output fails
            print(f"Warning: Structured output failed ({e}). Falling back to basic JSON mode.")
            try:
                if self.provider == PROVIDER_GEMINI:
                    raw = self._call_gemini(prompt, use_schema=False)
                else:
                    raw = self._call_openrouter(prompt, use_schema=False)
            except Exception as e2:
                if self.debug:
                    print("\n===== ERROR =====")
                    print(f"Stage: Fallback Provider call ({self.provider})")
                    print(f"Exception: {type(e2).__name__}")
                    print(f"Message: {e2}")
                    import traceback
                    traceback.print_exc()
                    print("=================")
                raise e2

        return _parse_response(raw, context, debug=self.debug)

    def _call_gemini(self, prompt: str, use_schema: bool = True, schema_class: Any = None) -> str:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        config_args = {"response_mime_type": "application/json", "temperature": 0.0}
        if use_schema:
            config_args["response_schema"] = schema_class or MultiQueryPlan
            
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(**config_args)
        )
        return response.text

    def _call_openrouter(self, prompt: str, use_schema: bool = True, schema_class: Any = None) -> str:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://github.com/Aadiraj-max/wfme_agent_revision",
                "X-Title": "WFM Query Agent"
            }
        )
        
        format_args = {"type": "json_object"}
        if use_schema:
            target_schema = schema_class or MultiQueryPlan
            # OpenRouter support for json_schema depends on the model
            format_args = {
                "type": "json_schema",
                "json_schema": {
                    "name": target_schema.__name__.lower(),
                    "schema": target_schema.model_json_schema(),
                    "strict": True
                }
            }

        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format=format_args
        )
        return response.choices[0].message.content
    def _call_aicore(self, prompt: str, use_schema: bool = True, schema_class: Any = None) -> str:
        from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
        import requests
        
        proxy = get_proxy_client('gen-ai-hub')
        deps = [d for d in proxy.get_deployments() if d.model_name == GENAI_MODEL]
        
        if not deps:
            raise ValueError(f"No AI Core deployment found for model {GENAI_MODEL}")
            
        dep = deps[0]
        
        if "amazon" in GENAI_MODEL.lower():
            url = f"{dep.url}/converse"
            headers = proxy.request_header.copy()
            headers['Content-Type'] = 'application/json'
            
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "temperature": 0.0
                }
            }
            
            if use_schema and schema_class:
                payload["system"] = [{"text": f"You must strictly output a populated JSON object matching the structure of the schema below. Do NOT output the schema metadata, definitions ($defs, properties, required, title, type attributes), or comments. Only output the final populated instance JSON. Schema:\n{json.dumps(schema_class.model_json_schema(), indent=2)}"}]
            
            resp = requests.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            
            resp_json = resp.json()
            content = resp_json["output"]["message"]["content"][0]["text"]
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()
                
            return content
        else:
            url = f"{dep.url}/chat/completions"
            headers = proxy.request_header.copy()
            headers['Content-Type'] = 'application/json'
            
            payload = {
                "model": GENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0
            }
            if use_schema and schema_class:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_class.__name__,
                        "schema": schema_class.model_json_schema()
                    }
                }
            resp = requests.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            resp_json = resp.json()
            return resp_json["choices"][0]["message"]["content"]

    def plan_unified(self, query: str, schema: dict, allowed_operators: list[str], auth_context: dict = None) -> Any:
        from src.core.schema import UnifiedCubeQueryPlan
        import json
        
        schema_yaml = ""
        if isinstance(schema, list):
            for cube_meta in schema:
                cube = cube_meta.get("name")
                schema_yaml += f"Cube: {cube}\n  Measures:\n"
                for m in cube_meta.get("measures", []):
                    schema_yaml += f"    - {m['name']} (Title: {m.get('title')})\n"
                schema_yaml += f"  Dimensions:\n"
                for d in cube_meta.get("dimensions", []):
                    schema_yaml += f"    - {d['name']} (Title: {d.get('title')}, Type: {d.get('type')})\n"
                schema_yaml += "\n"
        else:
            for cube, meta in schema.items():
                schema_yaml += f"Cube: {cube}\n  Measures:\n"
                for m in meta.get("measures", []):
                    schema_yaml += f"    - {m['name']} (Title: {m.get('title')})\n"
                schema_yaml += f"  Dimensions:\n"
                for d in meta.get("dimensions", []):
                    schema_yaml += f"    - {d['name']} (Title: {d.get('title')}, Type: {d.get('type')})\n"
                schema_yaml += "\n"
            
        allowed_ops_str = f"[{', '.join(allowed_operators)}]"
        import datetime
        current_date = datetime.date.today().isoformat()
        
        security_rules_block = ""
        if auth_context:
            role = auth_context.get("role", "E")
            user_id = auth_context.get("user_id", "")
            managed_locations = auth_context.get("managed_locations", [])
            
            if role == "E":
                security_rules_block = f"""
STRICT SECURITY RULE (Row-Level Security):
- The requesting user is an Employee (user_id: '{user_id}').
- You MUST append a filter restricting all returned data to their own User ID:
  member: 'UserDetails.userid' (or the user ID column of the relevant cube), operator: 'equals', values: ['{user_id}']
"""
            elif role == "M" and "*" not in managed_locations:
                loc_list_str = json.dumps(managed_locations)
                security_rules_block = f"""
STRICT SECURITY RULE (Row-Level Security):
- The requesting user is a Manager (user_id: '{user_id}') managing locations: {loc_list_str}.
- If the user asks about themselves, you MUST filter by their user ID: member: 'UserDetails.userid', operator: 'equals', values: ['{user_id}'].
- Otherwise, you MUST append a filter restricting data to their managed locations using the location column of the relevant cube (e.g. 'Locations.locationdesc', 'UserDetails.locationid', or 'EmpPlanning.locationid'):
  member: <location_member>, operator: 'equals' (if single) or 'in' (if multiple), values: {loc_list_str}
"""
        
        prompt = f"""You are a SAP HANA WFM query planning assistant for Cube.js.
Your job is to translate a natural language workforce management question into a structured UnifiedCubeQueryPlan JSON.
{security_rules_block}
AVAILABLE SCHEMA:
{schema_yaml}

ALLOWED OPERATORS for filters:
{allowed_ops_str}

RULES:
1. You must ONLY use the exact measure, dimension, and time dimension names provided in the AVAILABLE SCHEMA above.
2. In 'timeDimensions', specify the time dimension name and 'dateRange' as start and end date list (e.g. ["2026-05-01", "2026-05-31"]). Resolve relative date terms (like "today", "this month", "last week") relative to the CURRENT SYSTEM DATE {current_date}.
3. In 'filters', use ONLY the allowed operators from the list above. The 'member' must be a fully qualified dimension or measure (e.g. 'UserDetails.gender'). 'values' must be a list of strings (e.g. ["Male"]). Do not create or include filters unless they are explicitly requested by the user's question or required by the Row-Level Security rules. Never add arbitrary default filters (like filtering on gender being notSet or set, or status being notSet) if the user did not ask for it.
4. Filter by User ID: When a specific employee/user ID is queried (e.g., employee 2000005), you MUST apply the filter to 'UserDetails.userid' or 'ViewsUserDetail.userid' (or the user ID column of the relevant cube).
   - IMPORTANT: If you are querying shifts or roster schedules (which belong to the 'RosterItem' cube), you MUST filter on 'ViewsUserDetail.userid' (and NEVER 'RosterItem.userid' or 'UserDetails.userid') because 'RosterItem' only connects to user IDs via the 'ViewsVRosterPlannedEmp' and 'ViewsUserDetail' join path.
   - NEVER invent 'userid' on other cubes (like RosterItem, Locations, ViewsVRosterPlannedEmp, etc.) as they do not possess this column.
5. Limit the query output rows to a reasonable value (default 100).
6. Output MUST strictly match the UnifiedCubeQueryPlan schema format.

USER QUESTION: {query}"""
        
        if self.debug:
            logger.info("===== FINAL PROMPT =====")
            logger.info(prompt)
            logger.info("========================")
            
        if self.provider == PROVIDER_GEMINI:
            raw = self._call_gemini(prompt, use_schema=True, schema_class=UnifiedCubeQueryPlan)
        elif self.provider == PROVIDER_OPENROUTER:
            raw = self._call_openrouter(prompt, use_schema=True, schema_class=UnifiedCubeQueryPlan)
        else:
            raw = self._call_aicore(prompt, use_schema=True, schema_class=UnifiedCubeQueryPlan)

        if self.debug:
            logger.info("===== RAW LLM OUTPUT =====")
            logger.info(raw)
            logger.info("==========================")

        cleaned = raw.strip()
        cleaned = re.sub(r'```(?:json)?\s*|\s*```', '', cleaned).strip()
        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        if first_brace != -1 and last_brace != -1:
            cleaned = cleaned[first_brace:last_brace + 1]
            
        data = json.loads(cleaned)
        if self.debug:
            logger.info("===== PARSED JSON CUBE PLAN =====")
            logger.info(json.dumps(data, indent=2))
            logger.info("=================================")
        return UnifiedCubeQueryPlan(**data)

if __name__ == "__main__":
    from src.retrieval.context_builder import ContextBuilder
    
    # Initialize the planner to check configuration
    planner = QueryPlanner(enforce_schema=True, debug=True)
    active_model = GEMINI_MODEL if planner.provider == PROVIDER_GEMINI else OPENROUTER_MODEL

    test_query = "Show me total headcount by department, and also show me the attrition rate for the last 30 days"

    print("=" * 50)
    print("QueryPlanner Smoke Test")
    print(f"Provider Active          : {planner.provider.upper()}")
    print(f"Model Active             : {active_model}")
    print(f"Original User Query      : {test_query}")
    print(f"Timestamp                : {datetime.datetime.now().isoformat()}")
    print(f"Schema Enforcement       : {planner.enforce_schema}")
    print("=" * 50)
    
    builder = ContextBuilder()
    print(f"\nBuilding context for: '{test_query}'")
    context = builder.build_context(test_query)
    
    print("\nGenerating MultiQueryPlan...")
    try:
        plan = planner.plan(test_query, context)
        print("\nRESULTING MULTI-QUERY PLAN:")
        print(json.dumps(plan.model_dump(), indent=2))
    except Exception as e:
        print("\nSMOKE TEST FAILED")
        print(f"Exception: {type(e).__name__}")
        print(f"Message: {e}")
