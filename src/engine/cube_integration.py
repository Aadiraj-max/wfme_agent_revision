import os
import sys
import json
import logging
import requests
import pandas as pd
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.engine.schema_reflector import SchemaReflector
from src.graph.schema_graph import SchemaGraph
from src.retrieval.vector_store import BSLVectorStore
from src.llm.query_planner import QueryPlanner
from src.core.schema import UnifiedCubeQueryPlan
from google import genai

load_dotenv()

logger = logging.getLogger("query_agent.pipeline")

class CubeIntegrationPipeline:
    def __init__(self, cube_url: str = "http://localhost:4000/cubejs-api/v1/load", debug: bool = False):
        self.cube_url = cube_url
        self.debug = debug
        
        # 1. Initialize SchemaReflector & cache metadata
        self.reflector = SchemaReflector(meta_url=self.cube_url.replace("/load", "/meta"))
        self.filtered_meta = self.reflector.fetch_and_filter()
        
        # 2. Initialize Dynamic Vector Store & build index dynamically on boot if incomplete or schema changed
        self.vector_store = BSLVectorStore()
        expected_count = sum(
            1 + len(c.get("measures", [])) + len(c.get("dimensions", []))
            for c in self.filtered_meta.get("cubes", [])
        )
        current_count = self.vector_store.get_collection_count()
        if current_count != expected_count:
            if self.debug:
                print(f"[CubeIntegrationPipeline] Vector store count mismatch (current: {current_count}, expected: {expected_count}). Rebuilding...")
            self.vector_store.rebuild_index(self.filtered_meta)
        
        # 3. Initialize Dynamic NetworkX Graph Validator
        self.graph = SchemaGraph(
            joins=self.filtered_meta.get("joins", []),
            cubes=self.filtered_meta.get("cubes", [])
        )
        
        # 4. Initialize QueryPlanner
        self.planner = QueryPlanner(debug=self.debug)
        
        # 5. Native Cube.js operators list (22 operators total)
        self.OPERATORS = [
            "equals", "notEquals", "contains", "notContains",
            "gt", "gte", "lt", "lte", "set", "notSet",
            "in", "notIn", "startsWith", "endsWith",
            "beforeDate", "afterDate", "inDateRange", "notInDateRange"
        ]
        
        # 6. Initialize Human Response Generator Client
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
        if self.provider == "gemini":
            self.genai_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        else:
            self.genai_model = os.getenv("GENAI_MODEL", "amazon--nova-pro")
        if self.provider == "aicore":
            if os.getenv("AICORE_OAUTH_URL") and not os.getenv("AICORE_AUTH_URL"):
                os.environ["AICORE_AUTH_URL"] = os.getenv("AICORE_OAUTH_URL")
            self.ai_client = None
        else:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            self.ai_client = genai.Client(api_key=api_key)

        if self.debug:
            logger.info("===== INITIALIZING DYNAMIC REFLECTION PIPELINE =====")
            logger.info(f"NetworkX Schema Graph built with {self.graph.graph.number_of_nodes()} cubes and {self.graph.graph.number_of_edges()} joins.")
            logger.info(f"Cubes loaded in allowlist: {sorted(list(self.graph.graph.nodes()))}")
            logger.info("====================================================")

    def run(self, natural_language_query: str, auth_context: dict = None) -> str:
        try:
            if self.debug: 
                logger.info(f"[Step 1] Input Query: '{natural_language_query}'")
            
            # Step 2: Vector Search to get matching dimensions/measures/cubes
            search_results = self.vector_store.search(natural_language_query, top_k=8, threshold=0.55)
            if self.debug:
                logger.info("[Step 2] Vector Search Candidates:")
                for res in search_results:
                    logger.info(f"  - Similarity score: [{res['similarity']:.4f}] | Type: {res['type'].upper()} | Cube: {res['cube']} | Column/Key: {res['key']}")
            
            # Step 3: Extract unique cube names from top vector matches
            cubes_involved = []
            for res in search_results:
                if res["cube"] not in cubes_involved:
                    cubes_involved.append(res["cube"])
            
            # Force include core employee tables in candidates to enable user-level filtering joins
            for core_cube in ["UserDetails", "ViewsUserDetail"]:
                if core_cube not in cubes_involved:
                    cubes_involved.append(core_cube)
            
            # Step 4: NetworkX Graph Path Validation (drops isolated tables)
            verified_cube_names = self.graph.validate_path(cubes_involved)
            if self.debug:
                logger.info("[Step 3] Graph Path Validation:")
                logger.info(f"  - Initial Candidates from search: {cubes_involved}")
                logger.info(f"  - Verified & Joined Cubes Path: {verified_cube_names}")
                
            # Get full schema info for ONLY the verified connected cubes
            verified_cubes_schema = [
                c for c in self.filtered_meta["cubes"] if c["name"] in verified_cube_names
            ]
            
            # Step 5: Force LLM planner to output single Pydantic UnifiedCubeQueryPlan payload
            plan: UnifiedCubeQueryPlan = self.planner.plan_unified(
                natural_language_query, 
                verified_cubes_schema, 
                self.OPERATORS,
                auth_context=auth_context
            )
            
            # Post-process filters to apply filter_value_mappings
            from src.engine.bsl_dictionary import BSL_MAPPING
            mappings = BSL_MAPPING.get("filter_value_mappings", {})
            for f in plan.query.filters:
                member_col = f.member.split(".")[-1].upper()
                if member_col in mappings:
                    mapped_vals = []
                    for val in f.values:
                        val_str = str(val).lower().strip()
                        if val_str in mappings[member_col]:
                            mapped_vals.append(mappings[member_col][val_str])
                        else:
                            mapped_vals.append(val)
                    f.values = mapped_vals

            # Convert planner result to final payload
            cube_payload = {"query": plan.query.model_dump(exclude_none=True)}
            if self.debug:
                logger.info(f"[Step 4] Final Execution Payload:\n{json.dumps(cube_payload, indent=2)}")
            
            # Step 6: Post to Cube API `/load`
            response_data = self._execute_request(cube_payload)
            
            # Step 7: Parse response to clean DataFrame
            df = self._process_response(response_data)
            if self.debug:
                logger.info(f"[Step 5] Execution Raw Output Data:\n{df.to_markdown(index=False)}")
            
            # Step 8: Generate final NLP explanation
            nlp_res = self._generate_human_response(natural_language_query, df)
            if self.debug:
                logger.info(f"[Step 6] Synthesized NLP Response:\n{nlp_res}")
            return nlp_res
            
        except Exception as e:
            if self.debug:
                logger.error("[PIPELINE ERROR] An error occurred while executing the pipeline:", exc_info=True)
            return "I cannot retrieve this information because the data is not sufficient or an error occurred."

    def _execute_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            self.cube_url, 
            json=payload, 
            headers={"Content-Type": "application/json"}, 
            timeout=30
        )
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if self.debug: 
                print(f"[CUBE ERROR] {response.text}")
            raise Exception(f"Cube.js API Error: {response.text}")

    def _process_response(self, response_data: Dict[str, Any]) -> pd.DataFrame:
        data = response_data.get("data", [])
        df = pd.DataFrame(data)
        if not df.empty:
            df.columns = [col.split(".")[-1] if "." in col else col for col in df.columns]
        return df

    def _generate_human_response(self, original_query: str, df: pd.DataFrame) -> str:
        if df.empty:
            data_string = "The query returned an empty result set (0 records matching the criteria)."
        else:
            data_string = df.to_markdown(index=False)
        
        prompt = (
            f"You are an expert HR and Workforce Management data assistant.\n"
            f"The user asked this question: '{original_query}'\n"
            f"I queried the Cube.js backend and retrieved this raw data:\n\n{data_string}\n\n"
            f"Please provide a concise, natural, and conversational answer based ONLY on this data. "
            f"Format numbers nicely (e.g. 1,565 instead of 1565.0). "
            f"If the result is a single number, state it clearly in a sentence. "
            f"If it's a table, summarize the key points or present it cleanly. Do not explain how you got the data."
        )
        
        try:
            if self.provider == "aicore":
                from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
                import requests
                
                proxy = get_proxy_client('gen-ai-hub')
                deps = [d for d in proxy.get_deployments() if d.model_name == self.genai_model]
                
                if not deps:
                    raise ValueError(f"No AI Core deployment found for model {self.genai_model}")
                    
                dep = deps[0]
                
                if "amazon" in self.genai_model.lower():
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
                    
                    resp = requests.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    
                    resp_json = resp.json()
                    return resp_json["output"]["message"]["content"][0]["text"]
                else:
                    url = f"{dep.url}/chat/completions"
                    headers = proxy.request_header.copy()
                    headers['Content-Type'] = 'application/json'
                    
                    payload = {
                        "model": self.genai_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.0
                    }
                    
                    resp = requests.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    resp_json = resp.json()
                    return resp_json["choices"][0]["message"]["content"]
                    
            else:
                response = self.ai_client.models.generate_content(
                    model=self.genai_model,
                    contents=prompt,
                )
                return response.text
        except Exception as e:
            if self.debug: 
                print(f"[NLP Generation Error] {e}")
            return f"Here is the raw data:\n\n{data_string}"

if __name__ == "__main__":
    pipeline = CubeIntegrationPipeline(debug=True)
    
    test_queries = [
        "What is the total headcount of employees?",
        "What is the total headcount by gender?"
    ]
    
    for query in test_queries:
        print(f"\n=========================================")
        print(f"TESTING: {query}")
        print(f"=========================================")
        try:
            response = pipeline.run(query)
            print("\n--- AGENT RESPONSE ---")
            print(response)
        except Exception as e:
            print(f"\n[ERROR] {e}")
