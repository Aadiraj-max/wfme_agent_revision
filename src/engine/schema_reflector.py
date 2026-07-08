import os
import re
import requests
import json
from typing import Dict, List, Any

# Strict 10-table allowlist
CORE_TABLE_ALLOWLIST = [
    "UserDetails", "RosterItem", "VacationBalance", "EmpRequests", "Locations",
    "ViewsUserDetail", "ViewsVMasterOrg", "ViewsVPlannedEmp", "ViewsVRosterPlannedEmp",
    "Position"
]

class SchemaReflector:
    def __init__(self, 
                 meta_url: str = "http://localhost:4000/cubejs-api/v1/meta", 
                 model_dir: str = None):
        self.meta_url = meta_url
        if model_dir is None:
            # Dynamically resolve to the workspace workforce-semantic-layer/model folder
            model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "workforce-semantic-layer", "model"))
        self.model_dir = model_dir
        self.cache = None

    def fetch_and_filter(self) -> Dict[str, Any]:
        """
        Fetches live metadata from the Cube API, filters it against the CORE_TABLE_ALLOWLIST,
        and dynamically extracts join relationships from JS files.
        """
        if self.cache is not None:
            return self.cache

        # 1. Fetch live meta or fallback to local sample
        raw_meta = None
        try:
            response = requests.get(self.meta_url, timeout=10)
            if response.status_code == 200:
                raw_meta = response.json()
        except Exception as e:
            print(f"[SchemaReflector] Warning: Failed to fetch live metadata: {e}. Falling back to sample.")

        if not raw_meta:
            # Try loading from local meta_sample.json in revised repo
            try:
                local_sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scratch", "meta_sample.json"))
                if os.path.exists(local_sample_path):
                    with open(local_sample_path, "r", encoding="utf-8") as f:
                        raw_meta = json.load(f)
            except Exception as e:
                print(f"[SchemaReflector] Error loading local sample: {e}")

        if not raw_meta:
            raw_meta = {"cubes": []}

        # 2. Filter cubes, measures, and dimensions
        filtered_cubes = []
        for cube in raw_meta.get("cubes", []):
            cube_name = cube["name"]
            if cube_name in CORE_TABLE_ALLOWLIST:
                filtered_cube = {
                    "name": cube_name,
                    "title": cube.get("title", cube_name),
                    "measures": [
                        {
                            "name": m["name"],
                            "title": m.get("title", m["name"].split(".")[-1]),
                            "type": m.get("type", "number"),
                            "aggType": m.get("aggType")
                        } for m in cube.get("measures", []) if m.get("isVisible", True)
                    ],
                    "dimensions": [
                        {
                            "name": d["name"],
                            "title": d.get("title", d["name"].split(".")[-1]),
                            "type": d.get("type", "string"),
                            "primaryKey": d.get("primaryKey", False)
                        } for d in cube.get("dimensions", []) if d.get("isVisible", True) or d.get("primaryKey", False)
                    ]
                }
                filtered_cubes.append(filtered_cube)

        # 3. Parse joins dynamically from JS files in model_dir
        parsed_joins = []
        if os.path.exists(self.model_dir):
            for file_name in os.listdir(self.model_dir):
                if file_name.endswith(".js"):
                    file_path = os.path.join(self.model_dir, file_name)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Extract main cube name from model
                        cube_match = re.search(r"cube\(\s*[`'\"](\w+)[`'\"]", content)
                        if not cube_match:
                            continue
                        source_cube = cube_match.group(1)
                        if source_cube not in CORE_TABLE_ALLOWLIST:
                            continue

                        # Extract joins block
                        # Simple curly brace matching to find content inside joins: { ... }
                        joins_match = re.search(r"joins:\s*\{", content)
                        if joins_match:
                            start_idx = joins_match.end()
                            # Find closing brace of joins block
                            brace_count = 1
                            end_idx = start_idx
                            while brace_count > 0 and end_idx < len(content):
                                char = content[end_idx]
                                if char == "{":
                                    brace_count += 1
                                elif char == "}":
                                    brace_count -= 1
                                end_idx += 1

                            joins_block = content[start_idx:end_idx-1]
                            
                            # Find each target cube join inside block
                            # e.g., TargetCube: { relationship: `belongsTo`, sql: ... }
                            target_matches = re.finditer(r"(\w+):\s*\{", joins_block)
                            for tm in target_matches:
                                target_cube = tm.group(1)
                                if target_cube not in CORE_TABLE_ALLOWLIST:
                                    continue

                                # Extract relationship and sql inside this target's block
                                start_t = tm.end()
                                brace_t = 1
                                end_t = start_t
                                while brace_t > 0 and end_t < len(joins_block):
                                    char = joins_block[end_t]
                                    if char == "{":
                                        brace_t += 1
                                    elif char == "}":
                                        brace_t -= 1
                                    end_t += 1
                                
                                target_block = joins_block[start_t:end_t-1]
                                rel_match = re.search(r"relationship:\s*[`'\"](\w+)[`'\"]", target_block)
                                relationship = rel_match.group(1) if rel_match else "belongsTo"
                                
                                sql_match = re.search(r"sql:\s*[`'\"]([^`'\"]+)[`'\"]", target_block)
                                sql_cond = sql_match.group(1) if sql_match else ""

                                # Parse column names from join condition
                                # e.g. `${CUBE}."ROSTER_HEADER_ID" = ${RosterHeader}."ROSTER_HEADER_ID"`
                                from_col = None
                                to_col = None
                                
                                # Match: ${CUBE}."COL_A" = ${Target}."COL_B"
                                m1 = re.search(r"\$\{CUBE\}\.\"([^\"]+)\"\s*=\s*\$\{" + re.escape(target_cube) + r"\}\.\"([^\"]+)\"", sql_cond, re.IGNORECASE)
                                # Match: ${Target}."COL_B" = ${CUBE}."COL_A"
                                m2 = re.search(r"\$\{" + re.escape(target_cube) + r"\}\.\"([^\"]+)\"\s*=\s*\$\{CUBE\}\.\"([^\"]+)\"", sql_cond, re.IGNORECASE)

                                if m1:
                                    from_col = m1.group(1)
                                    to_col = m1.group(2)
                                elif m2:
                                    from_col = m2.group(2)
                                    to_col = m2.group(1)
                                else:
                                    # Relaxed search if structure is different
                                    cols = re.findall(r"\.\"([^\"]+)\"", sql_cond)
                                    if len(cols) >= 2:
                                        from_col = cols[0]
                                        to_col = cols[1]

                                parsed_joins.append({
                                    "from_cube": source_cube,
                                    "to_cube": target_cube,
                                    "from_column": from_col or "id",
                                    "to_column": to_col or "id",
                                    "relationship_type": relationship
                                })
                    except Exception as e:
                        print(f"[SchemaReflector] Error parsing file {file_name}: {e}")

        self.cache = {
            "cubes": filtered_cubes,
            "joins": parsed_joins
        }
        return self.cache
