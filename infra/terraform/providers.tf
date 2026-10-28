terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Descomenta este bloque si deseas almacenar el tfstate en Azure Blob Storage remoto:
  # backend "azurerm" {
  #   resource_group_name  = "rg-tfstate-ptbr"
  #   storage_account_name = "sttfstateptbrlms"
  #   container_name       = "tfstate"
  #   key                  = "ptbr-lms.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}
