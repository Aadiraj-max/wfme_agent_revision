import sys, os
from dotenv import load_dotenv
from sqlalchemy import text
from src.infrastructure.hana_connection import get_engine

# Ensure Python can find the src module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

load_dotenv()

def list_all_objects():
    engine = get_engine()
    schema = 'WFMSCH_1'
    
    print(f"Listing all TABLES and VIEWS in schema {schema}...\n")
    
    query = text("""
        SELECT OBJECT_NAME, OBJECT_TYPE
        FROM SYS.OBJECTS
        WHERE SCHEMA_NAME = :s
        AND OBJECT_TYPE IN ('VIEW', 'TABLE')
        ORDER BY OBJECT_TYPE, OBJECT_NAME
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {'s': schema})
            rows = result.fetchall()
            
            if not rows:
                print(f"No objects found in schema {schema}.")
                return
                
            print(f"{'Object Name':<40} | {'Type':<10}")
            print("-" * 55)
            for row in rows:
                print(f"{row[0]:<40} | {row[1]:<10}")
            
            print(f"\nTotal objects found: {len(rows)}")
                
    except Exception as e:
        print(f"Error listing objects: {str(e)}")

if __name__ == '__main__':
    list_all_objects()
