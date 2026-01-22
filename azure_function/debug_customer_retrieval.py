import shopify
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def debug_customer_retrieval():
    """Debug le processus de récupération des clients"""
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    client_id = os.getenv("SHOPIFY_CLIENT_ID")
    client_secret = os.getenv("SHOPIFY_CLIENT_SECRET")
    collection_id = "298781474968"  # Forgés

    if not access_token and client_id and client_secret:
        import requests
        url = f"https://{store_url}/admin/oauth/access_token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            access_token = response.json().get("access_token")

    session = shopify.Session(store_url, '2025-01', access_token)
    shopify.ShopifyResource.activate_session(session)

    print("=" * 90)
    print("DIAGNOSTIC: Récupération des clients par collection")
    print("=" * 90)
    
    # Paramètres
    days_start = 0
    days_end = 30
    
    date_start = (datetime.now() - timedelta(days=days_end)).strftime('%Y-%m-%d')
    date_end = (datetime.now() - timedelta(days=days_start)).strftime('%Y-%m-%d')
    
    print(f"\nPériode: {date_start} à {date_end}")
    print(f"Collection ID: {collection_id}\n")
    
    # Étape 1: Récupérer les produits de la collection
    print("ÉTAPE 1: Récupérer les produits de la collection")
    print("-" * 90)
    try:
        products = shopify.Product.find(collection_id=collection_id)
        product_ids = [p.id for p in products]
        print(f"✓ Trouvé: {len(product_ids)} produits")
        for i, pid in enumerate(product_ids, 1):
            print(f"  {i}. Product ID: {pid}")
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return

    # Étape 2: Récupérer TOUTES les commandes dans la période
    print(f"\nÉTAPE 2: Récupérer TOUTES les commandes ({date_start} à {date_end})")
    print("-" * 90)
    try:
        all_orders = shopify.Order.find(
            created_at_min=f"{date_start}T00:00:00Z",
            created_at_max=f"{date_end}T23:59:59Z",
            status='any',
            limit=250
        )
        print(f"✓ Trouvé: {len(all_orders)} commandes totales\n")
        
        print(f"{'#':<3} {'Order':<15} {'Date':<12} {'Client':<30} {'Items':<6} {'De la collection?':<18}")
        print("-" * 90)
        
        # Étape 3: Filtrer les commandes pour trouver celles de la collection
        collection_orders = []
        collection_customers = {}
        
        for i, order in enumerate(all_orders, 1):
            has_collection_item = False
            items_list = []
            
            if order.line_items:
                for item in order.line_items:
                    items_list.append(item.product_id)
                    if item.product_id in product_ids:
                        has_collection_item = True
            
            if order.customer:
                customer_name = f"{order.customer.first_name or ''} {order.customer.last_name or ''}".strip()[:25]
            else:
                customer_name = "Anonyme"
            
            date = order.created_at[:10] if order.created_at else "N/A"
            status = "OUI" if has_collection_item else "NON"
            
            print(f"{i:<3} {order.name:<15} {date:<12} {customer_name:<30} {len(items_list):<6} {status:<18}")
            
            if has_collection_item:
                collection_orders.append(order)
                if order.customer and order.customer.id not in collection_customers:
                    collection_customers[order.customer.id] = order.customer
        
        print("-" * 90)
        print(f"\n✓ Commandes de la collection: {len(collection_orders)} / {len(all_orders)}")
        print(f"✓ Clients uniques de la collection: {len(collection_customers)}")
        
        # Étape 4: Afficher les clients trouvés
        print(f"\nÉTAPE 3: Détail des clients de la collection")
        print("-" * 90)
        
        for i, (customer_id, customer) in enumerate(collection_customers.items(), 1):
            # Récupérer l'historique d'achat du client
            customer_orders = shopify.Order.find(customer_id=customer_id, status='any')
            all_bought_ids = set()
            for order in customer_orders:
                for item in order.line_items:
                    all_bought_ids.add(item.product_id)
            
            # Recommandations
            recommendations = [pid for pid in product_ids if pid not in all_bought_ids][:3]
            
            print(f"\n{i}. {customer.email}")
            print(f"   Nom: {customer.first_name or ''} {customer.last_name or ''}")
            print(f"   Total de produits achetés: {len(all_bought_ids)}")
            print(f"   Produits de Forgés achetés: {len([p for p in all_bought_ids if p in product_ids])}")
            print(f"   Recommandations disponibles: {len(recommendations)}")
            if recommendations:
                print(f"   IDs recommandés: {recommendations}")
    
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_customer_retrieval()
