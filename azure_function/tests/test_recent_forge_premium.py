import sys
import os
import logging
from datetime import datetime, timedelta

# Ajouter le chemin vers core pour l'import de shopify_helper
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from shopify_helper import ShopifyHelper
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_recent_forge_premium_test():
    """
    Script de test pour identifier les clients "Forgé Premium" des 60 derniers jours.
    """
    logger.info("=== DÉMARRAGE TEST RÉCENT FORGÉ PREMIUM (60 DERNIERS JOURS) ===")
    
    store_url = os.environ.get("SHOPIFY_STORE_URL")
    access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    client_id = os.environ.get("SHOPIFY_CLIENT_ID")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")

    if not store_url or not (access_token or (client_id and client_secret)):
        logger.error("Configuration Shopify manquante dans le .env")
        return

    helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)

    # Collections Forgé Premium
    target_collections = {
        '299133730968': 'Brigade forgé premium®',
        '303575662744': 'Forgé Premium Evercut®'
    }

    # Fenêtre autorisée : 60 jours
    delay_start = 0
    delay_end = 60

    logger.info(f"Recherche entre J-0 et J-60")

    all_eligible_customers = {}

    for coll_id, coll_name in target_collections.items():
        logger.info(f"\n--- Analyse Collection: {coll_name} ({coll_id}) ---")
        collection_product_ids = helper.get_collection_products(coll_id)
        
        customers = helper.get_eligible_customers(
            days_start=delay_start,
            days_end=delay_end,
            collection_id=coll_id
        )
        
        for customer in customers:
            if customer.id not in all_eligible_customers:
                all_eligible_customers[customer.id] = {
                    'email': customer.email,
                    'count': 1,
                    'collections': [coll_name]
                }
            else:
                all_eligible_customers[customer.id]['count'] += 1
                all_eligible_customers[customer.id]['collections'].append(coll_name)

    logger.info(f"\n=== RÉSULTATS: {len(all_eligible_customers)} clients trouvés (60 derniers jours) ===")
    for cid, data in all_eligible_customers.items():
        logger.info(f"{data['email']} | Collections: {', '.join(data['collections'])}")

if __name__ == "__main__":
    run_recent_forge_premium_test()
