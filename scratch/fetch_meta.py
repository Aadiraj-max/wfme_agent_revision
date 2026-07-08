import requests
import json

try:
    response = requests.get("http://localhost:4000/cubejs-api/v1/meta", timeout=10)
    print("Status code:", response.status_code)
    if response.status_code == 200:
        meta = response.json()
        print("Cubes found:", [c["name"] for c in meta.get("cubes", [])])
        # Save a sample to file
        with open("scratch/meta_sample.json", "w") as f:
            json.dump(meta, f, indent=2)
        print("Saved meta to scratch/meta_sample.json")
    else:
        print("Response text:", response.text)
except Exception as e:
    print("Error:", e)
