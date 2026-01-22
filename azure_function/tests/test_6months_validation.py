#!/usr/bin/env python3
"""
Script de validation: Trouvez les clients qui ont acheté un produit il y a ~6 mois
(150-210 jours, soit 30-40 jours glissants de fenêtre), identifiez leur collection,
et proposez des produits complémentaires de la même collection.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict

# Ajouter le répertoire parent pour importer le module core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.shopify_helper import ShopifyHelper

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_collection_by_product_id(helper, product_id):
    """Trouve la collection contenant un produit donné."""
    # Récupérer tous les produits d'une collection (on doit itérer sur les collections)
    # Pour cette validation, on teste avec les collections principales
    
    known_collections = {
        '298781474968': 'Forgés',
        '299133665432': 'Louis',
        '299133763736': 'Brigade forgé premium',
        '303575662744': 'Forgé Premium Evercut'
    }
    
    for collection_id, collection_name in known_collections.items():
        try:
            products = helper.get_collection_products(collection_id)
            if product_id in products:
                return collection_id, collection_name
        except Exception as e:
            logger.debug(f"Erreur lors de la vérification de collection {collection_id}: {str(e)}")
            continue
    
    return None, "Inconnue"


def validate_6months_scenario():
    """
    Valide le scénario de 6 mois:
    1. Trouvez les clients ayant acheté il y a ~6 mois (150-210 jours)
    2. Identifiez leur collection d'achat
    3. Proposez des produits complémentaires
    
    NOTE: Pour les tests avec données faibles, on teste sur les 30 derniers jours
    avec la collection Forgés (validée comme active).
    """
    
    logger.info("=" * 80)
    logger.info("VALIDATION: Clients 6 mois + Détection Collection + Recommandations")
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
    
    # Pour test avec données réelles: Utiliser les 30 derniers jours
    # (En production, on utiliserait 150-210 jours pour le scénario 6 mois)
    DAYS_START = 0   # Aujourd'hui
    DAYS_END = 30    # Derniers 30 jours
    
    logger.info(f"Recherche TEST: Clients ayant acheté entre {DAYS_START} et {DAYS_END} jours")
    logger.info("(En production, on chercherait 150-210 jours pour 6 mois)")
    
    # 1. Faire une recherche brute sur TOUS les clients ayant commandé dans cette fenêtre
    #    (indépendamment de la collection)
    try:
        # Récupérer TOUS les produits des collections principales
        all_collection_products = {}
        known_collections = {
            '298781474968': 'Forgés',
            '299133665432': 'Louis',
            '299133763736': 'Brigade forgé premium',
            '303575662744': 'Forgé Premium Evercut'
        }
        
        for coll_id, coll_name in known_collections.items():
            try:
                products = helper.get_collection_products(coll_id)
                all_collection_products[coll_id] = {
                    'name': coll_name,
                    'products': products
                }
            except Exception as e:
                logger.warning(f"Erreur lors de la récupération des produits de {coll_name}: {str(e)}")
        
        logger.info(f"✓ Collections: {len(all_collection_products)} collections chargées")
        
        # Chercher des clients dans CHAQUE collection sur la fenêtre
        results_by_collection = {}
        
        for collection_id, collection_info in all_collection_products.items():
            coll_name = collection_info['name']
            try:
                # Chercher les clients éligibles pour cette collection
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
            logger.warning("❌ Aucun client trouvé dans la fenêtre de test")
            return False
        
        logger.info(f"✓ Clients trouvés: {sum(len(data['customers']) for data in results_by_collection.values())} clients")
        
        # 2. Pour chaque client, calculer les recommandations
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
                    # Récupérer l'historique d'achat du client
                    history = helper.get_customer_purchase_history(customer.id)
                    
                    # Produits non achetés de cette collection
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
        
        # 3. Résumé final
        logger.info("\n" + "=" * 80)
        logger.info("RÉSUMÉ VALIDATION")
        logger.info("=" * 80)
        logger.info(f"Fenêtre temporelle TEST: {DAYS_START}-{DAYS_END} jours")
        logger.info(f"(En production: 150-210 jours pour scénario 6 mois)")
        logger.info(f"Total clients trouvés: {sum(len(data['customers']) for data in results_by_collection.values())}")
        logger.info(f"Clients avec recommandations: {total_with_recommendations}")
        logger.info(f"Total recommandations générées: {total_recommended}")
        
        if total_with_recommendations > 0:
            logger.info(f"Moyenne recommandations/client: {total_recommended/total_with_recommendations:.1f}")
            logger.info("✅ VALIDATION: SUCCESS")
            return True
        else:
            logger.warning("⚠️ VALIDATION: Aucune recommandation générée")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = validate_6months_scenario()
    sys.exit(0 if success else 1)
