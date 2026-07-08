import sys
import os
import pytest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.schema_reflector import SchemaReflector, CORE_TABLE_ALLOWLIST
from src.graph.schema_graph import SchemaGraph
from src.retrieval.vector_store import BSLVectorStore

@pytest.fixture
def sample_meta():
    reflector = SchemaReflector()
    return reflector.fetch_and_filter()

def test_schema_reflector_allowlist(sample_meta):
    print("Running: test_schema_reflector_allowlist")
    # Verify reflector filters strictly to allowed cubes
    for cube in sample_meta["cubes"]:
        assert cube["name"] in CORE_TABLE_ALLOWLIST

def test_schema_graph_build(sample_meta):
    print("Running: test_schema_graph_build")
    # Verify graph can initialize and correctly resolved allowed joins
    graph = SchemaGraph(joins=sample_meta["joins"])
    
    # Check that nodes are in CORE_TABLE_ALLOWLIST
    for node in graph.get_all_tables():
        assert node in CORE_TABLE_ALLOWLIST

def test_schema_graph_path_validation(sample_meta):
    print("Running: test_schema_graph_path_validation")
    graph = SchemaGraph(joins=sample_meta["joins"])
    
    # Test path validation
    targets = ["UserDetails", "Locations", "Position"]
    validated = graph.validate_path(targets)
    
    # UserDetails and Locations/Position should have a path
    assert len(validated) > 0
    assert validated[0] == "UserDetails"

def test_vector_store_indexing(tmp_path):
    print("Running: test_vector_store_indexing")
    # Use a temp directory for the test to avoid polluting the dev DB
    test_db_dir = os.path.join(str(tmp_path), "test_chroma_store")
    store = BSLVectorStore(persist_dir=test_db_dir)
    
    # Use a tiny mock schema to verify indexing logic without making 150 API calls
    mock_meta = {
        "cubes": [
            {
                "name": "Position",
                "title": "Position Details",
                "measures": [
                    {"name": "Position.fteAvg", "title": "Average FTE", "type": "number"}
                ],
                "dimensions": [
                    {"name": "Position.positionid", "title": "Position ID", "type": "string"}
                ]
            }
        ]
    }
    
    total_indexed = store.rebuild_index(mock_meta)
    assert total_indexed == 3  # 1 cube + 1 measure + 1 dimension
    assert store.get_collection_count() == 3


if __name__ == '__main__':
    pytest.main([__file__])
