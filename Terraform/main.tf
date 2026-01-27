# 1. Groupe de Ressources (Resource Group)
# C'est le conteneur logique pour toutes les ressources du projet
resource "azurerm_resource_group" "rg" {
  name     = "rg-${local.base_name}"
  location = var.location
  tags     = local.tags
}

# 2. Compte de Stockage (Storage Account)
# Requis par Azure Functions pour stocker le code et les logs internes
resource "azurerm_storage_account" "st" {
  name                     = "st${local.storage_name}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS" # Local Redundancy (moins cher pour dev)
  tags                     = local.tags
}

# 3. Plan de Service (App Service Plan)
# Définit la puissance de calcul allouée à la fonction
resource "azurerm_service_plan" "plan" {
  name                = "asp-${local.base_name}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux" # On utilise Python sur Linux
  sku_name            = "Y1"    # Mode 'Consumption' (on ne paye qu'à l'exécution) - Quota débloqué par l'admin
  tags                = local.tags
}

# 4. L'Application de Fonction (Linux Function App)
# C'est ici que votre code Python sera réellement hébergé
resource "azurerm_linux_function_app" "func" {
  name                = "func-${local.base_name}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  storage_account_name       = azurerm_storage_account.st.name
  storage_account_access_key = azurerm_storage_account.st.primary_access_key
  service_plan_id            = azurerm_service_plan.plan.id

  site_config {
    application_stack {
      python_version = "3.11" # Version recommandée pour la stabilité
    }
  }

  # Configuration des variables d'environnement (similaire au fichier .env local)
  app_settings = {
    "SHOPIFY_STORE_URL"    = var.shopify_store_url
    "SHOPIFY_ACCESS_TOKEN" = var.shopify_access_token
  }

  tags = local.tags
}

# 5. Sorties (Outputs)
# Permet d'afficher les informations utiles à la fin du déploiement
output "function_app_name" {
  value = azurerm_linux_function_app.func.name
}

output "function_app_default_hostname" {
  value = "https://${azurerm_linux_function_app.func.default_hostname}"
}
