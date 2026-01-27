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
        """Récupère tous les produits d'une collection avec détails (ID, Titre, Handle, Image, Prix)."""
        logger.info(f"Récupération des produits de la collection {collection_id}")
        products = shopify.Product.find(collection_id=collection_id)
        
        product_data = {}
        for p in products:
            image_url = p.images[0].src if p.images else ""
            # On récupère le prix du premier variant
            price = p.variants[0].price if p.variants else "0.00"
            
            product_data[p.id] = {
                "id": p.id,
                "title": p.title,
                "handle": p.handle,
                "image_url": image_url,
                "price": price,
                "url": f"https://{self.store_url}/products/{p.handle}"
            }
            
        logger.info(f"Trouvé: {len(product_data)} produits dans la collection")
        return product_data

    def get_collection_url(self, collection_id):
        """Récupère l'URL d'une collection Shopify par son ID."""
        logger.info(f"Récupération URL de la collection {collection_id}")
        try:
            # Essayer d'abord avec CustomCollection
            collection = shopify.CustomCollection.find(collection_id)
            if not collection:
                # Puis avec SmartCollection
                collection = shopify.SmartCollection.find(collection_id)
            
            if collection:
                return f"https://{self.store_url}/collections/{collection.handle}"
        except Exception as e:
            logger.warning(f"Impossible de trouver la collection {collection_id}: {str(e)}")
            
        return f"https://{self.store_url}"

    def get_product_names(self, product_ids):
        """Traduit une liste d'IDs en noms de produits."""
        if not product_ids: return []
        names = []
        for pid in product_ids:
            try:
                p = shopify.Product.find(pid)
                names.append(p.title) if p else names.append(str(pid))
            except:
                names.append(str(pid))
        return names

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

    def get_customer_by_email(self, email):
        """Recherche un client par e-mail."""
        import shopify
        customers = shopify.Customer.search(query=f"email:{email}")
        if customers:
            return customers[0]
        return None

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
        eligible_entries = []
        seen_customers = set()
        target_product_ids = self.get_collection_products(collection_id) if collection_id else None
        
        logger.info(f"Traitement de {len(all_orders)} commandes au total")
        
        for o in all_orders:
            if not o.customer or o.customer.id in seen_customers:
                continue
                
            # --- VÉRIFICATION RGPD / CONSENTEMENT ---
            # On ne récupère que les clients ayant explicitement accepté le marketing (SUBSCRIBED)
            consent = getattr(o.customer, 'email_marketing_consent', {})
            is_subscribed = False
            if isinstance(consent, dict):
                is_subscribed = consent.get('state') == 'subscribed'
            elif hasattr(consent, 'state'):
                is_subscribed = consent.state == 'subscribed'
            
            # Secours sur le champ classique 'accepts_marketing' si l'objet de consentement est vide
            if not is_subscribed:
                is_subscribed = getattr(o.customer, 'accepts_marketing', False)

            if not is_subscribed:
                logger.debug(f"Client {o.customer.email} sauté (Non abonné au marketing)")
                continue
            # ----------------------------------------

            triggering_product_name = "N/A"
            if target_product_ids:
                # Trouver quel produit de la collection est dans CETTE commande
                trigger_item = next((item for item in o.line_items if item.product_id in target_product_ids), None)
                if not trigger_item:
                    continue
                triggering_product_name = trigger_item.title
            
            seen_customers.add(o.customer.id)
            eligible_entries.append({
                "customer": o.customer,
                "purchase_date": o.created_at[:10],
                "purchased_product": triggering_product_name
            })
        
        logger.info(f"Trouvé: {len(eligible_entries)} clients uniques éligibles")
        return eligible_entries

    def update_customer_recommendations(self, customer_id, product_ids, manual_names=None, manual_data=None, collection_url=None):
        """Met à jour les metafields (JSON + Texte + Link) et ajoute le tag de déclenchement."""
        logger.info(f"Mise à jour recommandations pour client {customer_id}")
        customer = shopify.Customer.find(customer_id)
        if not customer:
            logger.error(f"Client {customer_id} non trouvé")
            return False

        # 1. Version texte Riche (Noms + Prix) - LE PLUS STABLE
        reco_items = manual_data if manual_data else [manual_names[i] for i in range(len(product_ids[:3]))]
        # Si on n'a pas manual_data, on essaye de construire une chaîne propre
        if manual_data:
            reco_names_with_prices = [f"{item['title']} ({item['price']} €)" for item in manual_data]
        else:
            reco_names_with_prices = manual_names if manual_names else self.get_product_names(product_ids[:3])
            
        recommendation_str = " • " + " • ".join(reco_names_with_prices)
        
        # 2. Version JSON (Pour le futur)
        new_metafields = [
            shopify.Metafield({
                'namespace': 'cross_sell',
                'key': 'next_recommendations',
                'value': recommendation_str,
                'type': 'single_line_text_field'
            }),
            shopify.Metafield({
                'namespace': 'cross_sell',
                'key': 'reco_data',
                'value': json.dumps(reco_json_data, ensure_ascii=False),
                'type': 'json'
            })
        ]

        if collection_url:
            new_metafields.append(shopify.Metafield({
                'namespace': 'cross_sell',
                'key': 'collection_url',
                'value': collection_url,
                'type': 'single_line_text_field'
            }))

        # 3. Gestion du Trigger (Double save pour s'assurer que le tag est "nouveau")
        current_tags = [t.strip() for t in customer.tags.split(',')] if customer.tags else []
        
        if 'trigger_reco' in current_tags:
            current_tags.remove('trigger_reco')
            customer.tags = ", ".join(current_tags)
            customer.save()
            customer = shopify.Customer.find(customer_id)
        
        # On rajoute le tag
        tags = [t.strip() for t in customer.tags.split(',')] if customer.tags else []
        if 'trigger_reco' not in tags:
            tags.append('trigger_reco')
        customer.tags = ", ".join(tags)
        
        # Injection finale des metafields
        for meta in new_metafields:
            customer.add_metafield(meta)
        
        return customer.save()
