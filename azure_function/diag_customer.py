import shopify
import json

import os
store_url = os.environ.get("SHOPIFY_STORE_URL")
access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")

session = shopify.Session(store_url, "2024-01", access_token)
shopify.ShopifyResource.activate_session(session)

email = "a.bezille@tb-groupe.fr"
customers = shopify.Customer.search(query=f"email:{email}")

if not customers:
    print(f"ERREUR : Client {email} non trouvé.")
else:
    c = customers[0]
    data = c.to_dict()
    print(f"--- DIAGNOSTIC CLIENT: {email} ---")
    print(json.dumps(data, indent=2))
    
    # Vérification explicite du consentement
    consent = data.get('email_marketing_consent', {})
    print(f"\nÉTAT DU CONSENTEMENT : {consent.get('state') if consent else 'Inconnu'}")

shopify.ShopifyResource.clear_session()
