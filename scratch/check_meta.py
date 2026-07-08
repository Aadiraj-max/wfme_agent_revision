import requests
try:
    r = requests.get("http://localhost:4000/cubejs-api/v1/meta")
    if r.status_code == 200:
        data = r.json()
        names = [c["name"] for c in data.get("cubes", [])]
        print("Cubes in live Cube.js /meta:")
        print(names)
    else:
        print(f"Cube.js returned status code {r.status_code}: {r.text}")
except Exception as e:
    print(f"Error connecting to Cube.js: {e}")
