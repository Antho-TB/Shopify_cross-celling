import azure.functions as func
import logging
import os
import json
import io
from datetime import datetime
from shopify_helper import ShopifyHelper
from report_manager import ReportManager

app = func.FunctionApp()

# Configuration du logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# @app.schedule(schedule="0 0 2 * * 1", arg_name="myTimer", run_on_startup=False, use_monitor=False) 
# def weekly_cross_sell_scanner_timer(myTimer: func.TimerRequest) -> None:
#     """Désactivé : Le scan est maintenant piloté exclusivement par Shopify Flow."""
#     run_global_scan()

@app.route(route="run_global_scan", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def http_run_global_scan(req: func.HttpRequest) -> func.HttpResponse:
    """Permet à Shopify Flow de déclencher le scan manuellement ou sur programme."""
    try:
        results = run_global_scan()
        # Si des erreurs critiques ont été détectées durant le scan, on peut aussi décider de renvoyer un 500
        # Mais ici on préfère renvoyer 200 avec la liste des erreurs pour que Flow puisse faire un choix.
        return func.HttpResponse(json.dumps({"success": True, "details": results}), mimetype="application/json")
    except Exception as e:
        logger.error(f"CRITICAL FAILURE: {str(e)}")
        return func.HttpResponse(
            json.dumps({"success": False, "error": str(e)}), 
            status_code=500, 
            mimetype="application/json"
        )

def run_global_scan():
    """Cœur de la logique de scan (Mutualisé)."""
    logger.info('=== Démarrage du scan global (Production) ===')
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "type": "SCAN",
        "status": "in_progress",
        "total_found": 0,
        "total_updated": 0,
        "skipped_rgpd": 0,
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
        
        # Fenêtre de 6 mois (173-180 jours) - Rétablie
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

        total_customers_found = 0
        total_customers_updated = 0
        total_skipped_rgpd = 0
        detailed_errors = []
        
        # 2. Itération sur chaque collection cible
        for coll_id, coll_name in collections.items():
            logger.info(f"Scanning collection: {coll_name}")
            
            # Récupération de tous les produits de cette collection
            coll_products = helper.get_collection_products(coll_id)
            if not coll_products: continue
            
            # Recherche des clients ayant acheté dans cette collection il y a ~6 mois
            eligible, skipped = helper.get_eligible_customers(days_start=delay_start, days_end=delay_end, collection_id=coll_id)
            
            total_customers_found += len(eligible) + skipped
            total_skipped_rgpd += skipped
            
            coll_updated_count = 0

            # 3. Traitement de chaque client éligible trouvé
            for entry in eligible:
                customer = entry["customer"]
                try:
                    # On compare ce qu'il a déjà acheté avec le contenu de la collection
                    history = helper.get_customer_purchase_history(customer.id)
                    p_ids = list(coll_products.keys())
                    
                    # Les recommandations sont les produits de la collection qu'il n'a PAS encore acheté
                    recos = [pid for pid in p_ids if pid not in history][:3]
                    
                    if recos:
                        reco_data = [coll_products[pid] for pid in recos]
                        reco_names = [d["title"] for d in reco_data]
                        logger.info(f"  -> {len(recos)} recos trouvées pour {customer.email}: {', '.join(reco_names)}")
                        coll_url = helper.get_collection_url(coll_id)
                        
                        # 4. Mise à jour Shopify : Injection des Metafields et du Tag déclencheur
                        if helper.update_customer_recommendations(
                            customer.id, 
                            recos, 
                            manual_names=reco_names, 
                            manual_data=reco_data, 
                            collection_url=coll_url,
                            last_product_name=entry["purchased_product"],
                            last_collection_name=coll_name
                        ):
                            coll_updated_count += 1
                        else:
                            detailed_errors.append(f"Échec sauvegarde pour {customer.email}")
                    else:
                        logger.info(f"  -> 0 reco pour {customer.email}")
                except Exception as e:
                    err_msg = f"Erreur client {getattr(customer, 'email', customer.id)}: {str(e)}"
                    logger.error(err_msg)
                    detailed_errors.append(err_msg)
            
            total_customers_updated += coll_updated_count
            logger.info(f"Collection {coll_name}: {coll_updated_count} clients mis à jour")
        
        report["status"] = "success"
        report["total_found"] = total_customers_found
        report["total_updated"] = total_customers_updated
        report["skipped_rgpd"] = total_skipped_rgpd
        report["errors"] = detailed_errors
        
        log_handler.flush()
        report["raw_logs"] = log_stream.getvalue()
        logger.removeHandler(log_handler)
        report_manager.save_report(report)
        
        return {
            "total_found": total_customers_found,
            "updated": total_customers_updated,
            "skipped_rgpd": total_skipped_rgpd,
            "errors": detailed_errors[:5] # On envoie les 5 premières erreurs max à Shopify
        }

    except Exception as e:
        logger.error(f"Erreur fatale: {str(e)}")
        report["status"] = "error"
        report["errors"].append(str(e))
        log_handler.flush()
        report["raw_logs"] = log_stream.getvalue()
        logger.removeHandler(log_handler)
        report_manager.save_report(report)
        raise e


@app.route(route="status", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def get_status_dashboard(req: func.HttpRequest) -> func.HttpResponse:
    """
    Archive: Le dashboard a été mis hors ligne pour la production.
    Consulter azure_function/Doc/dashboard_archive.html pour le code.
    """
    return func.HttpResponse("Dashboard archived for production.", status_code=404)
