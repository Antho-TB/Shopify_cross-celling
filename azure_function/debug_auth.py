
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def debug_shopify_auth():
    shop = os.getenv("SHOPIFY_STORE_URL")
    client_id = os.getenv("SHOPIFY_CLIENT_ID")
    client_secret = os.getenv("SHOPIFY_CLIENT_SECRET")
    
    print(f"--- Diagnostic Authentification Shopify ---")
    print(f"Boutique : {shop}")
    print(f"Client ID : {client_id}")
    
    # 1. Tentative Flux 2026 (Client Credentials)
    url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    
    print("\n[Test 1] Tentative Client Credentials (Flux 2026)...")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✅ SUCCÈS ! Jeton récupéré : {token[:10]}...")
            return token
        else:
            print(f"❌ ÉCHEC (Code {response.status_code})")
            print(f"Réponse : {response.text}")
    except Exception as e:
        print(f"❌ Erreur : {str(e)}")

    print("\n[Conclusion] Le flux automatique est bloqué par Shopify.")
    print("Veuillez vérifier que 'Use legacy install flow' est sur TRUE dans le Dev Dashboard.")
    return None

if __name__ == "__main__":
    debug_shopify_auth()
