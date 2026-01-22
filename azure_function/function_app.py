import azure.functions as func
import logging
import os
from datetime import datetime
from shopify_helper import ShopifyHelper

app = func.FunctionApp()

@app.schedule(schedule="0 0 2 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def daily_cross_sell_scanner(myTimer: func.TimerRequest) -> None:
    logging.info('Démarrage du scanner quotidien de cross-selling.')

    # Configuration
    store_url = os.environ.get("SHOPIFY_STORE_URL")
    access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    client_id = os.environ.get("SHOPIFY_CLIENT_ID")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")
    collection_id = os.environ.get("TARGET_COLLECTION_ID")
    delay_start = int(os.environ.get("ORDER_DELAY_DAYS_START", 365))
    delay_end = int(os.environ.get("ORDER_DELAY_DAYS_END", 548))

    if not all([store_url, collection_id]) or not (access_token or (client_id and client_secret)):
        logging.error("Variables d'environnement manquantes (il faut soit le token, soit le duo ID/Secret).")
        return

    helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)

    # 1. Récupérer les produits de la collection cible (ex: Louis)
    collection_product_ids = helper.get_collection_products(collection_id)
    logging.info(f"Produits dans la collection cible: {len(collection_product_ids)}")

    # 2. Trouver les clients ayant commandé dans la plage cible et ayant acheté un produit de la collection
    customers = helper.get_eligible_customers(days_start=delay_start, days_end=delay_end, collection_id=collection_id)
    logging.info(f"Nombre de clients éligibles (J-{delay_start} à J-{delay_end}): {len(customers)}")

    for customer in customers:
        # 3. Calculer les produits à recommander
        history = helper.get_customer_purchase_history(customer.id)
        
        # On retire les produits déjà achetés
        remaining_products = [pid for pid in collection_product_ids if pid not in history]
        
        if remaining_products:
            # On en prend 3 max
            top_recos = remaining_products[:3]
            
            # 4. Injecter dans Shopify
            helper.update_customer_recommendations(customer.id, top_recos)
            logging.info(f"Recommandations envoyées pour le client {customer.id}: {top_recos}")
        else:
            logging.info(f"Client {customer.id} possède déjà toute la collection.")

    logging.info('Scanner terminé.')
