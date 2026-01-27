# 1. Valeurs des Variables
# Ce fichier contient les valeurs réelles transmises aux variables définies dans variables.tf
# Note : Dans une vraie pipeline CI/CD, ces valeurs seraient injectées dynamiquement.

project     = "Shopify"
feature     = "CrossSelling"
environment = "dev" # Utilisé pour le déploiement sur l'abonnement Sandbox

# 2. Utilisation des Tokens @#{...}#@
# Conformément au guide du prestataire, on utilise des tokens qui seront remplacés
# par les secrets stockés dans GitHub Actions lors du déploiement.
shopify_store_url    = "@#{SHOPIFY_STORE_URL}#@"
shopify_access_token = "@#{SHOPIFY_ACCESS_TOKEN}#@"
