from shopify_helper import ShopifyHelper
import os
from dotenv import load_dotenv

load_dotenv()

def test_forged_premium_relance():
    """
    Test de relance pour les clients ayant acheté un couteau 
    de la collection "Forgé Premium" il y a entre 6 et 12 mois.
    """
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    client_id = os.getenv("SHOPIFY_CLIENT_ID")
    client_secret = os.getenv("SHOPIFY_CLIENT_SECRET")
    # Collection ID pour "Forgé Premium" - à définir en variable d'env
    collection_id = os.getenv("FORGED_PREMIUM_COLLECTION_ID")

    if not all([store_url, collection_id]) or not (access_token or (client_id and client_secret)):
        print("Erreur: Variables .env manquantes (store_url, collection_id, et token ou duo ID/Secret requis).")
        return

    helper = ShopifyHelper(store_url, access_token=access_token, client_id=client_id, client_secret=client_secret)

    print(f"--- Test Relance Forgé Premium (6-12 mois) pour {store_url} ---\n")
    
    # 1. Récupérer les produits de la collection "Forgé Premium"
    try:
        product_ids = helper.get_collection_products(collection_id)
        print(f"✓ {len(product_ids)} produits trouvés dans la collection 'Forgé Premium' ({collection_id})\n")
    except Exception as e:
        print(f"✗ Erreur API (Collection): {e}")
        return

    # 2. Chercher les clients ayant acheté ENTRE 6 et 12 mois
    # days_end = 180 jours (6 mois) en arrière
    # days_start = 365 jours (12 mois) en arrière
    days_start = 365  # 12 mois
    days_end = 180    # 6 mois
    
    try:
        eligible_customers = helper.get_eligible_customers(
            days_start=days_start, 
            days_end=days_end, 
            collection_id=collection_id
        )
        print(f"✓ {len(eligible_customers)} clients trouvés ayant acheté entre 6-12 mois\n")
        
        if len(eligible_customers) == 0:
            print("ℹ Aucun client trouvé pour cette période. Vérifiez les dates.")
            return
            
    except Exception as e:
        print(f"✗ Erreur API (Clients): {e}")
        return

    # 3. Traiter chaque client pour calculer les recommandations
    print("=" * 70)
    print(f"{'Client':<40} {'Email':<30} {'Recos':<20}")
    print("=" * 70)
    
    total_recos_sent = 0
    
    for i, customer in enumerate(eligible_customers, 1):
        try:
            # Récupérer l'historique d'achat du client
            purchase_history = helper.get_customer_purchase_history(customer.id)
            
            # Calculer les recommandations : produits de la collection non achetés
            recommendations = [pid for pid in product_ids if pid not in purchase_history][:3]
            
            customer_name = f"{customer.first_name or ''} {customer.last_name or ''}".strip()
            recos_str = f"{len(recommendations)} produits" if recommendations else "Aucun"
            
            print(f"{customer_name:<40} {customer.email:<30} {recos_str:<20}")
            
            if recommendations:
                print(f"  └─ Produits recommandés: {recommendations}")
                total_recos_sent += 1
            else:
                print(f"  └─ ⚠ Client a déjà acheté tous les produits de la collection")
                
        except Exception as e:
            print(f"  ✗ Erreur lors du traitement du client {customer.id}: {e}")
    
    print("=" * 70)
    print(f"\n📊 Résumé:")
    print(f"  • Clients éligibles (6-12 mois): {len(eligible_customers)}")
    print(f"  • Clients avec recommandations disponibles: {total_recos_sent}")
    print(f"  • Clients ayant tous les produits: {len(eligible_customers) - total_recos_sent}")

if __name__ == "__main__":
    test_forged_premium_relance()
