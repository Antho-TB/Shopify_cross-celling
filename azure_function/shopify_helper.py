import shopify
import os
from datetime import datetime, timedelta

class ShopifyHelper:
    def __init__(self, store_url, access_token):
        self.store_url = store_url
        self.access_token = access_token
        self.session = shopify.Session(self.store_url, '2024-01', self.access_token)
        shopify.ShopifyResource.activate_session(self.session)

    def get_collection_products(self, collection_id):
        """Récupère tous les IDs de produits d'une collection."""
        products = shopify.Product.find(collection_id=collection_id)
        return [p.id for p in products]

    def get_customer_purchase_history(self, customer_id):
        """Récupère tous les produits achetés par un client."""
        orders = shopify.Order.find(customer_id=customer_id, status='any')
        purchased_ids = set()
        for order in orders:
            for line_item in order.line_items:
                purchased_ids.add(line_item.product_id)
        return purchased_ids

    def get_eligible_customers(self, days_ago=180):
        """Trouve les clients ayant passé commande il y a exactement X jours."""
        target_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        # On cherche les commandes créées ce jour là
        orders = shopify.Order.find(created_at_min=f"{target_date}T00:00:00Z", 
                                   created_at_max=f"{target_date}T23:59:59Z")
        return [o.customer for o in orders if o.customer]

    def update_customer_recommendations(self, customer_id, product_ids):
        """Met à jour les metafields et ajoute le tag de déclenchement."""
        customer = shopify.Customer.find(customer_id)
        
        # Injection des recommandations dans un Metafield
        # Format: "ID1,ID2,ID3" ou JSON
        recommendation_str = ",".join(map(str, product_ids))
        
        metafield = shopify.Metafield({
            'namespace': 'cross_sell',
            'key': 'next_recommendations',
            'value': recommendation_str,
            'type': 'single_line_text_field'
        })
        customer.add_metafield(metafield)
        
        # Ajout du Tag pour Shopify Flow
        if 'trigger_reco' not in customer.tags:
            customer.tags += ", trigger_reco"
            customer.save()
        
        return True
