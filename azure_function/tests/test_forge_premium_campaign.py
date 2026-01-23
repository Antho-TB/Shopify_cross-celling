import os
import shopify
from dotenv import load_dotenv
from shopify_helper import ShopifyHelper
from datetime import datetime

load_dotenv()

def run_forge_premium_test():
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    
    # ID Collection "Forgé Premium" (Brigade forgé premium®)
    collection_id = "299133730968"
    
    # Plage 6-12 mois (180 à 365 jours)
    delay_start = 180
    delay_end = 365

    print(f"\n--- Test Campagne Forgé Premium (6-12 mois) ---")
    print(f"Boutique : {store_url}")
    print(f"Collection : {collection_id}")
    
    helper = ShopifyHelper(store_url, access_token=access_token)
    
    # 1. Récupérer les produits de la collection
    pids = helper.get_collection_products(collection_id)
    print(f"DEBUG: {len(pids)} produits trouvés dans la collection Forgé Premium.")

    # 2. Chercher les clients éligibles
    try:
        customers = helper.get_eligible_customers(days_start=delay_start, days_end=delay_end, collection_id=collection_id)
        print(f"DEBUG: {len(customers)} clients trouvés pour la période J-{delay_start} à J-{delay_end} (ayant acheté Forgé Premium)")
        
        for customer in customers:
            print(f"\nClient: {customer.first_name} {customer.last_name} ({customer.email})")
            history = helper.get_customer_purchase_history(customer.id)
            recos = [pid for pid in pids if pid not in history][:3]
            print(f"  -> Recommandations calculées: {recos}")
            
            # Pour le test, on n'injecte pas réellement sauf si demandé
            # success = helper.update_customer_recommendations(customer.id, recos)
            # if success: print("  -> Injection simulée réussie")
            
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    run_forge_premium_test()
