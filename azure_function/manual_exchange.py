import os
import requests
from dotenv import load_dotenv

load_dotenv()

STORE_URL = os.getenv("SHOPIFY_STORE_URL")
CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET")
CODE = "7d6ed28c8952034a34af2d0991d60366"

def exchange():
    url = f"https://{STORE_URL}/admin/oauth/access_token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": CODE
    }
    print(f"Échange du code {CODE} pour {STORE_URL}...")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Réponse: {response.text}")

if __name__ == "__main__":
    exchange()
