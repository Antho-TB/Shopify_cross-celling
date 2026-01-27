import azure.functions as func
import logging
import json
import os
import io
from datetime import datetime
from shopify_helper import ShopifyHelper
from report_manager import ReportManager

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
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "weekly_scan",
        "status": "started",
        "collections": [],
        "total_updated": 0,
        "errors": []
    }
    report_manager = ReportManager()

    # Capture des logs en mémoire
    log_stream = io.StringIO()
    log_handler = logging.StreamHandler(log_stream)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_handler)

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
                
                # Calculer l'URL de la collection une seule fois pour cette boucle
                collection_url = helper.get_collection_url(collection_id)
                logger.info(f"URL de la collection: {collection_url}")
                
                # Trouver les clients ayant commandé dans la plage cible
                eligible_entries = helper.get_eligible_customers(
                    days_start=delay_start, 
                    days_end=delay_end, 
                    collection_id=collection_id
                )
                logger.info(f"Clients éligibles: {len(eligible_entries)}")
                
                # Pour chaque client, calculer et injecter les recommandations
                collection_updated_count = 0
                for entry in eligible_entries:
                    customer = entry["customer"]
                    try:
                        history = helper.get_customer_purchase_history(customer.id)
                        
                        # Produits non encore achetés
                        remaining_products = list(collection_product_ids.keys())
                        remaining_products = [pid for pid in remaining_products if pid not in history]
                        
                        if remaining_products:
                            top_recos = remaining_products[:3]
                            
                            # Préparation des data riches (images, prix, etc.)
                            reco_data = [collection_product_ids[pid] for pid in top_recos]
                            reco_names = [d["title"] for d in reco_data]
                            
                            # Injection dans Shopify (Metafields + Tag)
                            if helper.update_customer_recommendations(customer.id, top_recos, manual_names=reco_names, manual_data=reco_data, collection_url=collection_url):
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
        
        report["status"] = "success"
        report["total_updated"] = total_customers_updated
        
        # Récupération des logs capturés
        log_handler.flush()
        report["raw_logs"] = log_stream.getvalue()
        logger.removeHandler(log_handler)
        
        report_manager.save_report(report)

    except Exception as e:
        logger.error(f"Erreur générale dans weekly_cross_sell_scanner: {str(e)}")
        report["status"] = "error"
        report["errors"].append(str(e))
        
        # Récupération des logs même en cas d'erreur
        log_handler.flush()
        report["raw_logs"] = log_stream.getvalue()
        logger.removeHandler(log_handler)
        
        report_manager.save_report(report)


@app.route(route="dry_run", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def http_dry_run(req: func.HttpRequest) -> func.HttpResponse:
    """
    Exécute une simulation complète (Dry Run) du scanner hebdomadaire.
    RETOURNE les résultats sans modifier Shopify.
    """
    logger.info('=== Démarrage d\'une SIMULATION (Dry Run) ===')
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_eligible": 0,
        "simulated_updates": []
    }

    try:
        # Configuration
        store_url = os.environ.get("SHOPIFY_STORE_URL")
        access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
        client_id = os.environ.get("SHOPIFY_CLIENT_ID")
        client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")
        delay_start = int(os.environ.get("ORDER_DELAY_DAYS_START", 173))
        delay_end = int(os.environ.get("ORDER_DELAY_DAYS_END", 180))

        if not store_url:
            return func.HttpResponse(json.dumps({"error": "Config manquante"}), status_code=500)

        helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)

        all_collections = {
            '298781474968': 'Forgés',
            '299133665432': 'Louis',
            '299133730968': 'Brigade forgé premium®',
            '303575662744': 'Forgé Premium Evercut®'
        }
        
        for collection_id, collection_name in all_collections.items():
            collection_product_data = helper.get_collection_products(collection_id)
            if not collection_product_data: continue
            
            eligible_entries = helper.get_eligible_customers(days_start=delay_start, days_end=delay_end, collection_id=collection_id)
            
            for entry in eligible_entries:
                customer = entry["customer"]
                history = helper.get_customer_purchase_history(customer.id)
                
                collection_product_ids = list(collection_product_data.keys())
                remaining_products = [pid for pid in collection_product_ids if pid not in history]
                
                if remaining_products:
                    # Traduction des IDs en noms pour le Dry Run
                    reco_names = [collection_product_data[pid] for pid in remaining_products[:3]]
                    
                    results["simulated_updates"].append({
                        "email": customer.email,
                        "collection": collection_name,
                        "purchase_date": entry["purchase_date"],
                        "purchased_product": entry["purchased_product"],
                        "recommendations": reco_names
                    })
        
        results["total_eligible"] = len(results["simulated_updates"])
        return func.HttpResponse(json.dumps(results), mimetype="application/json")

    except Exception as e:
        logger.error(f"Erreur Dry Run: {str(e)}")
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500, mimetype="application/json")


