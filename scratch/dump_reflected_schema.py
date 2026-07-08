import sys
import os
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.schema_reflector import SchemaReflector

def main():
    print("Initializing SchemaReflector...")
    reflector = SchemaReflector()
    
    print("Fetching and filtering metadata...")
    meta = reflector.fetch_and_filter()
    
    output_path = os.path.join(os.path.dirname(__file__), "reflected_schema_dump.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    print(f"\nSuccessfully dumped reflected schema metadata to:")
    print(f"  {output_path}\n")
    print(f"Cubes/Tables included ({len(meta.get('cubes', []))}):")
    for cube in meta.get("cubes", []):
        print(f"  - {cube['name']} (Measures: {len(cube.get('measures', []))}, Dimensions: {len(cube.get('dimensions', []))})")
        
    print(f"\nJoin pathways detected ({len(meta.get('joins', []))}):")
    for join in meta.get("joins", []):
        print(f"  - {join['from_cube']}.{join['from_column']} -> {join['to_cube']}.{join['to_column']} ({join['relationship_type']})")

if __name__ == "__main__":
    main()
