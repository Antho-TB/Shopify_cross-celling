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
        
        # On peut passer une collection spécifique via le body ou query
        collection_id_param = req.params.get("collection_id")
        if not collection_id_param:
            try:
                collection_id_param = req.get_json().get("collection_id")
            except: pass

        delay_start = int(os.environ.get("ORDER_DELAY_DAYS_START", 173))
        delay_end = int(os.environ.get("ORDER_DELAY_DAYS_END", 180))

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
        
        for collection_id, collection_name in collections_to_scan.items():
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
                        processed.append({"simulated_for": real_customer.email, "collection": collection_name, "recos": reco_names})
                        
                        time.sleep(10) # Pause pour Flow
        
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
    Tableau de bord de surveillance et de test (Restauré & Amélioré)
    """
    report_manager = ReportManager()
    reports = report_manager.get_latest_reports(limit=5)
    
    total_updated_all = sum(r.get('total_updated', 0) for r in reports)
    
    reports_html = ""
    for r in reports:
        ts = r['timestamp'].replace('T', ' ')[:19]
        rtype = r.get('type', 'SCAN').upper()
        rstatus = r['status'].upper()
        color = 'var(--success)' if r['status'] == 'success' else 'var(--error)'
        count = r.get('total_updated', 0)
        logs = r.get('raw_logs', 'Logs en cours...').replace('\n', '<br>')
        
        reports_html += f"""
        <div class="report-item">
            <div class="report-header">
                <div style="font-weight:700;">{ts}</div>
                <span class="tag">{rtype}</span>
                <div style="color:{color}">{rstatus} • {count} clients</div>
            </div>
            <div style="padding:20px;">
                <div class="raw-logs">{logs}</div>
            </div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Surveillance du Cross-selling • TB Groupe</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #0a0e14;
                --card-bg: #141b24;
                --text: #e2e8f0;
                --primary: #c5a67c;
                --secondary: #ff6b00;
                --success: #10b981;
                --error: #f43f5e;
                --accent: #1e293b;
            }}
            body {{
                font-family: 'Outfit', sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 0;
                line-height: 1.6;
            }}
            .top-bar {{ background: linear-gradient(to right, #141b24, #1e293b); height: 4px; width: 100%; }}
            .container {{ max-width: 1100px; margin: 0 auto; padding: 60px 20px; }}
            header {{ text-align: center; margin-bottom: 60px; }}
            .logo-placeholder {{ font-weight: 700; font-size: 1.2rem; letter-spacing: 0.2rem; text-transform: uppercase; color: var(--primary); margin-bottom: 20px; display: block; }}
            h1 {{ font-size: 3rem; margin: 0; font-weight: 700; letter-spacing: -0.025em; color: #ffffff; }}
            .subtitle {{ color: #94a3b8; max-width: 600px; margin: 15px auto; font-size: 1.1rem; font-weight: 300; }}
            
            .config-panel {{
                background: var(--card-bg);
                padding: 30px;
                border-radius: 20px;
                margin-bottom: 40px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 20px;
            }}
            .select-wrapper {{ width: 100%; max-width: 400px; }}
            select {{
                width: 100%;
                padding: 12px;
                background: var(--bg);
                border: 1px solid var(--accent);
                color: #fff;
                border-radius: 8px;
                font-family: inherit;
                font-size: 1rem;
            }}
            
            .actions-panel {{ display: flex; justify-content: center; gap: 20px; margin-bottom: 40px; }}
            .btn {{ padding: 14px 28px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; border: none; font-size: 1rem; }}
            .btn-primary {{ background-color: var(--primary); color: #000; }}
            .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px -10px var(--primary); }}
            .btn-secondary {{ background-color: transparent; border: 1px solid var(--secondary); color: var(--secondary); }}
            .btn-secondary:hover {{ background-color: var(--secondary); color: #fff; }}
            
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; margin-bottom: 60px; }}
            .stat-card {{ background: var(--card-bg); padding: 30px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.05); }}
            .stat-label {{ font-size: 0.9rem; color: #64748b; text-transform: uppercase; font-weight: 600; }}
            .stat-value {{ font-size: 2.5rem; font-weight: 700; color: #fff; }}
            
            .section-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-left: 3px solid var(--primary); padding-left: 15px; }}
            .report-item {{ background: var(--card-bg); border-radius: 20px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.03); overflow: hidden; }}
            .report-header {{ padding: 25px 30px; display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02); }}
            .tag {{ padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; background: var(--accent); color: var(--primary); }}
            .raw-logs {{ background: #000; color: #10b981; font-family: monospace; padding: 20px; border-radius: 12px; font-size: 0.85rem; max-height: 400px; overflow-y: auto; }}
            
            #loading-overlay {{ 
                display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.85); z-index: 1000; flex-direction: column; justify-content: center; align-items: center; 
            }}
            .loader {{ border: 4px solid #1a2430; border-top: 4px solid var(--secondary); border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            
            .data-table {{ width: 100%; border-collapse: collapse; }}
            .data-table th {{ text-align: left; padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #64748b; font-size: 0.85rem; }}
            .data-table td {{ padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        </style>
    </head>
    <body>
        <div id="loading-overlay"><div class="loader"></div><div style="color:#fff; margin-top:20px;">Traitement en cours...</div></div>
        <div class="top-bar"></div>
        <div class="container">
            <header>
                <div class="logo-placeholder">TB GROUPE</div>
                <h1>Surveillance du Cross-selling</h1>
                <p class="subtitle">Outil de test et de diagnostic des recommandations.</p>
            </header>

            <div class="config-panel">
                <div style="font-weight:600; color: var(--primary)">SÉLECTIONNER UNE COLLECTION POUR LE TEST :</div>
                <div class="select-wrapper">
                    <select id="collection-selector">
                        <option value="299133665432">Louis (Couteaux de table)</option>
                        <option value="298781474968">Forgés (Cuisine traditionnelle)</option>
                        <option value="299133730968">Brigade forgé premium®</option>
                        <option value="303575662744">Forgé Premium Evercut®</option>
                        <option value="">-- TOUTES LES COLLECTIONS --</option>
                    </select>
                </div>
            </div>

            <div class="actions-panel">
                <button class="btn btn-primary" onclick="runAction('dry_run')">Simuler (Dry Run)</button>
                <button class="btn btn-secondary" onclick="runAction('trigger_test')" style="border-color: var(--primary); color: var(--primary)">Tester sur mon mail</button>
                <button class="btn btn-secondary" onclick="runAction('validation_scan')">Scan Validation (10 réels)</button>
            </div>

            <div id="results-area" style="display:none; margin-bottom:60px;">
                <div class="section-header"><h2>Détails de l'opération</h2></div>
                <div class="report-item" style="padding:20px; overflow-x:auto;">
                    <table class="data-table"><tbody id="results-body"></tbody></table>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Clients Ciblés (Historique)</div>
                    <div class="stat-value">{total_updated_all}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">État Système</div>
                    <div class="stat-value" style="color:var(--success)">OPÉRATIONNEL</div>
                </div>
            </div>

            <div class="section-header"><h2>Historique Récent</h2></div>
            {reports_html}
        </div>

        <script>
            async function runAction(endpoint) {{
                const colId = document.getElementById('collection-selector').value;
                const overlay = document.getElementById('loading-overlay');
                overlay.style.display = 'flex';
                
                try {{
                    const url = `/api/${{endpoint}}?collection_id=${{colId}}`;
                    const res = await fetch(url, {{ method: 'POST' }});
                    const data = await res.json();
                    
                    const area = document.getElementById('results-area');
                    const body = document.getElementById('results-body');
                    body.innerHTML = '';
                    area.style.display = 'block';
                    
                    if(data.simulated_updates) {{
                        data.simulated_updates.forEach(u => {{
                            body.innerHTML += `<tr><td>${{u.email}}</td><td><span class="tag">${{u.collection}}</span></td><td style="color:var(--primary)">${{u.recommendations.join(' • ')}}</td></tr>`;
                        }});
                    }} else if(data.details) {{
                        data.details.forEach(d => {{
                            body.innerHTML += `<tr><td>${{d.simulated_for}}</td><td><span class="tag">${{d.collection}}</span></td><td>Redirigé vers vous</td></tr>`;
                        }});
                    }} else if(data.success) {{
                        body.innerHTML = `<tr><td style="color:var(--success); font-weight:700;">SUCCÈS: Opération effectuée avec succès. Vérifiez vos emails et les logs Azure.</td></tr>`;
                    }} else {{
                        body.innerHTML = `<tr><td style="color:var(--error);">${{data.error || 'Erreur inconnue'}}</td></tr>`;
                    }}
                    window.scrollTo({{ top: area.offsetTop - 50, behavior: 'smooth' }});
                }} catch(e) {{ alert('Erreur: ' + e); }}
                finally {{ overlay.style.display = 'none'; }}
            }}
        </script>
    </body>
    </html>
    """
    return func.HttpResponse(html_content, mimetype="text/html")
