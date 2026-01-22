import os
import requests
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration
STORE_URL = os.getenv("SHOPIFY_STORE_URL")
CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8081"
SCOPES = "read_orders,read_customers,write_customers,read_products"

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)
        
        print(f"\n[DEBUG] Requête reçue : {self.path}")
        print(f"[DEBUG] Paramètres : {query_components}")
        
        if "code" in query_components:
            code = query_components["code"][0]
            print(f"\n[+] Code d'installation reçu : {code}")
            
            # Échange du code contre un token permanent
            token_url = f"https://{STORE_URL}/admin/oauth/access_token"
            payload = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code
            }
            
            response = requests.post(token_url, json=payload)
            
            if response.status_code == 200:
                access_token = response.json().get("access_token")
                print(f"\n[!!!] VOTRE TOKEN PERMANENT : {access_token}")
                # Sauvegarde dans un fichier par sécurité
                with open("token.txt", "w") as f:
                    f.write(access_token)
                print("\nLe jeton a été sauvegardé dans azure_function/token.txt")
                
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h1>Succès !</h1><p>Token récupéré : <code>{access_token}</code></p><p>Vous pouvez fermer cette fenêtre et arrêter le script.</p>".encode("utf-8"))
            else:
                print(f"\n[!] Erreur lors de l'échange : {response.text}")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Erreur lors de l'echange du token.")
        else:
            print("[!] Le paramètre 'code' est manquant dans l'URL.")
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h1>Paramètres reçus</h1><pre>{query_components}</pre><p>Le code est absent. Shopify n'a pas encore validé l'installation.</p>".encode("utf-8"))

def run_server():
    server_address = ('', 8081)
    httpd = HTTPServer(server_address, OAuthHandler)
    
    # Générer l'URL d'installation
    install_url = (
        f"https://{STORE_URL}/admin/oauth/authorize?"
        f"client_id={CLIENT_ID}&"
        f"scope={SCOPES}&"
        f"redirect_uri={REDIRECT_URI}"
    )
    
    print("\n" + "="*50)
    print("SERVEUR D'AUTH SHOPIFY (LOCALHOST:8080)")
    print("="*50)
    print(f"\n1. Assurez-vous que l'URL de redirection '{REDIRECT_URI}' est configurée dans votre App Shopify.")
    print(f"2. Ouvrez cette URL pour démarrer l'installation :")
    print(f"\n{install_url}\n")
    
    # Tenter d'ouvrir le navigateur automatiquement
    webbrowser.open(install_url)
    
    print("En attente de la redirection...")
    httpd.handle_request() # Gère une seule requête puis s'arrête

if __name__ == "__main__":
    if not all([STORE_URL, CLIENT_ID, CLIENT_SECRET]):
        print("[!] Erreur : Veuillez configurer SHOPIFY_STORE_URL, CLIENT_ID et CLIENT_SECRET dans le fichier .env")
    else:
        run_server()
