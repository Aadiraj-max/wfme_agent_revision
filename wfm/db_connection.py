import os
import ibis
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load credentials from .env in the root directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

HANA_HOST = os.getenv("HANA_HOST")
HANA_PORT = os.getenv("HANA_PORT", "443")
HANA_USER = os.getenv("HANA_USER")
HANA_PASSWORD = os.getenv("HANA_PASSWORD")

def get_hana_engine():
    """Returns a raw SQLAlchemy engine for execution."""
    connection_string = f"hana://{HANA_USER}:{HANA_PASSWORD}@{HANA_HOST}:{HANA_PORT}"
    engine = create_engine(
        connection_string,
        connect_args={
            'encrypt': 'true',
            'sslValidateCertificate': 'false',
            'sslCryptoProvider': 'openssl'
        }
    )
    return engine

def get_ibis_connection():
    """
    Returns a local Ibis connection for expression building.
    Since Ibis doesn't support HANA natively for execution, we use a local backend
    to build expressions and then compile them to HANA SQL via sqlglot.
    """
    try:
        # DuckDB is the preferred local backend for Ibis 12
        import ibis.backends.duckdb
        return ibis.duckdb.connect()
    except ImportError:
        try:
            # Fallback to an in-memory SQLite
            import ibis.backends.sqlite
            return ibis.sqlite.connect(":memory:")
        except ImportError:
            # Last resort: return the top-level ibis module
            # Many Ibis 12 functions work directly on the module
            return ibis

if __name__ == "__main__":
    try:
        print(f"Testing raw SQLAlchemy connection to {HANA_HOST}...")
        engine = get_hana_engine()
        with engine.connect() as conn:
            # Simple query to verify connection
            result = conn.execute(text("SELECT 'SQLAlchemy Connection Successful' FROM DUMMY")).scalar()
            print(f"HANA says: {result}")
            
        print("\nIbis local backend check...")
        con = get_ibis_connection()
        print(f"Ibis version: {ibis.__version__}")
        print("Ibis is ready for expression building.")
        
    except Exception as e:
        print(f"Connection failed: {e}")
