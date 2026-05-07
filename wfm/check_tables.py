from db_connection import get_hana_engine
from sqlalchemy import text

try:
    engine = get_hana_engine()
    print("Connecting to SAP HANA via SQLAlchemy...")
    
    with engine.connect() as conn:
        # Use a raw SQL query to list tables in the WFMSCH_1 schema
        query = text("SELECT TABLE_NAME FROM TABLES WHERE SCHEMA_NAME = 'WFMSCH_1'")
        result = conn.execute(query)
        
        tables = [row[0] for row in result]
        print(f"Tables in WFMSCH_1 ({len(tables)}):")
        for table in tables:
            print(f" - {table}")

except Exception as e:
    print(f"Error: {e}")
