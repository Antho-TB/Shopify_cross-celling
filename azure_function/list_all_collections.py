import shopify
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_all_collections():
    """
    Récupère toutes les collections Shopify et génère un fichier de résultats.
    """
    store_url = os.getenv("SHOPIFY_STORE_URL")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    client_id = os.getenv("SHOPIFY_CLIENT_ID")
    client_secret = os.getenv("SHOPIFY_CLIENT_SECRET")

    if not store_url or not (access_token or (client_id and client_secret)):
        print("✗ Erreur: Variables .env manquantes (SHOPIFY_STORE_URL et token requis).")
        return

    # Initialiser la session
    if not access_token and client_id and client_secret:
        # Récupérer un token frais
        import requests
        url = f"https://{store_url}/admin/oauth/access_token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            access_token = response.json().get("access_token")
        else:
            print(f"✗ Erreur lors de la récupération du token: {response.text}")
            return

    session = shopify.Session(store_url, '2025-01', access_token)
    shopify.ShopifyResource.activate_session(session)

    print(f"Recuperation de toutes les collections depuis {store_url}...\n")

    try:
        # Récupérer toutes les collections via GraphQL
        import requests
        
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        query = """
        {
            collections(first: 250) {
                edges {
                    node {
                        id
                        title
                        handle
                        description
                    }
                }
            }
        }
        """
        
        url = f"https://{store_url}/admin/api/2025-01/graphql.json"
        response = requests.post(url, json={'query': query}, headers=headers)
        
        if response.status_code != 200:
            print(f"✗ Erreur API: {response.status_code} - {response.text}")
            return
        
        data = response.json()
        if 'errors' in data:
            print(f"✗ Erreur GraphQL: {data['errors']}")
            return
        
        collections = [edge['node'] for edge in data.get('data', {}).get('collections', {}).get('edges', [])]
        
        if not collections:
            print("⚠ Aucune collection trouvée.")
            return

        # Préparer le contenu du fichier
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append(f"LISTE COMPLÈTE DES COLLECTIONS SHOPIFY")
        output_lines.append(f"Store: {store_url}")
        output_lines.append(f"Généré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append("=" * 80)
        output_lines.append("")
        output_lines.append(f"Total: {len(collections)} collection(s)\n")
        
        # Ajouter les détails de chaque collection
        for i, collection in enumerate(collections, 1):
            output_lines.append(f"{i}. {collection.get('title', 'N/A')}")
            output_lines.append(f"   ID: {collection.get('id')}")
            output_lines.append(f"   Handle: {collection.get('handle')}")
            if collection.get('description'):
                desc = collection.get('description')[:100]
                output_lines.append(f"   Description: {desc}...")
            output_lines.append("")
        
        # Ajouter un résumé en CSV pour facile import
        output_lines.append("\n" + "=" * 80)
        output_lines.append("FORMAT CSV (pour copie facile):")
        output_lines.append("=" * 80)
        output_lines.append("Titre,ID,Handle")
        for collection in collections:
            # Extraire juste le numérique de l'ID GraphQL
            collection_id = collection.get("id", "").split("/")[-1]
            output_lines.append(f'"{collection.get("title")}",{collection_id},"{collection.get("handle")}"')

        # Écrire dans le fichier
        filename = "collections_list.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(output_lines))

        print(f"✓ {len(collections)} collection(s) trouvee(s)!\n")
        print("Détails:")
        print("-" * 80)
        for i, collection in enumerate(collections, 1):
            collection_id = collection.get('id', '').split("/")[-1]
            print(f"{i:2}. [{collection_id:>12}] {collection.get('title', 'N/A'):<40} ({collection.get('handle')})")
        
        print(f"✓ Fichier genere: {filename}")

    except Exception as e:
        print(f"✗ Erreur lors de la récupération des collections: {e}")

if __name__ == "__main__":
    get_all_collections()
