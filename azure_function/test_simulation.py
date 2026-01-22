from shopify_helper import ShopifyHelper
import os
from dotenv import load_dotenv

load_dotenv()

def test_simulation():
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    client_id = os.getenv("SHOPIFY_CLIENT_ID")
    client_secret = os.getenv("SHOPIFY_CLIENT_SECRET")
    collection_id = os.getenv("TARGET_COLLECTION_ID")

    if not all([store_url, collection_id]) or not (access_token or (client_id and client_secret)):
        print("Erreur: Variables .env manquantes (token ou duo ID/Secret requis).")
        return

    helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)

    print(f"--- Simulation Scanner pour {store_url} ---")
    
    # 1. Test récupération collection
    try:
        pids = helper.get_collection_products(collection_id)
        print(f"DEBUG: {len(pids)} produits trouvés dans la collection {collection_id}")
    except Exception as e:
        print(f"Erreur API (Collection): {e}")
        return

    # 2. Test recherche clients (30 derniers jours pour validation technique)
    days_start = 0
    days_end = 30
    try:
        customers = helper.get_eligible_customers(days_start=days_start, days_end=days_end, collection_id=None)
        print(f"DEBUG: {len(customers)} clients trouvés pour la période J-{days_start} à J-{days_end} (SANS filtre collection)")
        
        for customer in customers:
            print(f"Traitement client {customer.id} ({customer.email})")
            history = helper.get_customer_purchase_history(customer.id)
            recos = [pid for pid in pids if pid not in history][:3]
            print(f"  -> Recommandations calculées: {recos}")
            
    except Exception as e:
        print(f"Erreur API (Clients): {e}")

if __name__ == "__main__":
    test_simulation()
