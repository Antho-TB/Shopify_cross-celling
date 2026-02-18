# 1. Variables de Structure (Projet et Environnement)
# Ces variables permettent de réutiliser le code pour différents projets ou environnements

variable "project" {
  type        = string
  description = "Nom du projet (ex: Shopify)"
  default     = "Shopify"
}

variable "feature" {
  type        = string
  description = "Nom de la fonctionnalité ou du module (ex: CrossSelling)"
  default     = "CrossSelling"
}

variable "environment" {
  type        = string
  description = "Environnement cible (dev, prod). 'dev' est utilisé pour la Sandbox."
  default     = "dev"
}

variable "location" {
  type        = string
  description = "Région Azure imposée par le prestataire (North Europe)"
  default     = "northeurope"
}

# 2. Secrets et Données Sensibles
# Le flag 'sensitive = true' empêche Terraform d'afficher les valeurs dans la console

variable "shopify_store_url" {
  type        = string
  description = "URL de la boutique Shopify (ex: tbgroupe-fr.myshopify.com)"
  sensitive   = true
}

variable "shopify_access_token" {
  type        = string
  description = "Token d'accès Admin API Shopify (shpca_...)"
  sensitive   = true
}