@app.route(route="trigger_test", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def http_trigger_test(req: func.HttpRequest) -> func.HttpResponse:
    """
    Recherche un client par email et déclenche une mise à jour réelle
    pour tester le Shopify Flow de bout en bout.
    """
    logger.info('=== Déclenchement d\'un TEST de bout en bout ===')
    email = "a.bezille@tb-groupe.fr" # Email cible par défaut
    
    try:
        # Configuration
        store_url = os.environ.get("SHOPIFY_STORE_URL")
        access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
        client_id = os.environ.get("SHOPIFY_CLIENT_ID")
        client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")

        helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)
        
        # 1. Recherche du client par email
        import shopify
        customers = shopify.Customer.search(query=f"email:{email}")
        if not customers:
            return func.HttpResponse(json.dumps({"success": False, "error": f"Client {email} non trouvé dans Shopify"}), status_code=404)
        
        customer = customers[0]
        logger.info(f"Client trouvé: {customer.id} ({customer.email})")

        # 2. Calcul recommandation (Collection Louis par défaut)
        collection_id = "299133665432"
        collection_product_data = helper.get_collection_products(collection_id)
        collection_product_ids = list(collection_product_data.keys())
        
        history = helper.get_customer_purchase_history(customer.id)
        recommendations = [pid for pid in collection_product_ids if pid not in history][:3]

        if not recommendations:
            return func.HttpResponse(json.dumps({"success": False, "error": "Aucune recommandation possible (déjà tout acheté)"}), status_code=400)

        # 3. Mise à jour réelle (Metafield + Tag)
        reco_data = [collection_product_data[pid] for pid in recommendations]
        reco_names = [d["title"] for d in reco_data]
        collection_url = helper.get_collection_url(collection_id)
        logger.info(f"Déclenchement test avec: {reco_names} | Collection URL: {collection_url}")
        
        if helper.update_customer_recommendations(customer.id, recommendations, manual_names=reco_names, manual_data=reco_data, collection_url=collection_url):
            return func.HttpResponse(json.dumps({
                "success": True, 
                "customer_id": customer.id,
                "recommendations": reco_names
            }), mimetype="application/json")
        else:
            return func.HttpResponse(json.dumps({"success": False, "error": "Échec mise à jour Shopify"}), status_code=500)

    except Exception as e:
        logger.error(f"Erreur Test: {str(e)}")
        return func.HttpResponse(json.dumps({"success": False, "error": str(e)}), status_code=500)


