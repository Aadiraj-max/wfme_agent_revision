import ibis
import ibis.expr.datatypes as dt

# Create a dummy table
schema = ibis.schema({"val": dt.string})
t = ibis.table(schema, name="TEST_TABLE")

# Test casting
expr = t.val.cast("int64")

print("--- TESTING POSTGRES CAST COMPILATION ---")
try:
    sql = ibis.to_sql(expr, dialect="postgres")
    print(f"Postgres Output: {sql}")
except Exception as e:
    print(f"Postgres failed: {e}")

try:
    sql_duck = ibis.to_sql(expr, dialect="duckdb")
    print(f"DuckDB Output: {sql_duck}")
except Exception as e:
    print(f"DuckDB failed: {e}")
