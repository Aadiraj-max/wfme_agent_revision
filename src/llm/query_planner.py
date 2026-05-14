import os
import sys
import json
import re
import datetime
from typing import Optional

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
from src.core.schema import QueryPlan, FilterCondition, TimeRange

load_dotenv()

# ── Provider constants ─────────────────────────────────────────────────────────
PROVIDER_GEMINI     = "gemini"
PROVIDER_OPENROUTER = "openrouter"

GEMINI_MODEL        = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
OPENROUTER_MODEL    = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def _build_prompt(query: str, context: dict) -> str:
    """
    Formats the pruned BSL context dict into a compact LLM prompt.
    Injects the current system date for relative time resolution.
    """
    current_date = datetime.date.today().isoformat()
    
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
5. Return ONLY the JSON object. No explanation, no markdown fences.

REQUIRED OUTPUT FORMAT:
{{"metrics": ["metric_name"], "dimensions": ["dimension_name"], "filters": [], "time_range": null, "limit": 100}}

USER QUESTION: {query}"""
    return prompt.strip()

def _parse_response(raw: str, context: dict) -> QueryPlan:
    """
    Parses raw LLM string output into a validated QueryPlan.
    Strips hallucinated metrics/dimensions not present in the provided context.
    """
    cleaned = re.sub(r'```(?:json)?\s*|\s*```', '', raw).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM returned non-JSON response.\nParse error: {e}\nRaw output:\n{raw}"
        )

    # Context Validation (Safety Net against hallucinations)
    valid_metrics = set(context.get("metrics", {}).keys())
    valid_dims = set(context.get("dimensions", {}).keys())

    metrics = [m for m in data.get("metrics", []) if m in valid_metrics]
    dimensions = [d for d in data.get("dimensions", []) if d in valid_dims]

    filters = []
    for f in data.get("filters", []):
        filters.append(FilterCondition(
            field=f.get("field"),
            operator=f.get("operator", "eq"),
            value=f.get("value")
        ))

    tr_data = data.get("time_range")
    time_range = None
    if tr_data and isinstance(tr_data, dict):
        time_range = TimeRange(
            start_date=tr_data.get("start_date"),
            end_date=tr_data.get("end_date")
        )

    return QueryPlan(
        metrics=metrics,
        dimensions=dimensions,
        filters=filters,
        time_range=time_range,
        limit=data.get("limit", 100)
    )

class QueryPlanner:
    """
    Converts a natural language WFM query + pruned BSL context dict into a validated QueryPlan.
    """
    def __init__(self, enforce_schema: bool = True):
        self.provider = os.getenv("LLM_PROVIDER", PROVIDER_GEMINI).lower().strip()
        self.enforce_schema = enforce_schema
        self._validate_env()

    def _validate_env(self):
        if not os.getenv("GEMINI_API_KEY"):
            raise EnvironmentError("GEMINI_API_KEY is not set.")
        if self.provider == PROVIDER_OPENROUTER and not os.getenv("OPENROUTER_API_KEY"):
            raise EnvironmentError("OPENROUTER_API_KEY is not set for OpenRouter mode.")

    def plan(self, query: str, context: dict) -> QueryPlan:
        prompt = _build_prompt(query, context)
        
        try:
            if self.provider == PROVIDER_GEMINI:
                raw = self._call_gemini(prompt, use_schema=self.enforce_schema)
            else:
                raw = self._call_openrouter(prompt, use_schema=self.enforce_schema)
        except Exception as e:
            # Fallback to basic JSON mode if structured output fails
            print(f"Warning: Structured output failed ({e}). Falling back to basic JSON mode.")
            if self.provider == PROVIDER_GEMINI:
                raw = self._call_gemini(prompt, use_schema=False)
            else:
                raw = self._call_openrouter(prompt, use_schema=False)

        return _parse_response(raw, context)

    def _call_gemini(self, prompt: str, use_schema: bool = True) -> str:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        config_args = {"response_mime_type": "application/json", "temperature": 0.0}
        if use_schema:
            config_args["response_schema"] = QueryPlan
            
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(**config_args)
        )
        return response.text

    def _call_openrouter(self, prompt: str, use_schema: bool = True) -> str:
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
            # OpenRouter support for json_schema depends on the model
            format_args = {
                "type": "json_schema",
                "json_schema": {
                    "name": "query_plan",
                    "schema": QueryPlan.model_json_schema(),
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

if __name__ == "__main__":
    from src.retrieval.context_builder import ContextBuilder
    
    # Initialize the planner to check configuration
    planner = QueryPlanner(enforce_schema=True)
    active_model = GEMINI_MODEL if planner.provider == PROVIDER_GEMINI else OPENROUTER_MODEL

    print("=" * 50)
    print("QueryPlanner Smoke Test")
    print(f"Provider Active : {planner.provider.upper()}")
    print(f"Model Active    : {active_model}")
    print("=" * 50)
    
    builder = ContextBuilder()
    test_query = "show me total headcount by department for all employees in the last 30 days"
    print(f"\nBuilding context for: '{test_query}'")
    context = builder.build_context(test_query)
    
    planner = QueryPlanner(enforce_schema=True)
    print("\nGenerating QueryPlan...")
    plan = planner.plan(test_query, context)
    
    print("\nRESULTING QUERY PLAN:")
    print(json.dumps(plan.model_dump(), indent=2))
