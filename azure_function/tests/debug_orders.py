import shopify
import os
from dotenv import load_dotenv

load_dotenv()

def debug_orders():
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")

    session = shopify.Session(store_url, '2025-01', access_token)
    shopify.ShopifyResource.activate_session(session)
    
    print(f"Test de récupération simple sur {store_url}...")
    try:
        # Test 1 : Sans aucun paramètre
        orders = shopify.Order.find(limit=1)
        print(f"Test 1 (Sans param) : Succès ! {len(orders)} commande trouvée.")
        
        # Test 2 : Avec status='any'
        orders = shopify.Order.find(limit=1, status='any')
        print(f"Test 2 (status='any') : Succès !")
        
    except Exception as e:
        print(f"ERREUR : {e}")
        if hasattr(e, 'response'):
            print(f"Détails réponse : {e.response.body}")

if __name__ == "__main__":
    debug_orders()
