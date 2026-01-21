from shopify_helper import ShopifyHelper
import os
from dotenv import load_dotenv

load_dotenv()

def test_simulation():
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    collection_id = os.getenv("TARGET_COLLECTION_ID")

    if not all([store_url, access_token, collection_id]):
        print("Erreur: Variables .env manquantes.")
        return

    helper = ShopifyHelper(store_url, access_token)

    print(f"--- Simulation Scanner pour {store_url} ---")
    
    # 1. Test récupération collection
    try:
        pids = helper.get_collection_products(collection_id)
        print(f"DEBUG: {len(pids)} produits trouvés dans la collection {collection_id}")
    except Exception as e:
        print(f"Erreur API (Collection): {e}")
        return

    # 2. Test recherche clients
    try:
        customers = helper.get_eligible_customers(days_ago=180)
        print(f"DEBUG: {len(customers)} clients trouvés pour J-180")
        
        for customer in customers:
            print(f"Traitement client {customer.id} ({customer.email})")
            history = helper.get_customer_purchase_history(customer.id)
            recos = [pid for pid in pids if pid not in history][:3]
            print(f"  -> Recommandations calculées: {recos}")
            
    except Exception as e:
        print(f"Erreur API (Clients): {e}")

if __name__ == "__main__":
    test_simulation()
