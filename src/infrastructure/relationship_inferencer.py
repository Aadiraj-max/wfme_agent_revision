import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import json
import collections
from sqlalchemy import text
from src.infrastructure.hana_connection import get_engine

SCHEMA_NAME = 'WFMSCH_1'

TARGET_TABLES = [
    "USER_DETAIL", "USER_DETAILS", "V_MASTER_ORG", "EMP_HR", "EMP_MANAGER", 
    "EMP_CONTRACT_DETAILS", "VACATION_HISTORY", "VACATION_BALANCE", "EMP_REQUESTS", 
    "SKILLS_CERTIFICATE", "EMP_SKILL_CERTIFICATE", "SCH_COMPANY_ROLES", "ROLE_DEFINATION", 
    "POSITION", "EMP_PLANNING", "EMP_WORKSLOT", "ROSTER_ITEM", "ROSTER_HEADER", 
    "LOCATIONS", "WORKDAY_TYPES", "SHIFTCODE_SLOTMAPPING", "V_PLANNED_EMP", 
    "V_ROSTER_PLANNED_EMP", "STORES", "TEAMS"
]

KNOWN_PKS = {
    'USER_DETAILS': ['USERID', 'COMPANYID'],
    'LOCATIONS': ['COMPANYID', 'BUSINESSUNITID', 'DIVISIONID', 'DEPARTMENTID', 'SUBDEPARTMENTID', 'LOCATIONID'],
    'ROSTER_HEADER': ['ROSTER_HEADER_ID'],
    'ROSTER_ITEM': ['ROSTER_HEADER_ID', 'ROSTER_ITEM_ID', 'DAY_NUMBER'],
    'POSITION': ['COMPANYID', 'POSITIONID'],
    'SKILLS_CERTIFICATE': ['COMPANYID', 'JOBCODE', 'TYPE', 'CODE'],
    'STORES': ['ID'],
    'TEAMS': ['ID'],
    'WORKDAY_TYPES': ['COMPANYID', 'COUNTRYCODE', 'WORKDAYCODE'],
    'SHIFTCODE_SLOTMAPPING': ['COMPANYID', 'COUNTRYCODE', 'SHIFT_CODE'],
    'ROLE_DEFINATION': ['COMPANYID', 'ROLE_ID'],
    'EMP_CONTRACT_DETAILS': ['USERID', 'COMPANYID', 'EFFECTIVESTARTDATE', 'EFFECTIVEENDDATE', 'CONTRACTNUMBER', 'LOCATIONID'],
    'EMP_HR': ['USERID', 'COMPNAYID', 'HR_EMPID', 'EFFECTIVESTARTDATE', 'EFFECTIVEENDDATE'],
    'EMP_MANAGER': ['USERID', 'COMPANYID', 'MANAGER_EMPID', 'EFFECTIVESTARTDATE', 'EFFECTIVEENDDATE'],
    'EMP_PLANNING': ['USERID', 'COMPANYID', 'LOCATIONID', 'JOBCODE', 'WORKDATE'],
    'EMP_REQUESTS': ['USERID', 'COMPANYID', 'WORKDATE', 'REQUESTTYPE', 'STATUS'],
    'EMP_SKILL_CERTIFICATE': ['COMPANYID', 'USERID', 'TYPE', 'CODE', 'EFFECTIVESTARTDATE'],
    'EMP_WORKSLOT': ['USERID', 'COMPANYID', 'LOCATIONID', 'JOBCODE', 'WORKDATE', 'CHECKINTIME', 'CHECKOUTTIME'],
    'VACATION_BALANCE': ['COMPANYID', 'USERID', 'YEAR', 'CONTRACTNUMBER'],
    'VACATION_HISTORY': ['COMPANYID', 'USERID', 'YEAR', 'CONTRACTNUMBER'],
}

