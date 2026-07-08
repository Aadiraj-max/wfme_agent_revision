import json

with open("scratch/meta_sample.json") as f:
    meta = json.load(f)

for cube in meta.get("cubes", []):
    time_dims = [d["name"] for d in cube.get("dimensions", []) if d.get("type") == "time"]
    if time_dims:
        print(f"Cube: {cube['name']} -> Time Dimensions: {time_dims}")
