import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import json
from sqlalchemy import text
from src.infrastructure.hana_connection import get_engine
from src.graph.logical_edges import LOGICAL_EDGES

SCHEMA_NAME = 'WFMSCH_1'

TARGET_TABLES = [
    'EMP_CONTRACT_DETAILS', 'EMP_HR', 'EMP_MANAGER', 'EMP_PLANNING',
    'EMP_REQUESTS', 'EMP_SKILL_CERTIFICATE', 'EMP_WORKSLOT', 'LOCATIONS',
    'POSITION', 'ROLE_DEFINATION', 'ROSTER_HEADER', 'ROSTER_ITEM',
    'SHIFTCODE_SLOTMAPPING', 'SKILLS_CERTIFICATE', 'STORES', 'TEAMS',
    'USER_DETAILS', 'VACATION_BALANCE', 'VACATION_HISTORY', 'WORKDAY_TYPES',
    'views::USER_DETAIL', 'views::V_MASTER_ORG', 'views::V_PLANNED_EMP',
    'views::V_ROSTER_PLANNED_EMP'
]

VIEW_TABLES = [t for t in TARGET_TABLES if t.startswith('views::')]
PHYSICAL_TABLES = [t for t in TARGET_TABLES if not t.startswith('views::')]

DOMAIN_MAP = {
    'EMP_CONTRACT_DETAILS': 'HR', 'EMP_HR': 'HR', 'EMP_MANAGER': 'HR', 'EMP_REQUESTS': 'HR', 
    'EMP_SKILL_CERTIFICATE': 'HR', 'POSITION': 'HR', 'ROLE_DEFINATION': 'HR', 
    'SKILLS_CERTIFICATE': 'HR', 'USER_DETAILS': 'HR', 'VACATION_BALANCE': 'HR', 'VACATION_HISTORY': 'HR', 
    'views::USER_DETAIL': 'HR', 'views::V_MASTER_ORG': 'HR',
    'EMP_PLANNING': 'OPS', 'EMP_WORKSLOT': 'OPS', 'LOCATIONS': 'OPS', 'ROSTER_HEADER': 'OPS', 
    'ROSTER_ITEM': 'OPS', 'SHIFTCODE_SLOTMAPPING': 'OPS', 'STORES': 'OPS', 'TEAMS': 'OPS', 
    'views::V_PLANNED_EMP': 'OPS', 'views::V_ROSTER_PLANNED_EMP': 'OPS', 'WORKDAY_TYPES': 'OPS'
}

def pull_targeted_schema():
    engine = get_engine()
    
    # Construct IN clause string (plain comma-separated string of quoted table names)
    in_clause = ", ".join([f"'{t}'" for t in TARGET_TABLES])
    
    with engine.connect() as conn:
        # Step 1 — Pull table comments
        print("Step 1: Pulling table comments...")
        table_comments = {t: "" for t in TARGET_TABLES}
        comments_sql = f"""
            SELECT TABLE_NAME, COMMENTS
            FROM SYS.TABLES
            WHERE SCHEMA_NAME = '{SCHEMA_NAME}'
            AND TABLE_NAME IN ({in_clause})
        """
        result = conn.execute(text(comments_sql))
        for row in result:
            table_comments[row[0]] = row[1] if row[1] else ""
            
        # Step 2 — Pull all columns for all tables
        print("Step 2: Pulling column metadata...")
        table_columns = {t: [] for t in TARGET_TABLES}
        
        # Physical tables from SYS.TABLE_COLUMNS
        physical_in = ", ".join([f"'{t}'" for t in PHYSICAL_TABLES])
        physical_sql = f"""
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE_NAME, LENGTH, IS_NULLABLE, COMMENTS, POSITION
            FROM SYS.TABLE_COLUMNS
            WHERE SCHEMA_NAME = '{SCHEMA_NAME}'
            AND TABLE_NAME IN ({physical_in})
            ORDER BY TABLE_NAME, POSITION
        """
        result = conn.execute(text(physical_sql))
        for row in result:
            table_columns[row[0]].append({
                "name": row[1],
                "type": row[2],
                "length": row[3],
                "nullable": row[4],
                "comments": row[5] if row[5] else ""
            })
            
        # Views from SYS.VIEW_COLUMNS
        view_in = ", ".join([f"'{t}'" for t in VIEW_TABLES])
        view_sql = f"""
            SELECT VIEW_NAME, COLUMN_NAME, DATA_TYPE_NAME, LENGTH, IS_NULLABLE, POSITION
            FROM SYS.VIEW_COLUMNS
            WHERE SCHEMA_NAME = '{SCHEMA_NAME}'
            AND VIEW_NAME IN ({view_in})
            ORDER BY VIEW_NAME, POSITION
        """
        result = conn.execute(text(view_sql))
        for row in result:
            table_columns[row[0]].append({
                "name": row[1],
                "type": row[2],
                "length": row[3],
                "nullable": row[4],
                "comments": "" # No comments column in VIEW_COLUMNS
            })
            
        # Step 3 — Pull Primary Keys (Physical tables only)
        print("Step 3: Pulling primary keys...")
        table_pks = {t: [] for t in TARGET_TABLES}
        pks_sql = f"""
            SELECT TABLE_NAME, COLUMN_NAME
            FROM SYS.CONSTRAINTS
            WHERE SCHEMA_NAME = '{SCHEMA_NAME}'
            AND IS_PRIMARY_KEY = 'TRUE'
            AND TABLE_NAME IN ({physical_in})
        """
        result = conn.execute(text(pks_sql))
        for row in result:
            table_pks[row[0]].append(row[1])
            
        # Step 4 — Assemble final schema dict
        print("Step 4: Assembling final schema...")
        final_schema = {}
        for table in TARGET_TABLES:
            # Filter LOGICAL_EDGES where from_table or to_table matches
            edges = [edge for edge in LOGICAL_EDGES if edge["from_table"] == table or edge["to_table"] == table]
            
            final_schema[table] = {
                'physical_name': f'{SCHEMA_NAME}.{table}',
                'domain': DOMAIN_MAP.get(table, 'UNKNOWN'),
                'comments': table_comments.get(table, ""),
                'primary_keys': table_pks.get(table, []),
                'logical_edges': edges,
                'columns': table_columns.get(table, [])
            }
            
        # Step 5 — Save
        output_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../engine/raw_schema.json'))
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(final_schema, f, indent=2, default=str)
            
        print("\nSchema pulled successfully.")
        for table in sorted(TARGET_TABLES):
            col_count = len(table_columns.get(table, []))
            print(f"Table: {table:<30} | Columns: {col_count}")

if __name__ == '__main__':
    pull_targeted_schema()
