import shopify

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
    print(f"Souscription de {email} au marketing...")
    
    # Mise à jour du consentement
    c.email_marketing_consent = {
        "state": "subscribed",
        "opt_in_level": "single_opt_in",
        "consent_updated_at": "2026-01-26T14:40:00Z"
    }
    c.accepts_marketing = True
    
    if c.save():
        print("SUCCÈS : Votre compte est maintenant ABONNÉ. Shopify Flow peut maintenant vous envoyer des e-mails.")
    else:
        print(f"ÉCHEC : {c.errors.full_messages()}")

shopify.ShopifyResource.clear_session()
