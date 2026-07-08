import sys, os
from dotenv import load_dotenv
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.infrastructure.hana_connection import get_engine

load_dotenv()

def inspect_db():
    engine = get_engine()
    with engine.connect() as conn:
        print("--- STORES ---")
        try:
            res = conn.execute(text('SELECT * FROM "WFMSCH_1"."STORES" LIMIT 5'))
            print("Columns:", list(res.keys()))
            for r in res.fetchall():
                print(r)
        except Exception as e:
            print("Error query STORES:", e)

        print("\n--- LOCATIONS ---")
        try:
            res = conn.execute(text('SELECT * FROM "WFMSCH_1"."LOCATIONS" LIMIT 5'))
            print("Columns:", list(res.keys()))
            for r in res.fetchall():
                print(r)
        except Exception as e:
            print("Error query LOCATIONS:", e)

        print("\n--- STORES where ID or NAME like 1309 ---")
        try:
            res = conn.execute(text('SELECT * FROM "WFMSCH_1"."STORES" WHERE "ID" = \'1309\' OR "NAME" LIKE \'%1309%\''))
            for r in res.fetchall():
                print(r)
        except Exception as e:
            print("Error query STORES search:", e)

        print("\n--- LOCATIONS where LOCATIONID or LOCATIONDESC like 1309 ---")
        try:
            res = conn.execute(text('SELECT * FROM "WFMSCH_1"."LOCATIONS" WHERE "LOCATIONID" = \'1309\' OR "LOCATIONDESC" LIKE \'%1309%\''))
            for r in res.fetchall():
                print(r)
        except Exception as e:
            print("Error query LOCATIONS search:", e)

if __name__ == "__main__":
    inspect_db()