def infer_relationships():
    engine = get_engine()
    
    # Step 1 — Pull all columns for all 25 tables from live DB
    print(f"Fetching column metadata for {len(TARGET_TABLES)} tables...")
    table_columns = collections.defaultdict(list)
    
    from sqlalchemy import bindparam
    
    query = text("""
        SELECT TABLE_NAME, COLUMN_NAME 
        FROM SYS.TABLE_COLUMNS 
        WHERE SCHEMA_NAME = :schema AND TABLE_NAME IN :tables
        ORDER BY TABLE_NAME, POSITION
    """).bindparams(bindparam("tables", expanding=True))
    
    with engine.connect() as conn:
        result = conn.execute(query, {"schema": SCHEMA_NAME, "tables": TARGET_TABLES})
        for row in result:
            table_columns[row[0]].append(row[1])
            
    # Step 2 — Build a reverse PK lookup
    print("Building reverse PK lookup...")
    reverse_pk_lookup = collections.defaultdict(list)
    for table_name, pks in KNOWN_PKS.items():
        for pk in pks:
            reverse_pk_lookup[pk].append(table_name)
            
    # Step 3 — Infer edges
    print("Inferring relationships...")
    inferred_edges = []
    
    for source_table in TARGET_TABLES:
        if source_table not in table_columns:
            continue
            
        for column_name in table_columns[source_table]:
            if column_name in reverse_pk_lookup:
                referenced_tables = reverse_pk_lookup[column_name]
                
                for target_table in referenced_tables:
                    # Referenced table is NOT the same as the source table
                    if target_table == source_table:
                        continue
                        
                    # Determine confidence
                    target_pks = KNOWN_PKS.get(target_table, [])
                    
                    if len(target_pks) == 1 and column_name == target_pks[0]:
                        confidence = 'HIGH'
                    elif column_name in target_pks:
                        confidence = 'MEDIUM'
                    else:
                        # Should not really happen based on logic but as a fallback
                        confidence = 'LOW'
                        
                    # Downgrade if the column appears as PK in more than 3 tables (too ambiguous)
                    if len(referenced_tables) > 3:
                        confidence = 'LOW'
                        
                    inferred_edges.append({
                        "from_table": source_table,
                        "from_column": column_name,
                        "to_table": target_table,
                        "to_column": column_name,
                        "confidence": confidence
                    })
                    
    # Step 4 — Deduplicate and sort
    # Deduplicate based on unique tuple of from/to table/column
    unique_edges = {}
    for edge in inferred_edges:
        key = (edge["from_table"], edge["from_column"], edge["to_table"], edge["to_column"])
        if key not in unique_edges:
            unique_edges[key] = edge
        else:
            # Keep the highest confidence if duplicate found (unlikely here but safe)
            conf_map = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
            if conf_map[edge["confidence"]] > conf_map[unique_edges[key]["confidence"]]:
                unique_edges[key] = edge
                
    final_edges = list(unique_edges.values())
    
    # Sort by confidence: HIGH first, then MEDIUM, then LOW
    conf_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    final_edges.sort(key=lambda x: (conf_order[x["confidence"]], x["from_table"], x["to_table"]))
    
    # Step 5 — Save and print
    output_path = os.path.join(os.path.dirname(__file__), '../graph/inferred_edges.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(final_edges, f, indent=2)
        
    print(f"\nSaved {len(final_edges)} inferred edges to {output_path}")
    
    # Print summary table
    print(f"\n{'From Table':<25} | {'From Column':<20} | {'To Table':<25} | {'Confidence':<10}")
    print("-" * 85)
    
    counts = collections.Counter()
    for edge in final_edges:
        print(f"{edge['from_table']:<25} | {edge['from_column']:<20} | {edge['to_table']:<25} | {edge['confidence']:<10}")
        counts[edge['confidence']] += 1
        
    print("\nSummary Counts:")
    print(f"HIGH:   {counts['HIGH']}")
    print(f"MEDIUM: {counts['MEDIUM']}")
    print(f"LOW:    {counts['LOW']}")
    
if __name__ == '__main__':
    infer_relationships()
