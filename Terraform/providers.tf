# 1. Configuration de Terraform et des Providers
# Ce bloc définit les versions minimales requises et les sources des plugins (providers)
terraform {
  required_version = ">= 1.5.0" # Version minimale de Terraform à utiliser

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm" # Plugin officiel pour Microsoft Azure
      version = "~> 3.0"             # Utilise une version compatible 3.x
    }
  }
}

# 2. Configuration du Provider Azure
# Ce bloc permet d'indiquer comment Terraform doit se connecter à Azure
provider "azurerm" {
  features {} # Requis par le provider azurerm même si vide
}
