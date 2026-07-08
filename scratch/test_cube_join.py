import requests
import json

def test_query():
    payload = {
        "query": {
            "measures": ["UserDetails.count"],
            "dimensions": ["Locations.locationdesc"],
            "limit": 10
        }
    }
    try:
        res = requests.post("http://localhost:4000/cubejs-api/v1/load", json=payload, timeout=5)
        print("Status:", res.status_code)
        print("Response:", json.dumps(res.json(), indent=2))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_query()
