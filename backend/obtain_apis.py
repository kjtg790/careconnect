import requests
import json

url = "http://localhost:8000/openapi.json"
response = requests.get(url)

if response.status_code == 200:
    openapi_data = response.json()
    
    for path, methods in openapi_data["paths"].items():
        print(f"Path: {path}")
        for method, details in methods.items():
            print(f"  Method: {method.upper()}")
            print(f"  Summary: {details.get('summary')}")
            params = details.get('parameters', [])
            if params:
                print("  Parameters:")
                for param in params:
                    name = param.get('name')
                    location = param.get('in')
                    required = param.get('required', False)
                    param_type = param.get('schema', {}).get('type')
                    print(f"    - {name} ({location}) - type: {param_type} - required: {required}")
            print()
else:
    print(f"Failed to fetch OpenAPI schema: {response.status_code}")
