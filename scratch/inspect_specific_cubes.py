import json

with open("scratch/meta_sample.json") as f:
    meta = json.load(f)

specific_cubes = ["Position", "RosterItem", "RosterHeader", "ShiftcodeSlotmapping", "UserDetails", "EmpRequests"]

for cube in meta.get("cubes", []):
    if cube["name"] in specific_cubes:
        print(f"\nCube: {cube['name']}")
        measures = [m["name"] for m in cube.get("measures", [])]
        dimensions = [d["name"] for d in cube.get("dimensions", [])]
        print(f"  Measures: {measures}")
        print(f"  Dimensions: {dimensions}")
