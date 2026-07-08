import requests

def fetch_selected_meta():
    try:
        res = requests.get("http://localhost:4000/cubejs-api/v1/meta", timeout=5)
        meta = res.json()
        target_cubes = ["UserDetails", "Stores", "Locations"]
        for cube in meta.get("cubes", []):
            if cube["name"] in target_cubes:
                print(f"\nCube: {cube['name']}")
                print("  Measures:")
                for m in cube.get("measures", []):
                    print(f"    - {m['name']} ({m.get('type')})")
                print("  Dimensions:")
                for d in cube.get("dimensions", []):
                    print(f"    - {d['name']} ({d.get('type')})")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    fetch_selected_meta()
