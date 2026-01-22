#!/usr/bin/env python3
"""
Script de validation: Fenêtre 6 mois ±7 jours (173-180 jours)
Utilisé pour le scan hebdomadaire du lundi.

Cherche les clients qui ont acheté il y a 6 mois jour pour jour ±7 jours
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Ajouter le répertoire parent pour importer le module core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.shopify_helper import ShopifyHelper

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_6months_weekly_window():
    """
    Valide le scénario de relance hebdomadaire: 6 mois ±7 jours (173-180 jours)
    
    TEST: Utilise seulement Forgé et Louis pour validation rapide
    PROD: Scanner toutes les collections (voir function_app.py)
    """
    
    logger.info("=" * 80)
    logger.info("VALIDATION: Fenêtre 6 mois ±7 jours (173-180 jours)")
    logger.info("Mode: TEST (collections: Forgé + Louis)")
    logger.info("Pour production: Toutes les collections seront scannées")
    logger.info("=" * 80)
    
    # Configuration
    store_url = os.environ.get("SHOPIFY_STORE_URL")
    access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    client_id = os.environ.get("SHOPIFY_CLIENT_ID")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")
    
    if not store_url or not (access_token or (client_id and client_secret)):
        logger.error("❌ Configuration: Variables d'environnement manquantes")
        return False
    
    logger.info("✓ Configuration: Environnement OK")
    
    # Initialiser le helper
    helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)
    
    # Fenêtre: 6 mois ±7 jours = 173-180 jours
    DAYS_START = 173  # 6 mois - 7 jours
    DAYS_END = 180    # 6 mois pile
    
    logger.info(f"Recherche: Clients ayant acheté entre {DAYS_START} et {DAYS_END} jours")
    
    # Calculer les dates réelles
    today = datetime.utcnow()
    date_start = today - timedelta(days=DAYS_END)
    date_end = today - timedelta(days=DAYS_START)
    logger.info(f"Périodes réelles: {date_start.date()} à {date_end.date()}")
    
    try:
        # Récupérer les produits des collections principales
        # MODE TEST: Seulement Forgé et Louis pour validation rapide
        # MODE PROD: Toutes les collections (voir function_app.py)
        
        test_collections = {
            '298781474968': 'Forgés',
            '299133665432': 'Louis',
        }
        
        all_collection_products = {}
        for coll_id, coll_name in test_collections.items():
            try:
                products = helper.get_collection_products(coll_id)
                all_collection_products[coll_id] = {
                    'name': coll_name,
                    'products': products
                }
            except Exception as e:
                logger.warning(f"Erreur lors de la récupération des produits de {coll_name}: {str(e)}")
        
        logger.info(f"✓ Collections TEST: {len(all_collection_products)} collections")
        logger.info("  (En production: toutes les collections seront scannées)")
        
        # Chercher des clients dans CHAQUE collection
        results_by_collection = {}
        
        for collection_id, collection_info in all_collection_products.items():
            coll_name = collection_info['name']
            try:
                customers = helper.get_eligible_customers(
                    days_start=DAYS_START,
                    days_end=DAYS_END,
                    collection_id=collection_id
                )
                
                if customers:
                    results_by_collection[collection_id] = {
                        'name': coll_name,
                        'customers': customers,
                        'products': collection_info['products']
                    }
                    logger.info(f"  {coll_name}: {len(customers)} clients trouvés")
                    
            except Exception as e:
                logger.warning(f"Erreur lors de la recherche de clients pour {coll_name}: {str(e)}")
        
        if not results_by_collection:
            logger.warning("⚠️ Aucun client trouvé dans la fenêtre 6 mois ±7 jours")
            logger.info("(Cela peut être normal si peu de clients ont acheté exactement à cette période)")
            return False
        
        logger.info(f"✓ Clients trouvés: {sum(len(data['customers']) for data in results_by_collection.values())} clients")
        
        # Pour chaque client, calculer les recommandations
        logger.info("\n" + "=" * 80)
        logger.info("ANALYSE DÉTAILLÉE PAR CLIENT")
        logger.info("=" * 80)
        
        total_recommended = 0
        total_with_recommendations = 0
        
        for collection_id, collection_data in results_by_collection.items():
            coll_name = collection_data['name']
            customers = collection_data['customers']
            all_products = collection_data['products']
            
            logger.info(f"\n📦 Collection: {coll_name}")
            logger.info(f"   Produits disponibles: {len(all_products)}")
            logger.info(f"   Clients: {len(customers)}")
            logger.info("-" * 80)
            
            for customer in customers:
                try:
                    history = helper.get_customer_purchase_history(customer.id)
                    remaining = [pid for pid in all_products if pid not in history]
                    recommendations = remaining[:3]
                    
                    if recommendations:
                        total_with_recommendations += 1
                        total_recommended += len(recommendations)
                        
                        logger.info(f"   👤 {customer.email}")
                        logger.info(f"      Historique: {len(history)} produits achetés")
                        logger.info(f"      Recommandations: {len(recommendations)} produits")
                        logger.info(f"      IDs: {recommendations}")
                    else:
                        logger.info(f"   👤 {customer.email} - Aucune recommandation (tous les produits achetés)")
                        
                except Exception as e:
                    logger.error(f"   ❌ Erreur pour client {customer.email}: {str(e)}")
        
        # Résumé final
        logger.info("\n" + "=" * 80)
        logger.info("RÉSUMÉ VALIDATION - FENÊTRE 6 MOIS ±7 JOURS")
        logger.info("=" * 80)
        logger.info(f"Fenêtre temporelle: {DAYS_START}-{DAYS_END} jours")
        logger.info(f"Dates: {date_start.date()} à {date_end.date()}")
        logger.info(f"Total clients trouvés: {sum(len(data['customers']) for data in results_by_collection.values())}")
        logger.info(f"Clients avec recommandations: {total_with_recommendations}")
        logger.info(f"Total recommandations générées: {total_recommended}")
        
        if total_with_recommendations > 0:
            logger.info(f"Moyenne recommandations/client: {total_recommended/total_with_recommendations:.1f}")
            logger.info("✅ VALIDATION: SUCCESS (Prêt pour relance hebdomadaire)")
            return True
        else:
            logger.warning("⚠️ VALIDATION: Pas de recommandations générées")
            logger.info("(Peut être normal si peu de clients dans cette fenêtre)")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = validate_6months_weekly_window()
    sys.exit(0 if success else 1)
