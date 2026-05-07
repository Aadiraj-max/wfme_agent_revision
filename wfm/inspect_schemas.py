from db_connection import get_hana_engine
from sqlalchemy import text
import json

tables_to_inspect = ["USERS", "DEPARTMENT", "EMPLOYEE_PROFILES", "SHIFTS", "ROSTER_ITEM"]

try:
    engine = get_hana_engine()
    print("Inspecting table schemas in WFMSCH_1...")
    
    with engine.connect() as conn:
        for table in tables_to_inspect:
            print(f"\n--- {table} ---")
            query = text(f"SELECT COLUMN_NAME, DATA_TYPE_NAME FROM TABLE_COLUMNS WHERE SCHEMA_NAME = 'WFMSCH_1' AND TABLE_NAME = '{table}' ORDER BY POSITION")
            result = conn.execute(query)
            for row in result:
                print(f"{row[0]}: {row[1]}")

except Exception as e:
    print(f"Error: {e}")
