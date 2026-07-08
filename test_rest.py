from dotenv import load_dotenv
load_dotenv()
from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
import requests

proxy = get_proxy_client('gen-ai-hub')
deps = [d for d in proxy.get_deployments() if d.model_name == 'amazon--nova-pro']
if not deps:
    print("Deployment not found")
else:
    dep = deps[0]
    url = f"{dep.url}/converse"
    headers = proxy.request_header.copy()
    headers['Content-Type'] = 'application/json'
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Hello, how are you?"}]
            }
        ],
        "inferenceConfig": {
            "temperature": 0.0
        }
    }
    
    resp = requests.post(url, headers=headers, json=payload)
    print(resp.status_code)
    print(resp.text)
