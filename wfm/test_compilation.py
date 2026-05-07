import ibis
import ibis.expr.datatypes as dt
from db_connection import get_ibis_connection

try:
    # 1. Get a local connection for expression building
    con = get_ibis_connection()
    print(f"Ibis local backend: {con.name}")

    # 2. Define a dummy table schema
    schema = ibis.schema({"id": dt.int64, "name": dt.string, "value": dt.float64})
    t = ibis.table(schema, name="MY_TABLE")

    # 3. Build a simple expression
    expr = t.filter(t.id > 100).select("name", "value").limit(10)

    # 4. Attempt to compile to HANA SQL using the new dialect support
    print("\nAttempting to compile to SAP HANA SQL...")
    # In Ibis 12, to_sql often uses sqlglot
    hana_sql = ibis.to_sql(expr, dialect="hana")
    print("--- GENERATED HANA SQL ---")
    print(hana_sql)
    print("--------------------------")

except Exception as e:
    print(f"Compilation failed: {e}")
    # Try fallback to postgres dialect just to see if to_sql works at all
    try:
        print("\nFalling back to 'postgres' dialect for testing...")
        pg_sql = ibis.to_sql(expr, dialect="postgres")
        print("--- GENERATED POSTGRES SQL ---")
        print(pg_sql)
    except Exception as e2:
        print(f"Postgres compilation also failed: {e2}")
