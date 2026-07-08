import requests
import json

def fetch_meta():
    try:
        res = requests.get("http://localhost:4000/cubejs-api/v1/meta", timeout=5)
        print("Status:", res.status_code)
        meta = res.json()
        for cube in meta.get("cubes", []):
            print(f"\nCube: {cube['name']}")
            print("  Measures:")
            for m in cube.get("measures", []):
                print(f"    - {m['name']} ({m.get('type')})")
            print("  Dimensions:")
            for d in cube.get("dimensions", []):
                print(f"    - {d['name']} ({d.get('type')})")
    except Exception as e:
        print("Error fetching Cube meta:", e)

if __name__ == "__main__":
    fetch_meta()
