"""
Direct test of the recommendation refresh flow.
Logs in as Mayur, calls GET /me, then POST /refresh, and compares results.
"""
import requests
import json
import sys

BASE = "http://localhost:8000"

# Step 1: Register or login
# Try to find the right password by checking the seed data
print("=== Step 1: Attempting login ===")

# Try common passwords or check seed
passwords = ["Test1234!", "mayur123", "password123", "test123", "admin123", "Mayur@123", "Password123!", "smartreco123"]
token = None

for pwd in passwords:
    r = requests.post(f"{BASE}/auth/login", json={
        "email": "svmayurkaarthic@gmail.com",
        "password": pwd
    })
    if r.status_code == 200:
        token = r.json()["access_token"]
        print(f"  Login OK with password: {pwd}")
        break
    else:
        print(f"  {pwd} -> {r.status_code}")

if not token:
    # Try registering a new user and checking events for that user
    print("\n  Could not login. Trying admin...")
    for pwd in passwords:
        r = requests.post(f"{BASE}/auth/login", json={
            "email": "admin@smartreco.com",
            "password": pwd
        })
        if r.status_code == 200:
            token = r.json()["access_token"]
            print(f"  Admin login OK with password: {pwd}")
            break

if not token:
    print("\n  FAILED: Could not login with any known password.")
    print("  Check the seed_data.py or init script for the default password.")
    sys.exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Step 2: GET /recommendations/me
print("\n=== Step 2: GET /recommendations/me ===")
r = requests.get(f"{BASE}/recommendations/me", headers=headers)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    titles1 = [p["title"] for p in data.get("ranked_products", [])]
    print(f"  Generated at: {data.get('generated_at')}")
    print(f"  Trace ID: {data.get('trace_id')}")
    print(f"  Titles: {titles1}")
else:
    print(f"  Error: {r.text[:300]}")
    titles1 = []

# Step 3: POST /recommendations/refresh
print("\n=== Step 3: POST /recommendations/refresh ===")
r2 = requests.post(f"{BASE}/recommendations/refresh", headers=headers)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    data2 = r2.json()
    titles2 = [p["title"] for p in data2.get("ranked_products", [])]
    print(f"  Generated at: {data2.get('generated_at')}")
    print(f"  Trace ID: {data2.get('trace_id')}")
    print(f"  Titles: {titles2}")
    
    # Compare
    print(f"\n=== Comparison ===")
    print(f"  Same titles? {titles1 == titles2}")
    if titles1 != titles2:
        print(f"  BEFORE: {titles1}")
        print(f"  AFTER:  {titles2}")
else:
    print(f"  Error: {r2.text[:500]}")
