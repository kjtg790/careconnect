import requests

url = "http://127.0.0.1:8000/api/update-interview"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3Yjk5NWMwOC05YzBjLTQwOTctOWU4Ny1lODk0OGE5NGY3ZDYiLCJleHAiOjE3NTIwODQ5ODd9.cJDx0v9aHgTorFvvST5wydBpbkwtZ-dZQ_s4DFJNkzc",
    "Content-Type": "application/json"
}
payload = {
    "id": "ae13c7da-da18-4f28-a850-760ecfa56ae4",
    "message": "Test update",
    "status": "accepted"
}
resp = requests.put(url, headers=headers, json=payload)
print(resp.status_code)
print(resp.text)
