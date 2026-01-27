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

@app.schedule(schedule="0 0 2 * * 1", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
def weekly_cross_sell_scanner_timer(myTimer: func.TimerRequest) -> None:
    """Déclencheur temporel par défaut (Lundi 2h)."""
    run_global_scan()

@app.route(route="run_global_scan", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def http_run_global_scan(req: func.HttpRequest) -> func.HttpResponse:
    """Permet à Shopify Flow de déclencher le scan manuellement ou sur programme."""
    try:
        results = run_global_scan()
        return func.HttpResponse(json.dumps({"success": True, "details": results}), mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(json.dumps({"success": False, "error": str(e)}), status_code=500)

def run_global_scan():
    """Cœur de la logique de scan (Mutualisé)."""
    logger.info('=== Démarrage du scan global (Production) ===')
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "type": "SCAN",
        "status": "in_progress",
        "total_updated": 0,
        "errors": [],
        "raw_logs": ""
    }
    
    # Capture des logs pour le dashboard
    log_stream = io.StringIO()
    log_handler = logging.StreamHandler(log_stream)
    logger.addHandler(log_handler)
    
    try:
        store_url = os.environ.get("SHOPIFY_STORE_URL")
        access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
        
        # Fenêtre de 6 mois (173-180 jours)
        delay_start = int(os.environ.get("ORDER_DELAY_DAYS_START", 173))
        delay_end = int(os.environ.get("ORDER_DELAY_DAYS_END", 180))

        helper = ShopifyHelper(store_url, access_token=access_token)
        report_manager = ReportManager()

        # Liste des collections à scanner
        collections = {
            "299133665432": "Louis",
            "298781474968": "Forgés",
            "299133730968": "Brigade",
            "303575662744": "Forgé Premium Evercut"
        }

        total_customers_updated = 0
        
        for coll_id, coll_name in collections.items():
            logger.info(f"Scanning collection: {coll_name}")
            
            coll_products = helper.get_collection_products(coll_id)
            if not coll_products: continue
            
            eligible = helper.get_eligible_customers(days_start=delay_start, days_end=delay_end, collection_id=coll_id)
            coll_updated_count = 0

            for entry in eligible:
                customer = entry["customer"]
                try:
                    history = helper.get_customer_purchase_history(customer.id)
                    p_ids = list(coll_products.keys())
                    recos = [pid for pid in p_ids if pid not in history][:3]
                    
                    if recos:
                        reco_data = [coll_products[pid] for pid in recos]
                        reco_names = [d["title"] for d in reco_data]
                        coll_url = helper.get_collection_url(coll_id)
                        
                        if helper.update_customer_recommendations(customer.id, recos, manual_names=reco_names, manual_data=reco_data, collection_url=coll_url):
                            coll_updated_count += 1
                except Exception as e:
                    logger.error(f"Erreur client {customer.id}: {str(e)}")
            
            total_customers_updated += coll_updated_count
            logger.info(f"Collection {coll_name}: {coll_updated_count} clients mis à jour")
        
        report["status"] = "success"
        report["total_updated"] = total_customers_updated
        
        log_handler.flush()
        report["raw_logs"] = log_stream.getvalue()
        logger.removeHandler(log_handler)
        report_manager.save_report(report)
        
        return {"updated": total_customers_updated}

    except Exception as e:
        logger.error(f"Erreur fatale: {str(e)}")
        report["status"] = "error"
        report["errors"].append(str(e))
        log_handler.flush()
        report["raw_logs"] = log_stream.getvalue()
        logger.removeHandler(log_handler)
        report_manager.save_report(report)
        raise e


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
        
        # On peut passer une collection spécifique via le body ou query
        collection_id_param = req.params.get("collection_id")
        if not collection_id_param:
            try:
                collection_id_param = req.get_json().get("collection_id")
            except: pass

        delay_start = int(os.environ.get("SIMUL_ORDER_DELAY_START", 173))
        delay_end = int(os.environ.get("SIMUL_ORDER_DELAY_END", 180))

        if not store_url:
            return func.HttpResponse(json.dumps({"error": "Config manquante"}), status_code=500)

        helper = ShopifyHelper(store_url, access_token=access_token)

        all_collections = {
            '298781474968': 'Forgés',
            '299133665432': 'Louis',
            '299133730968': 'Brigade forgé premium®',
            '303575662744': 'Forgé Premium Evercut®'
        }
        
        # Si une collection est spécifiée, on ne scanne que celle-là
        collections_to_scan = {collection_id_param: all_collections.get(collection_id_param, "Inconnue")} if collection_id_param else all_collections

        for collection_id, collection_name in collections_to_scan.items():
            collection_product_data = helper.get_collection_products(collection_id)
            if not collection_product_data: continue
            
            eligible_entries = helper.get_eligible_customers(days_start=delay_start, days_end=delay_end, collection_id=collection_id)
            
            for entry in eligible_entries:
                customer = entry["customer"]
                history = helper.get_customer_purchase_history(customer.id)
                
                collection_product_ids = list(collection_product_data.keys())
                remaining_products = [pid for pid in collection_product_ids if pid not in history]
                
                if remaining_products:
                    reco_data = [collection_product_data[pid] for pid in remaining_products[:3]]
                    reco_names = [d["title"] for d in reco_data]
                    
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
        
        # Collection spécifique depuis paramètres
        collection_id = req.params.get("collection_id")
        if not collection_id:
            try:
                collection_id = req.get_json().get("collection_id")
            except: pass
        if not collection_id:
            collection_id = "299133665432" # Louis par défaut

        helper = ShopifyHelper(store_url, access_token=access_token)
        
        # 1. Recherche du client par email
        import shopify
        customers = shopify.Customer.search(query=f"email:{email}")
        if not customers:
            return func.HttpResponse(json.dumps({"success": False, "error": f"Client {email} non trouvé dans Shopify"}), status_code=404)
        
        customer = customers[0]
        logger.info(f"Client trouvé: {customer.id} ({customer.email})")

        # 2. Calcul recommandation
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
                "collection_id": collection_id,
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
        
        # Paramètres optionnels
        collection_id_param = req.params.get("collection_id")
        if not collection_id_param:
            try:
                collection_id_param = req.get_json().get("collection_id")
            except: pass

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
        
        # Filtre par collection si spécifié
        collections_to_scan = {collection_id_param: all_collections.get(collection_id_param, "Inconnue")} if collection_id_param else all_collections

        count = 0
        processed = []
        import time
        
        limit_total = 5 # On limite à 5 mails TOTAL pour éviter le spam
        for collection_id, collection_name in collections_to_scan.items():
            if count >= limit_total: break
            
            collection_product_data = helper.get_collection_products(collection_id)
            if not collection_product_data: continue
            
            eligible_entries = helper.get_eligible_customers(days_start=delay_start, days_end=delay_end, collection_id=collection_id)
            
            for entry in eligible_entries:
                if count >= limit_total: break
                
                real_customer = entry["customer"]
                history = helper.get_customer_purchase_history(real_customer.id)
                collection_product_ids = list(collection_product_data.keys())
                recommendations = [pid for pid in collection_product_ids if pid not in history][:3]
                
                if recommendations:
                    reco_data = [collection_product_data[pid] for pid in recommendations]
                    reco_names = [d["title"] for d in reco_data]
                    collection_url = helper.get_collection_url(collection_id)
                    
                    # On redirige la recommandation vers le client TEST
                    logger.info(f"Redirection ({count+1}/{limit_total}): Simulation pour {real_customer.email} envoyée à {test_email} (Collection: {collection_name})")
                    if helper.update_customer_recommendations(test_customer.id, recommendations, manual_names=reco_names, manual_data=reco_data, collection_url=collection_url):
                        count += 1
                        processed.append({"simulated_for": real_customer.email, "collection": collection_name, "recos": reco_names})
                        
                        time.sleep(15) # Un peu plus de temps pour éviter les collisions Flow
        
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
@app.route(route="status", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def get_status_dashboard(req: func.HttpRequest) -> func.HttpResponse:
    """
    Archive: Le dashboard a été mis hors ligne pour la production.
    Consulter azure_function/Doc/dashboard_archive.html pour le code.
    """
    return func.HttpResponse("Dashboard archived for production.", status_code=404)
