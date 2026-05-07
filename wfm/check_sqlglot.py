import sqlglot
print(f"SQLGlot version: {sqlglot.__version__}")
print(f"Available dialects: {sorted(sqlglot.dialects.DIALECTS)}")
