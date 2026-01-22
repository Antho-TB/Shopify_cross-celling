import azure.functions as func
import logging
import json
import os
from datetime import datetime
from shopify_helper import ShopifyHelper

app = func.FunctionApp()

# Configuration du logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@app.schedule(schedule="0 0 2 * * 1", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def weekly_cross_sell_scanner(myTimer: func.TimerRequest) -> None:
    """
    Scan hebdomadaire (2h du matin, chaque lundi) pour identifier les clients 
    ayant acheté un produit il y a 6 mois jour pour jour ±7 jours
    et injecter les recommandations pour TOUTES les collections.
    
    Fenêtre: 173-180 jours (6 mois - 7 jours à 6 mois pile)
    Fréquence: 1x par semaine (lundi à 2h)
    Mode: PRODUCTION (toutes les collections)
    """
    logger.info('=== Démarrage du scanner hebdomadaire (6 mois ±7 jours) - TOUTES COLLECTIONS ===')

    try:
        # Configuration
        store_url = os.environ.get("SHOPIFY_STORE_URL")
        access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
        client_id = os.environ.get("SHOPIFY_CLIENT_ID")
        client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")
        # Fenêtre 6 mois ±7 jours: 173-180 jours
        delay_start = int(os.environ.get("ORDER_DELAY_DAYS_START", 173))
        delay_end = int(os.environ.get("ORDER_DELAY_DAYS_END", 180))

        if not all([store_url]) or not (access_token or (client_id and client_secret)):
            logger.error("Variables d'environnement manquantes (SHOPIFY_STORE_URL + token requis).")
            return

        logger.info(f"Configuration: Fenêtre={delay_start}-{delay_end} jours (6 mois ±7j)")

        # Initialisation du helper
        helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)

        # 1. Récupérer TOUTES les collections
        logger.info("Récupération de toutes les collections...")
        all_collections = {
            '298781474968': 'Forgés',
            '299133665432': 'Louis',
            '299133730968': 'Brigade forgé premium®',
            '303575662744': 'Forgé Premium Evercut®'
        }
        
        logger.info(f"Collections à scanner: {len(all_collections)}")
        
        total_customers_updated = 0
        
        # 2. Pour CHAQUE collection
        for collection_id, collection_name in all_collections.items():
            logger.info(f"\n--- Traitement collection: {collection_name} ({collection_id}) ---")
            
            try:
                # Récupérer les produits de la collection
                collection_product_ids = helper.get_collection_products(collection_id)
                logger.info(f"Produits: {len(collection_product_ids)}")
                
                if not collection_product_ids:
                    logger.warning(f"Aucun produit trouvé dans {collection_name}")
                    continue
                
                # Trouver les clients ayant commandé dans la plage cible
                customers = helper.get_eligible_customers(
                    days_start=delay_start, 
                    days_end=delay_end, 
                    collection_id=collection_id
                )
                logger.info(f"Clients éligibles: {len(customers)}")
                
                # Pour chaque client, calculer et injecter les recommandations
                collection_updated_count = 0
                for customer in customers:
                    try:
                        history = helper.get_customer_purchase_history(customer.id)
                        
                        # Produits non encore achetés
                        remaining_products = [pid for pid in collection_product_ids if pid not in history]
                        
                        if remaining_products:
                            top_recos = remaining_products[:3]
                            
                            # Injection dans Shopify
                            if helper.update_customer_recommendations(customer.id, top_recos):
                                collection_updated_count += 1
                                logger.debug(f"✓ {customer.email}: {len(top_recos)} recommandations")
                        else:
                            logger.debug(f"- {customer.email}: aucune recommandation (tous les produits achetés)")
                            
                    except Exception as e:
                        logger.error(f"Erreur pour client {customer.id}: {str(e)}")
                        continue
                
                logger.info(f"Collection {collection_name}: {collection_updated_count}/{len(customers)} clients mis à jour")
                total_customers_updated += collection_updated_count
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement de {collection_name}: {str(e)}")
                continue

        logger.info(f"=== Scan hebdomadaire terminé: {total_customers_updated} clients mis à jour au total ===")

    except Exception as e:
        logger.error(f"Erreur générale dans weekly_cross_sell_scanner: {str(e)}")


@app.route(route="check_recommendations", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def http_check_recommendations(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP Trigger pour tester les recommandations pour un client spécifique.
    
    POST /api/check_recommendations
    Body JSON: {
        "customer_id": "123456789",
        "collection_id": "298781474968"
    }
    """
    logger.info("=== Requête HTTP: check_recommendations ===")
    
    try:
        req_body = req.get_json()
        customer_id = req_body.get("customer_id")
        collection_id = req_body.get("collection_id")

        if not customer_id or not collection_id:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": "Paramètres manquants: customer_id et collection_id requis"
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Configuration
        store_url = os.environ.get("SHOPIFY_STORE_URL")
        access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
        client_id = os.environ.get("SHOPIFY_CLIENT_ID")
        client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")

        if not store_url or not (access_token or (client_id and client_secret)):
            logger.error("Variables d'environnement manquantes")
            return func.HttpResponse(
                json.dumps({"success": False, "error": "Serveur mal configuré"}),
                status_code=500,
                mimetype="application/json"
            )

        helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)

        # Récupérer les produits de la collection
        collection_products = helper.get_collection_products(collection_id)
        
        # Récupérer l'historique d'achat du client
        customer_history = helper.get_customer_purchase_history(customer_id)
        
        # Recommandations = produits non achetés
        recommendations = [pid for pid in collection_products if pid not in customer_history][:3]

        logger.info(f"Client {customer_id}: {len(recommendations)} recommandations trouvées")

        return func.HttpResponse(
            json.dumps({
                "success": True,
                "customer_id": customer_id,
                "collection_id": collection_id,
                "collection_products_count": len(collection_products),
                "customer_history_count": len(customer_history),
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Erreur dans check_recommendations: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
