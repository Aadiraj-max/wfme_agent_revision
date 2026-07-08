import os
import sys
import json

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.schema_reflector import SchemaReflector

def main():
    print("Initializing SchemaReflector...")
    reflector = SchemaReflector()
    
    print("Fetching and filtering Cube schema...")
    meta = reflector.fetch_and_filter()
    
    print(f"\nFiltered cubes count: {len(meta['cubes'])}")
    for cube in meta['cubes']:
        print(f"- Cube: {cube['name']} ({len(cube['measures'])} measures, {len(cube['dimensions'])} dimensions)")
        
    print(f"\nParsed joins count: {len(meta['joins'])}")
    for join in meta['joins']:
        print(f"- Join: {join['from_cube']}.{join['from_column']} -> {join['to_cube']}.{join['to_column']} ({join['relationship_type']})")

if __name__ == "__main__":
    main()
