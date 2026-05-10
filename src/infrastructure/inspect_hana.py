import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.infrastructure.hana_connection import get_engine
from sqlalchemy import text

def inspect_schemas():
    """
    Connects to HANA and lists all user schemas along with their table counts.
    """
    engine = get_engine()
    print("Inspecting SAP HANA Schemas...\n")
    
    query = text("""
        SELECT SCHEMA_NAME, COUNT(*) as TABLE_COUNT
        FROM SYS.TABLES
        WHERE SCHEMA_NAME NOT LIKE '_SYS%'
        AND SCHEMA_NAME NOT IN ('SYS', 'SYSTEM')
        GROUP BY SCHEMA_NAME
        ORDER BY TABLE_COUNT DESC
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            rows = result.fetchall()
            
            if not rows:
                print("No user schemas found.")
                return

            print(f"{'Schema Name':<30} | {'Table Count':<12}")
            print("-" * 45)
            for row in rows:
                print(f"{row[0]:<30} | {row[1]:<12}")
                
    except Exception as e:
        print(f"Inspection failed: {str(e)}")

if __name__ == '__main__':
    inspect_schemas()
