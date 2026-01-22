#!/usr/bin/env python3
"""
Trouve les 2 collections avec le plus de ventes il y a pile 6 mois (fenêtre 30 jours).

Fenêtre: J-210 à J-180 jours (6 mois ±15 jours)
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.shopify_helper import ShopifyHelper
import shopify

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_top_collections_6months_ago():
    """
    Analyse les commandes de 6 mois ago (fenêtre 30 jours)
    et trouve les 2 collections avec le plus de ventes.
    """
    
    logger.info("=" * 100)
    logger.info("🔍 RECHERCHE: Collections les plus vendues il y a 6 mois (fenêtre 30 jours)")
    logger.info("=" * 100)
    
    # Configuration
    store_url = os.environ.get("SHOPIFY_STORE_URL")
    access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    client_id = os.environ.get("SHOPIFY_CLIENT_ID")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")
    
    if not store_url or not (access_token or (client_id and client_secret)):
        logger.error("❌ Variables d'environnement manquantes")
        return False
    
    logger.info("✅ Configuration OK")
    
    helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)
    
    # Fenêtre: 6 mois ±15 jours = J-210 à J-180
    DAYS_START = 180  # 6 mois pile
    DAYS_END = 210    # 6 mois - 30 jours
    
    today = datetime.utcnow()
    date_start = today - timedelta(days=DAYS_END)
    date_end = today - timedelta(days=DAYS_START)
    
    logger.info(f"\n📅 Fenêtre: {date_start.date()} à {date_end.date()} ({DAYS_END - DAYS_START} jours)")
    
    try:
        # Récupérer TOUTES les commandes de cette période
        logger.info(f"\n🔄 Récupération des commandes...")
        
        # Utiliser shopify pour récupérer les commandes
        import shopify
        
        # Créer une session shopify
        session = shopify.Session(store_url, '2025-01', access_token)
        shopify.ShopifyResource.activate_session(session)
        
        # Récupérer les commandes
        orders = shopify.Order.find(
            created_at_min=date_start.isoformat() + 'Z',
            created_at_max=date_end.isoformat() + 'Z',
            status='any',
            limit=250
        )
        
        logger.info(f"✅ {len(orders)} commandes trouvées")
        
        # Analyser les collections par nombre de ventes
        collection_sales = defaultdict(lambda: {'count': 0, 'revenue': 0, 'name': ''})
        
        # Récupérer toutes les collections pour mapper les IDs
        logger.info("\n📚 Récupération des collections...")
        import requests
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        all_collections_map = {}
        after = None
        
        while True:
            query = f"""
            {{
              collections(first: 100 {', after: "' + after + '"' if after else ''}) {{
                edges {{
                  node {{
                    id
                    title
                  }}
                }}
                pageInfo {{
                  hasNextPage
                  endCursor
                }}
              }}
            }}
            """
            
            response = requests.post(
                f"https://{store_url}/admin/api/2025-01/graphql.json",
                json={"query": query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                for edge in data['data']['collections']['edges']:
                    node = edge['node']
                    numeric_id = node['id'].split('/')[-1]
                    all_collections_map[numeric_id] = node['title']
                
                if not data['data']['collections']['pageInfo']['hasNextPage']:
                    break
                after = data['data']['collections']['pageInfo']['endCursor']
            else:
                logger.warning(f"Erreur: {response.text}")
                break
        
        logger.info(f"✅ {len(all_collections_map)} collections mappées")
        
        # Analyser les line items des commandes
        logger.info("\n📊 Analyse des ventes par collection...")
        
        for order in orders:
            total = float(order.total_price or 0)
            
            for line_item in order.line_items or []:
                product_id = line_item.product_id
                
                if product_id:
                    # Pour chaque produit, déterminer sa collection
                    try:
                        product = shopify.Product.find(product_id)
                        
                        # Extraire les collections du produit (via les tags/handle)
                        # Chercher via get_collection_products pour ce produit
                        # Simplification: chercher manuellement via API
                        pass
                        
                    except Exception as e:
                        logger.debug(f"Erreur produit {product_id}: {str(e)}")
                        continue
        
        # Alternative plus simple: chercher par commandes par collection
        logger.info("\n📊 Scan de toutes les collections...")
        
        import requests
        import time
        
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        # Récupérer toutes les collections
        all_collections_map = {}
        after = None
        
        while True:
            query = f"""
            {{
              collections(first: 100 {', after: "' + after + '"' if after else ''}) {{
                edges {{
                  node {{
                    id
                    title
                  }}
                }}
                pageInfo {{
                  hasNextPage
                  endCursor
                }}
              }}
            }}
            """
            
            response = requests.post(
                f"https://{store_url}/admin/api/2025-01/graphql.json",
                json={"query": query},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                for edge in data['data']['collections']['edges']:
                    node = edge['node']
                    numeric_id = node['id'].split('/')[-1]
                    all_collections_map[numeric_id] = node['title']
                
                if not data['data']['collections']['pageInfo']['hasNextPage']:
                    break
                after = data['data']['collections']['pageInfo']['endCursor']
                time.sleep(0.5)
            else:
                logger.warning(f"Erreur GraphQL: {response.text}")
                break
        
        logger.info(f"✅ {len(all_collections_map)} collections trouvées")
        
        # Scanner chaque collection pour trouver les ventes
        collection_sales = defaultdict(lambda: {'count': 0, 'revenue': 0, 'name': ''})
        
        for coll_id, coll_name in all_collections_map.items():
            logger.info(f"🔍 Analysing {coll_name}...")
            
            try:
                # Chercher les produits de cette collection
                products = helper.get_collection_products(coll_id)
                product_ids = [p for p in products]
                
                if not product_ids:
                    continue
                
                # Chercher les commandes contenant ces produits
                for order in orders:
                    order_total = float(order.total_price or 0)
                    
                    for line_item in order.line_items or []:
                        if line_item.product_id in product_ids:
                            collection_sales[coll_id]['count'] += 1
                            collection_sales[coll_id]['revenue'] += order_total / len(order.line_items or [1])
                            collection_sales[coll_id]['name'] = coll_name
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.debug(f"Erreur {coll_name}: {str(e)}")
                continue
        
    except Exception as e:
        logger.error(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    top_collections = find_top_collections_6months_ago()
    
    if top_collections:
        logger.info("\n" + "=" * 100)
        logger.info("Utilise ces IDs pour le test:")
        for coll_id, data in top_collections:
            logger.info(f"  '{coll_id}': '{data['name']}',")
    else:
        logger.error("Impossible de trouver les collections")
        sys.exit(1)
