import sys, os
from dotenv import load_dotenv
from sqlalchemy import text
from src.infrastructure.hana_connection import get_engine

# Ensure Python can find the src module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

load_dotenv()

def check_columns():
    engine = get_engine()
    tables = ['EMP_PLANNING', 'EMP_WORKSLOT', 'ROSTER_ITEM']
    schema = 'WFMSCH_1'
    
    print(f"Checking columns for {', '.join(tables)} in schema {schema}...\n")
    
    with engine.connect() as conn:
        for tbl in tables:
            query = text("""
                SELECT COLUMN_NAME 
                FROM SYS.TABLE_COLUMNS 
                WHERE SCHEMA_NAME = :s AND TABLE_NAME = :t 
                ORDER BY POSITION
            """)
            try:
                result = conn.execute(query, {'s': schema, 't': tbl})
                cols = [row[0] for row in result.fetchall()]
                print(f"{tbl}: {cols}")
            except Exception as e:
                print(f"Error checking {tbl}: {str(e)}")

if __name__ == '__main__':
    check_columns()
