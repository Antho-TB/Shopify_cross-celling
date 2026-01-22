from shopify_helper import ShopifyHelper
import os
from dotenv import load_dotenv

load_dotenv()

def test_recent_forges():
    """Test pour trouver les clients ayant acheté Forgés récemment"""
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    client_id = os.getenv("SHOPIFY_CLIENT_ID")
    client_secret = os.getenv("SHOPIFY_CLIENT_SECRET")
    collection_id = "298781474968"  # Forgés

    helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)

    print("--- Recherche: Clients Forgés (30 derniers jours) ---\n")
    
    # Récupérer les produits
    try:
        product_ids = helper.get_collection_products(collection_id)
        print(f"✓ {len(product_ids)} produits dans la collection Forgés\n")
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return

    # Chercher les clients sur 30 jours
    try:
        customers = helper.get_eligible_customers(
            days_start=0,
            days_end=30, 
            collection_id=collection_id
        )
        print(f"✓ {len(customers)} clients trouvés (30 jours)\n")
        
        if customers:
            print("=" * 80)
            print(f"{'#':<4} {'Email':<40} {'Nom':<30} {'Produits achetes':<15}")
            print("=" * 80)
            
            for i, c in enumerate(customers, 1):
                history = helper.get_customer_purchase_history(c.id)
                bought = len([p for p in history if p in product_ids])
                name = f"{c.first_name or ''} {c.last_name or ''}".strip()
                print(f"{i:<4} {c.email:<40} {name:<30} {bought:<15}")
            
            print("=" * 80)
        else:
            print("ℹ Aucun client trouvé dans cette période.")
            
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_recent_forges()
