import sys, os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Step 1: Ensure Python can find the src module regardless of how the test is run.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load environment variables
load_dotenv()

HANA_HOST = os.getenv("HANA_HOST")
HANA_PORT = os.getenv("HANA_PORT")
HANA_USER = os.getenv("HANA_USER")
HANA_PASSWORD = os.getenv("HANA_PASSWORD")

# Build the SQLAlchemy connection URL
# Mandatory parameters for SAP HANA Cloud: encrypt=true and sslValidateCertificate=false
HANA_URL = f"hana+hdbcli://{HANA_USER}:{HANA_PASSWORD}@{HANA_HOST}:{HANA_PORT}?encrypt=true&sslValidateCertificate=false"

# Create SQLAlchemy engine with pool_pre_ping to detect dead connections
engine = create_engine(HANA_URL, pool_pre_ping=True)

def test_connection():
    """
    Verifies the connection to SAP HANA Cloud by executing a ping query on the DUMMY table.
    """
    print("Testing SAP HANA connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM DUMMY")).fetchone()
            if result and result[0] == 1:
                print("SAP HANA connection successful.")
            else:
                print("SAP HANA connection failed: Unexpected result from DUMMY table.")
    except Exception as e:
        print(f"SAP HANA connection failed: {str(e)}")

def get_engine():
    """
    Returns the initialized SQLAlchemy engine object.
    """
    return engine

if __name__ == '__main__':
    test_connection()
