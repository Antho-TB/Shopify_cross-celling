import sys
import os
import logging
from datetime import datetime

# Ajouter le chemin vers core pour l'import de shopify_helper
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from shopify_helper import ShopifyHelper
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_forge_premium_test():
    """
    Script de test pour identifier les clients "Forgé Premium" d'il y a 6-12 mois.
    """
    logger.info("=== DÉMARRAGE TEST CAMPAGNE FORGÉ PREMIUM (6-12 MOIS) ===")
    
    store_url = os.environ.get("SHOPIFY_STORE_URL")
    access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    client_id = os.environ.get("SHOPIFY_CLIENT_ID")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")

    if not store_url or not (access_token or (client_id and client_secret)):
        logger.error("Configuration Shopify manquante dans le .env")
        return

    # Initialisation
    helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)

    # Collections Forgé Premium
    # 299133730968: Brigade forgé premium®
    # 303575662744: Forgé Premium Evercut®
    target_collections = {
        '299133730968': 'Brigade forgé premium®',
        '303575662744': 'Forgé Premium Evercut®'
    }

    # Période de test: Janvier à Juin 2025 (environ 6-12 mois ago)
    date_start = "2025-01-22T00:00:00Z"
    date_end = "2025-07-22T23:59:59Z"

    logger.info(f"Recherche entre {date_start} et {date_end}")

    all_eligible_customers = {}

    for coll_id, coll_name in target_collections.items():
        logger.info(f"\n--- Analyse Collection: {coll_name} ({coll_id}) ---")
        
        # Récupérer les produits de la collection
        collection_product_ids = helper.get_collection_products(coll_id)
        logger.info(f"Produits dans la collection: {len(collection_product_ids)}")

        # Récupérer les clients éligibles (on surcharge le helper pour être sûr des dates ici)
        logger.info(f"Recherche directe des commandes pour {coll_name}...")
        
        import shopify
        orders = shopify.Order.find(
            created_at_min=date_start,
            created_at_max=date_end,
            status='any',
            limit=250
        )
        
        logger.info(f"Traitement de {len(orders)} commandes trouvées dans cette plage")
        
        target_product_ids = set(collection_product_ids)
        for o in orders:
            if not o.customer or o.customer.id in all_eligible_customers:
                continue
                
            has_target_product = any(item.product_id in target_product_ids for item in o.line_items)
            if has_target_product:
                all_eligible_customers[o.customer.id] = {
                    'email': o.customer.email,
                    'first_name': o.customer.first_name,
                    'last_name': o.customer.last_name,
                    'collections': [coll_name]
                }

    logger.info(f"\n=== RÉSULTATS: {len(all_eligible_customers)} clients uniques trouvés ===")
    
    for cid, data in all_eligible_customers.items():
        logger.info(f"ID: {cid} | {data['email']} | {data['first_name']} {data['last_name']} | Collections: {', '.join(data['collections'])}")

if __name__ == "__main__":
    run_forge_premium_test()
