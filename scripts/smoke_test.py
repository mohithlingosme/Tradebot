"""Quick smoke tests to validate backend API imports and basic endpoints without starting uvicorn.

This script imports the FastAPI app (so it runs the same import-time code)
and uses TestClient to make a few requests that exercise common code paths.

Run:
    python scripts/smoke_test.py

"""

from fastapi.testclient import TestClient
import sys
import os
from pathlib import Path

# Add repository root to sys.path so 'backend' package import works when running as script
repo_root = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, repo_root)

from backend.api.main import app


def run_smoke_tests():
    client = TestClient(app)

    print("GET /")
    r = client.get("/")
    print(r.status_code, r.json())

    print("GET /status")
    r = client.get("/status")
    print(r.status_code, r.json())

    print("GET /health")
    r = client.get("/health")
    print(r.status_code, r.json())

    print("GET /metrics")
    r = client.get("/metrics")
    print(r.status_code, r.json().keys())

    # Test login & protected endpoints
    print("POST /auth/login (admin)")
    r = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    print(r.status_code, r.json())

    if r.status_code == 200:
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print("GET /protected (with token)")
        r = client.get("/protected", headers=headers)
        print(r.status_code, r.json())

        print("POST /trades (with token)")
        r = client.post("/trades", headers=headers, json={"symbol":"AAPL","side":"buy","quantity":1,"price":100.0})
        print(r.status_code, r.json())

    else:
        print("Login failed, skipping protected endpoint tests")


if __name__ == '__main__':
    run_smoke_tests()
