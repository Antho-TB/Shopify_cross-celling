import os
import shopify
from dotenv import load_dotenv

load_dotenv()

def cleanup_test_tag():
    store_url = os.environ.get("SHOPIFY_STORE_URL")
    access_token = os.environ.get("SHOPIFY_ACCESS_TOKEN")
    test_email = os.environ.get("TEST_CUSTOMER_EMAIL", "a.bezille@tb-groupe.fr")

    if not store_url or not access_token:
        print("Erreur: Config Shopify manquante")
        return

    session = shopify.Session(store_url, "2024-01", access_token)
    shopify.ShopifyResource.activate_session(session)

    print(f"Recherche du client {test_email}...")
    customers = shopify.Customer.search(query=f"email:{test_email}")
    
    if not customers:
        print(f"Client {test_email} non trouvé.")
        return

    customer = customers[0]
    tags = [t.strip() for t in customer.tags.split(',')] if customer.tags else []
    
    if 'trigger_reco' in tags:
        print(f"Tag 'trigger_reco' trouvé sur {customer.email}. Suppression...")
        tags.remove('trigger_reco')
        customer.tags = ", ".join(tags)
        if customer.save():
            print("Tag supprimé avec succès !")
        else:
            print("Échec de la suppression du tag.")
    else:
        print(f"Le tag 'trigger_reco' n'est pas présent sur le compte {customer.email}.")

if __name__ == "__main__":
    cleanup_test_tag()
