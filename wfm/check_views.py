from db_connection import get_hana_connection
import ibis

try:
    con = get_hana_connection()
    print("Connected successfully!")
    
    # In Ibis, views are often listed along with tables.
    # However, SAP HANA might need a specific query or schema inspection.
    # con.list_tables() usually covers both in many backends.
    
    # Let's try to query the VIEWS system table directly via Ibis
    # We can use con.sql() to run a raw query if needed, or inspect the backend.
    
    print("Attempting to list views in WFMSCH_1...")
    # For now, let's just list everything and see
    all_objects = con.list_tables(schema="WFMSCH_1")
    print(f"Objects in WFMSCH_1 ({len(all_objects)}):")
    for obj in all_objects:
        print(f" - {obj}")

except Exception as e:
    print(f"Error: {e}")
