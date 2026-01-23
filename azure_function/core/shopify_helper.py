import shopify
import os
import requests
import logging
from datetime import datetime, timedelta

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ShopifyHelper:
    def __init__(self, store_url, access_token=None, client_id=None, client_secret=None):
        self.store_url = store_url
        logger.info(f"Initialisation ShopifyHelper pour {store_url}")
        
        # Si on n'a pas de token mais qu'on a les clés client (Flux 2026)
        if not access_token and client_id and client_secret:
            logger.info("Récupération d'un token via Client Credentials")
            access_token = self._get_new_token(client_id, client_secret)
            
        self.access_token = access_token
        self.session = shopify.Session(self.store_url, '2025-01', self.access_token)
        shopify.ShopifyResource.activate_session(self.session)
        logger.info("Session Shopify activée avec succès")

    def _get_new_token(self, client_id, client_secret):
        """Récupère un jeton d'accès frais via le flux Client Credentials (2026)."""
        logger.info("Requête de token OAuth2 Client Credentials")
        url = f"https://{self.store_url}/admin/oauth/access_token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        }
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Échec token - Code: {response.status_code} - {response.text}")
            response.raise_for_status()
        
        logger.info("Token obtenu avec succès")
        return response.json().get("access_token")

    def get_collection_products(self, collection_id):
        """Récupère tous les IDs de produits d'une collection."""
        logger.info(f"Récupération des produits de la collection {collection_id}")
        products = shopify.Product.find(collection_id=collection_id)
        product_ids = [p.id for p in products]
        logger.info(f"Trouvé: {len(product_ids)} produits dans la collection")
        return product_ids

    def get_customer_purchase_history(self, customer_id):
        """Récupère tous les produits achetés par un client."""
        logger.debug(f"Récupération historique achat client {customer_id}")
        orders = shopify.Order.find(customer_id=customer_id, status='any')
        purchased_ids = set()
        for order in orders:
            for line_item in order.line_items:
                purchased_ids.add(line_item.product_id)
        logger.debug(f"Client {customer_id}: {len(purchased_ids)} produits achetés")
        return purchased_ids

    def get_eligible_customers(self, days_start=180, days_end=None, collection_id=None):
        """Trouve les clients ayant passé commande dans une plage de jours donnée."""
        if days_end is None:
            days_end = days_start
            
        date_start = (datetime.now() - timedelta(days=days_end)).strftime('%Y-%m-%d')
        date_end = (datetime.now() - timedelta(days=days_start)).strftime('%Y-%m-%d')
        
        logger.info(f"Recherche des commandes entre {date_start} et {date_end}")
        if collection_id:
            logger.info(f"  Filtre collection: {collection_id}")
        
        # Récupérer les commandes avec pagination
        orders = shopify.Order.find(
            created_at_min=f"{date_start}T00:00:00Z",
            created_at_max=f"{date_end}T23:59:59Z",
            status='any',
            limit=250
        )
        
        all_orders = []
        all_orders.extend(orders)
        
        while orders.has_next_page():
            orders = orders.next_page()
            all_orders.extend(orders)
            logger.info(f"Page suivante: {len(all_orders)} commandes récupérées au total")

        # On extrait les clients uniques qui ont acheté dans la collection cible si spécifiée
        customers = {}
        target_product_ids = self.get_collection_products(collection_id) if collection_id else None
        
        logger.info(f"Traitement de {len(all_orders)} commandes au total")
        
        for o in all_orders:
            if not o.customer or o.customer.id in customers:
                continue
                
            if target_product_ids:
                # Vérifier si un produit de la collection est dans CETTE commande
                has_target_product = any(item.product_id in target_product_ids for item in o.line_items)
                if not has_target_product:
                    continue
            
            customers[o.customer.id] = o.customer
        
        logger.info(f"Trouvé: {len(customers)} clients uniques éligibles")
        return list(customers.values())

    def update_customer_recommendations(self, customer_id, product_ids):
        """Met à jour les metafields et ajoute le tag de déclenchement."""
        logger.info(f"Mise à jour recommandations pour client {customer_id}")
        customer = shopify.Customer.find(customer_id)
        if not customer:
            logger.error(f"Client {customer_id} non trouvé")
            return False

        # On s'assure d'avoir exactement 3 recommandations (ou moins si on n'en a pas assez)
        reco_ids = product_ids[:3]
        recommendation_str = ",".join(map(str, reco_ids))
        logger.debug(f"Recommandations à injecter: {recommendation_str}")
        
        # Injection des recommandations dans un Metafield
        metafield = shopify.Metafield({
            'namespace': 'cross_sell',
            'key': 'next_recommendations',
            'value': recommendation_str,
            'type': 'single_line_text_field'
        })
        customer.add_metafield(metafield)
        logger.debug(f"Metafield créé pour client {customer_id}")
        
        # Ajout du Tag pour Shopify Flow
        tags = [t.strip() for t in customer.tags.split(',')] if customer.tags else []
        if 'trigger_reco' not in tags:
            tags.append('trigger_reco')
            customer.tags = ", ".join(tags)
            logger.debug(f"Tags mis à jour: {customer.tags}")
        
        # Sauvegarde unique pour tout envoyer (Metafield + Tags)
        if customer.save():
            logger.info(f"Recommandations ({recommendation_str}) injectées pour le client {customer_id}")
            return True
        else:
            logger.error(f"Erreur lors de la sauvegarde du client {customer_id}: {customer.errors.full_messages()}")
            return False
