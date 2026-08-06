"""Test unenroll event via the live HTTP API"""
import requests
import json

BASE = "http://localhost:8000"

# Login as Mayur first
login_resp = requests.post(f"{BASE}/auth/login", json={
    "email": "svmayurkaarthic@gmail.com",
    "password": "password123"
})
if login_resp.status_code != 200:
    print("Login failed:", login_resp.text)
    exit(1)

token = login_resp.json().get("access_token")
print(f"Logged in, token: {token[:40]}...")

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Send unenroll event via /events/single
payload = {
    "session_id": "test-unenroll-sess-001",
    "event_type": "unenroll",
    "product_id": "bd4e24e4-7eea-41d2-a038-d7044befa545",
    "metadata": {
        "course_title": "Reverse Engineering & Malware Analysis Studio",
        "category": "Cyber Security",
        "action": "unenroll"
    }
}

resp = requests.post(f"{BASE}/events/single", json=payload, headers=headers)
print(f"\n/events/single unenroll → status={resp.status_code}")
print(f"Response: {resp.text[:300]}")

# Also test lesson_complete
payload2 = {
    "session_id": "test-lesson-sess-001",
    "event_type": "lesson_complete",
    "product_id": "bd4e24e4-7eea-41d2-a038-d7044befa545",
    "metadata": {
        "course_title": "Reverse Engineering & Malware Analysis Studio",
        "category": "Cyber Security",
        "lesson_name": "Module 1: Intro to Malware"
    }
}
resp2 = requests.post(f"{BASE}/events/single", json=payload2, headers=headers)
print(f"\n/events/single lesson_complete → status={resp2.status_code}")
print(f"Response: {resp2.text[:300]}")
