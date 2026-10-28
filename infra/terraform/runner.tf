# ============================================================================
# 6. Self-Hosted GitHub Actions Runner Ejecutándose en Azure
#    Diseñado bajo principios FinOps:
#    - Opción A (Default: 'ACA'): Azure Container Apps en Consumption Plan
#      (pago por segundo de vCPU/RAM, auto-reparación y secretos seguros).
#    - Opción B ('ACI'): Azure Container Instances para ejecución directa.
# ============================================================================

resource "azurerm_log_analytics_workspace" "runner_logs" {
  name                = "law-runner-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_container_app_environment" "runner_env" {
  count                      = var.runner_deployment_mode == "ACA" ? 1 : 0
  name                       = "cae-runner-${local.name_prefix}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.runner_logs.id
  tags                       = var.tags
}

# Opción A: GitHub Self-Hosted Runner en Azure Container Apps (ACA)
resource "azurerm_container_app" "github_runner" {
  count                        = var.runner_deployment_mode == "ACA" ? 1 : 0
  name                         = "ca-gh-runner-${random_string.suffix.result}"
  container_app_environment_id = azurerm_container_app_environment.runner_env[0].id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = var.tags

  secret {
    name  = "github-access-token"
    value = var.github_pat != "" ? var.github_pat : "REPLACE_WITH_GITHUB_PAT"
  }

  template {
    min_replicas = 1
    max_replicas = 2

    container {
      name   = "github-actions-runner"
      image  = var.runner_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "REPO_URL"
        value = "https://github.com/${var.github_repo_owner}/${var.github_repo_name}"
      }
      env {
        name  = "RUNNER_NAME"
        value = "azure-aca-runner-${random_string.suffix.result}"
      }
      env {
        name  = "RUNNER_SCOPE"
        value = "repo"
      }
      env {
        name  = "LABELS"
        value = "self-hosted,azure,linux,ptbr-lms,finops"
      }
      env {
        name  = "RUNNER_WORKDIR"
        value = "/tmp/github-runner"
      }
      env {
        name  = "EPHEMERAL"
        value = "false"
      }
      env {
        name        = "ACCESS_TOKEN"
        secret_name = "github-access-token"
      }
    }
  }
}

# Opción B: GitHub Self-Hosted Runner en Azure Container Instances (ACI)
resource "azurerm_container_group" "github_runner_aci" {
  count               = var.runner_deployment_mode == "ACI" ? 1 : 0
  name                = "aci-gh-runner-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  restart_policy      = "Always"
  tags                = var.tags

  container {
    name   = "github-runner"
    image  = var.runner_image
    cpu    = "1.0"
    memory = "2.0"

    environment_variables = {
      REPO_URL       = "https://github.com/${var.github_repo_owner}/${var.github_repo_name}"
      RUNNER_NAME    = "azure-aci-runner-${random_string.suffix.result}"
      RUNNER_SCOPE   = "repo"
      LABELS         = "self-hosted,azure,linux,ptbr-lms,aci"
      RUNNER_WORKDIR = "/tmp/github-runner"
    }

    secure_environment_variables = {
      ACCESS_TOKEN = var.github_pat != "" ? var.github_pat : "REPLACE_WITH_GITHUB_PAT"
    }

    ports {
      port     = 443
      protocol = "TCP"
    }
  }
}
