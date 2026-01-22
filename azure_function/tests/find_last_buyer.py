import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import shopify
import os
from dotenv import load_dotenv
from core.shopify_helper import ShopifyHelper

load_dotenv()

def find_last_louis_buyer():
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    collection_id = os.getenv("TARGET_COLLECTION_ID")

    helper = ShopifyHelper(store_url, access_token=access_token)
    
    print(f"--- Recherche du dernier acheteur 'Louis' ({collection_id}) ---")
    
    # 1. Récupérer les IDs des produits Louis
    louis_pids = helper.get_collection_products(collection_id)
    print(f"DEBUG: {len(louis_pids)} produits dans la collection.")

    # 2. Chercher les dernières commandes
    # On cherche les 50 dernières commandes pour trouver un match
    orders = shopify.Order.find(limit=50, status='any')
    
    found = False
    for order in orders:
        has_louis = any(item.product_id in louis_pids for item in order.line_items)
        if has_louis and order.customer:
            print(f"\n✅ TROUVÉ ! Commande {order.name} du {order.created_at}")
            print(f"Client: {order.customer.first_name} {order.customer.last_name} ({order.customer.email})")
            print(f"ID Client: {order.customer.id}")
            
            # Simulation recommandation
            history = helper.get_customer_purchase_history(order.customer.id)
            recos = [pid for pid in louis_pids if pid not in history][:3]
            print(f"Recommandations suggérées: {recos}")
            found = True
            break
            
    if not found:
        print("\n❌ Aucun acheteur Louis trouvé dans les 50 dernières commandes.")

if __name__ == "__main__":
    find_last_louis_buyer()