@app.route(route="validation_scan", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def http_validation_scan(req: func.HttpRequest) -> func.HttpResponse:
    """
    Exécute un vrai scan sur les 10 premiers clients éligibles trouvés.
    Déclenchera le Shopify Flow (Email Interne).
    """
    logger.info('=== Démarrage d\'un SCAN DE VALIDATION (Limite 10) ===')
    
    try:
        store_url = os.environ.get("SHOPIFY_STORE_URL")
        access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
        delay_start = int(os.environ.get("ORDER_DELAY_DAYS_START", 173))
        delay_end = int(os.environ.get("ORDER_DELAY_DAYS_END", 180))

        helper = ShopifyHelper(store_url, access_token=access_token)
        
        test_email = os.environ.get("TEST_CUSTOMER_EMAIL", "a.bezille@tb-groupe.fr")
        test_customer = helper.get_customer_by_email(test_email)
        if not test_customer:
            return func.HttpResponse(json.dumps({"success": False, "error": f"Client test {test_email} non trouvé"}), status_code=404)

        all_collections = {
            '298781474968': 'Forgés',
            '299133665432': 'Louis',
            '299133730968': 'Brigade forgé premium®',
            '303575662744': 'Forgé Premium Evercut®'
        }
        
        count = 0
        processed = []
        import time
        
        for collection_id, collection_name in all_collections.items():
            if count >= 10: break
            
            collection_product_data = helper.get_collection_products(collection_id)
            if not collection_product_data: continue
            
            eligible_entries = helper.get_eligible_customers(days_start=delay_start, days_end=delay_end, collection_id=collection_id)
            
            for entry in eligible_entries:
                if count >= 10: break
                
                real_customer = entry["customer"]
                history = helper.get_customer_purchase_history(real_customer.id)
                collection_product_ids = list(collection_product_data.keys())
                recommendations = [pid for pid in collection_product_ids if pid not in history][:3]
                
                if recommendations:
                    reco_data = [collection_product_data[pid] for pid in recommendations]
                    reco_names = [d["title"] for d in reco_data]
                    collection_url = helper.get_collection_url(collection_id)
                    
                    # On redirige la recommandation vers le client TEST
                    logger.info(f"Redirection: Simulation pour {real_customer.email} envoyée à {test_email} (Collection: {collection_name})")
                    if helper.update_customer_recommendations(test_customer.id, recommendations, manual_names=reco_names, manual_data=reco_data, collection_url=collection_url):
                        count += 1
                        processed.append({"simulated_for": real_customer.email, "recos": reco_names})
                        
                        # Petite pause pour laisser le temps au Flow de se déclencher avant l'écrasement suivant
                        time.sleep(3)
        
        return func.HttpResponse(json.dumps({
            "success": True, 
            "total_sent_to_test": count,
            "details": processed
        }), mimetype="application/json")

    except Exception as e:
        logger.error(f"Erreur Validation Scan: {str(e)}")
        return func.HttpResponse(json.dumps({"success": False, "error": str(e)}), status_code=500)


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
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "manual_check",
        "status": "started",
        "total_updated": 0,
        "errors": []
    }
    report_manager = ReportManager()

    # Capture des logs
    log_stream = io.StringIO()
    log_handler = logging.StreamHandler(log_stream)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_handler)

    try:
        req_body = req.get_json()
        customer_id = req_body.get("customer_id")
        collection_id = req_body.get("collection_id")
        force_update = req_body.get("force_update", False)  # Nouveau flag

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

        # Mise à jour réelle si demandée (utile pour les tests du Flow)
        update_status = "N/A"
        if force_update and recommendations:
            collection_url = helper.get_collection_url(collection_id)
            logger.info(f"Force Update activé pour le client {customer_id}")
            if helper.update_customer_recommendations(customer_id, recommendations, collection_url=collection_url):
                update_status = "Success (Metafield + Tag injectés)"
            else:
                update_status = "Failed"

        logger.info(f"Client {customer_id}: {len(recommendations)} recommandations trouvées")

        log_handler.flush()
        report["raw_logs"] = log_stream.getvalue()
        report["status"] = "success"
        report["total_updated"] = 1 if (force_update and recommendations) else 0
        logger.removeHandler(log_handler)
        report_manager.save_report(report)

        return func.HttpResponse(
            json.dumps({
                "success": True,
                "customer_id": customer_id,
                "collection_id": collection_id,
                "force_update": force_update,
                "shopify_update_status": update_status,
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
        
        log_handler.flush()
        report["raw_logs"] = log_stream.getvalue()
        report["status"] = "error"
        report["errors"].append(str(e))
        logger.removeHandler(log_handler)
        report_manager.save_report(report)

        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )



