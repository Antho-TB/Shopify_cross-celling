import os
import shopify
from dotenv import load_dotenv
from shopify_helper import ShopifyHelper

load_dotenv()

def test_real_update():
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    
    # Client Jacques Matthys identifié précédemment
    customer_id = 8555203330200
    
    # Recommandations calculées pour lui
    recos = [7945003565208, 7921645256856, 7921645191320]

    helper = ShopifyHelper(store_url, access_token=access_token)
    
    print(f"--- Mise à jour réelle du client {customer_id} ---")
    
    success = helper.update_customer_recommendations(customer_id, recos)
    
    if success:
        print("\n✅ Succès ! Les Metafields et le tag 'trigger_reco' ont été ajoutés.")
        print("Vérifiez la fiche client dans votre administration Shopify.")
    else:
        print("\n❌ Échec de la mise à jour.")

if __name__ == "__main__":
    test_real_update()
