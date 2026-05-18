import httpx

base_url = "https://irrigation-api-v2.onrender.com/api/v1"

endpoints = [
    "",
    "/auth/me",
    "/zones",
    "/dashboard",
    "/farms/farm",
]

print("Probing Render API endpoints:")
with httpx.Client() as client:
    for ep in endpoints:
        url = f"{base_url}{ep}"
        try:
            resp = client.get(url)
            print(f"GET {url} -> Status: {resp.status_code}")
            print(f"  Response: {resp.text[:200]}")
        except Exception as e:
            print(f"GET {url} -> Error: {e}")
