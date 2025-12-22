import requests

url = "http://localhost:8000/auth/login"
data = {"username": "admin@example.com", "password": "adminpass"}
response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
