import sys
import os
import chromadb

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.retrieval.vector_store import BSLVectorStore

store = BSLVectorStore()
print("Current collection count:", store.get_collection_count())
