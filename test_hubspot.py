
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("HUBSPOT_ACCESS_TOKEN")

if not token or token == "YOUR_SERVICE_KEY":
    print("ERROR: Check HUBSPOT_ACCESS_TOKEN in your .env file.")
    raise SystemExit(1)

url = "https://api.hubapi.com/crm/v3/objects/contacts"

response = requests.get(
    url,
    headers={"Authorization": f"Bearer {token}"},
    params={"limit": 5},
    timeout=30,
)

if response.status_code == 200:
    data = response.json()
    print("SUCCESS: HubSpot connection working!")
    print("Contacts received:", len(data.get("results", [])))
elif response.status_code == 401:
    print("ERROR: Invalid service key. Check your .env file.")
elif response.status_code == 403:
    print("ERROR: Access denied. Check your HubSpot scopes.")
else:
    print("HTTP status:", response.status_code)
    print(response.text[:500])
