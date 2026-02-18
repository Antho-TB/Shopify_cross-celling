# 1. Variables Locales (Calculées)
# Les 'locals' servent à transformer des variables ou à créer des constantes complexes
locals {
  # Convention de nommage imposée : Prefix-Project-FeatureName-Environnement
  # On construit ici la base du nom qui sera déclinée pour chaque ressource
  base_name = "${var.project}-${var.feature}-${var.environment}"

  # Adaptation pour le Storage Account (Azure n'accepte ni tirets ni majuscules pour les comptes de stockage)
  storage_name = lower(replace("${var.project}${var.feature}${var.environment}", "-", ""))

  # Tags obligatoires à appliquer sur toutes les ressources pour le suivi (FinOps)
  tags = {
    deployment = "terraform"       # Indique la méthode de création
    project    = var.project       # Lien avec le projet Shopify
    feature    = var.feature       # Lien avec le module Cross-Selling
    env        = var.environment   # Environnement 'dev' pour Sandbox
  }
}
