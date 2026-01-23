import sys
import os
import logging
from dotenv import load_dotenv

# Ajouter le chemin vers core pour l'import de shopify_helper
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from shopify_helper import ShopifyHelper
import shopify

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_sandbox_injection():
    """
    Script de test pour injecter des recommandations RÉELLES sur l'email de test.
    """
    logger.info("=== DÉMARRAGE INJECTION SANDBOX (TEST EMAIL UNIQUEMENT) ===")
    
    store_url = os.environ.get("SHOPIFY_STORE_URL")
    access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    client_id = os.environ.get("SHOPIFY_CLIENT_ID")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")
    test_email = os.environ.get("TEST_EMAIL")

    if not test_email:
        logger.error("Variable TEST_EMAIL manquante dans le .env")
        return

    helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)

    # 1. Chercher le client par email
    logger.info(f"Recherche du client : {test_email}...")
    customers = shopify.Customer.search(query=f"email:{test_email}")
    
    if not customers:
        logger.error(f"Client non trouvé avec l'email : {test_email}")
        logger.info("Veuillez créer un compte client sur la boutique avec cet email pour tester.")
        return

    customer = customers[0]
    logger.info(f"Client trouvé : {customer.first_name} {customer.last_name} (ID: {customer.id})")

    # 2. Choisir une collection pour le test (ex: Forgé Premium Evercut®)
    collection_id = "303575662744"
    logger.info(f"Génération de recommandations pour la collection {collection_id}...")
    
    collection_product_ids = helper.get_collection_products(collection_id)
    history = helper.get_customer_purchase_history(customer.id)
    
    remaining_products = [pid for pid in collection_product_ids if pid not in history]
    
    if not remaining_products:
        logger.warning("Le client possède déjà tous les produits de cette collection.")
        # On force 3 produits pour le test si besoin, ou on change de collection
        recos = collection_product_ids[:3]
        logger.info(f"Mode TEST : On force quand même {len(recos)} recommandations.")
    else:
        recos = remaining_products[:3]
        logger.info(f"Trouvé {len(recos)} produits non possédés.")

    # 3. Injection réelle
    logger.info(f"Injection des recommandations : {recos}")
    if helper.update_customer_recommendations(customer.id, recos):
        logger.info("✅ SUCCESS : Metafield injecté et Tag 'trigger_reco' ajouté.")
        logger.info(f"Vérifiez la fiche client {test_email} sur Shopify et attendez le déclenchement du Flow.")
    else:
        logger.error("❌ ÉCHEC de l'injection.")

if __name__ == "__main__":
    run_sandbox_injection()
