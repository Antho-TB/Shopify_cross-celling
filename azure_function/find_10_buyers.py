import shopify
import os
from dotenv import load_dotenv
from shopify_helper import ShopifyHelper

load_dotenv()

def find_last_10_louis_buyers():
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    collection_id = os.getenv("TARGET_COLLECTION_ID")

    # Initialisation session
    session = shopify.Session(store_url, '2025-01', access_token)
    shopify.ShopifyResource.activate_session(session)
    
    helper = ShopifyHelper(store_url, access_token=access_token)
    
    print(f"--- Recherche des 10 derniers acheteurs 'Louis' ({collection_id}) ---")
    
    # 1. Récupérer les IDs des produits Louis
    louis_pids = helper.get_collection_products(collection_id)
    print(f"DEBUG: {len(louis_pids)} produits dans la collection.")

    # 2. Parcourir les commandes avec la pagination native
    found_customers = []
    seen_customer_ids = set()
    
    print("Analyse des commandes par blocs de 50...")
    
    orders = shopify.Order.find(limit=50, status='any')
    
    while orders:
        for order in orders:
            # Vérifier si la commande contient un produit Louis
            has_louis = any(item.product_id in louis_pids for item in order.line_items)
            
            if has_louis and order.customer:
                cid = order.customer.id
                if cid not in seen_customer_ids:
                    seen_customer_ids.add(cid)
                    found_customers.append({
                        'name': f"{order.customer.first_name} {order.customer.last_name}",
                        'email': order.customer.email,
                        'date': order.created_at,
                        'order_name': order.name
                    })
                    
                if len(found_customers) >= 10:
                    break
        
        if len(found_customers) >= 10:
            break
            
        if orders.has_next_page():
            print(f"Chargement de la page suivante... ({len(found_customers)} clients trouvés)")
            orders = orders.next_page()
        else:
            break
            
    print("\n" + "="*80)
    print(f"{'NOM':<25} | {'EMAIL':<35} | {'DATE':<20}")
    print("-" * 80)
    
    for c in found_customers:
        clean_date = c['date'].split('T')[0]
        print(f"{c['name']:<25} | {c['email']:<35} | {clean_date:<20}")
    
    print("="*80)
    if len(found_customers) < 10:
        print(f"Note: Seulement {len(found_customers)} acheteurs distincts trouvés.")

if __name__ == "__main__":
    find_last_10_louis_buyers()
