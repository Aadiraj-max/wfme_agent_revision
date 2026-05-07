import ibis
import sys

print(f"Python version: {sys.version}")
print(f"Ibis version: {ibis.__version__}")

try:
    print(f"Available backends: {ibis.util.get_backend_names()}")
except Exception as e:
    print(f"Could not list backends: {e}")

try:
    import ibis.backends.sqlalchemy as sa
    print("Found ibis.backends.sqlalchemy")
    print(f"Methods in sa: {dir(sa)}")
except ImportError:
    print("Could not import ibis.backends.sqlalchemy")

try:
    from ibis.backends.base.sql.alchemy import BaseAlchemyBackend
    print("Found BaseAlchemyBackend")
except ImportError:
    print("Could not import BaseAlchemyBackend")

try:
    import sqlalchemy
    print(f"SQLAlchemy version: {sqlalchemy.__version__}")
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:")
    con = ibis.connect(engine)
    print("ibis.connect(sqlite_engine) worked!")
except Exception as e:
    print(f"ibis.connect(sqlite_engine) failed: {e}")
