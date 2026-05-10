import sys, os
from dotenv import load_dotenv
from sqlalchemy import text
from src.infrastructure.hana_connection import get_engine

# Ensure Python can find the src module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

load_dotenv()

def check_views():
    engine = get_engine()
    objects = ('ROLES', 'SCH_')
    
    print(f"Searching for any objects related to ROLES or SCH_...\n")
    
    obj_query = text("""
        SELECT SCHEMA_NAME, OBJECT_NAME, OBJECT_TYPE 
        FROM SYS.OBJECTS 
        WHERE OBJECT_NAME LIKE :v
        ORDER BY OBJECT_NAME
    """)
    
    try:
        with engine.connect() as conn:
            for obj in objects:
                wildcard = f"%{obj}%"
                print(f"--- Searching for *{obj}* ---")
                res = conn.execute(obj_query, {'v': wildcard})
                rows = res.fetchall()
                for row in rows:
                    print(f"Found: {row[0]}.{row[1]} | Type: {row[2]}")
                if not rows: print("No results found.")
                print("-" * 30)
                
    except Exception as e:
        print(f"Error during search: {str(e)}")
                
    except Exception as e:
        print(f"Error checking views: {str(e)}")

if __name__ == '__main__':
    check_views()
