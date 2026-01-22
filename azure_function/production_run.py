import os
import logging
from shopify_helper import ShopifyHelper
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def production_run():
    # Configurer le logging pour la console
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    store_url = os.environ.get("SHOPIFY_STORE_URL")
    access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    client_id = os.environ.get("SHOPIFY_CLIENT_ID")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")
    collection_id = os.environ.get("TARGET_COLLECTION_ID")
    
    # Plage 12-18 mois
    delay_start = int(os.environ.get("ORDER_DELAY_DAYS_START", 365))
    delay_end = int(os.environ.get("ORDER_DELAY_DAYS_END", 548))

    if not all([store_url, collection_id, access_token]):
        print("Erreur : Variables d'environnement manquantes dans .env")
        return

    helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)

    print(f"\n{'='*60}")
    print(f"LANCEMENT DU SCANNER RÉEL : {store_url}")
    print(f"Période cible : J-{delay_start} à J-{delay_end} (12-18 mois)")
    print(f"Collection cible : {collection_id}")
    print(f"{'='*60}\n")

    # 1. Récupérer les produits de la collection
    collection_product_ids = helper.get_collection_products(collection_id)
    print(f"INFO: {len(collection_product_ids)} produits dans la collection Louis.")

    # 2. Trouver les clients
    customers = helper.get_eligible_customers(days_start=delay_start, days_end=delay_end, collection_id=collection_id)
    print(f"INFO: {len(customers)} clients éligibles trouvés sur cette période.")

    # 3. Traiter chaque client
    count = 0
    for customer in customers:
        print(f"\nTraitement de {customer.first_name} {customer.last_name} ({customer.id})...")
        
        history = helper.get_customer_purchase_history(customer.id)
        
        # On retire les produits déjà achetés
        top_recos = [pid for pid in collection_product_ids if pid not in history][:3]
        
        if top_recos:
            if helper.update_customer_recommendations(customer.id, top_recos):
                count += 1
        else:
            print(f"  -> Déjà possesseur de toute la collection.")

    print(f"\n{'='*60}")
    print(f"TERMINÉ : {count} client(s) mis à jour avec succès.")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    production_run()
