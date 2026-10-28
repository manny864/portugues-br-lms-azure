#!/usr/bin/env python3
"""
Script determinista para generar:
1. Infraestructura en Terraform (/infra/terraform/) bajo arquitectura FinOps/Serverless:
   - Azure Static Web Apps (Hosting HTML/CSS/JS + Managed Functions + Auth Entra ID/Google)
   - Azure Cosmos DB NoSQL en modo Serverless (con opción Free Tier)
   - Azure Blob Storage (Hot Tier) + Azure Front Door (CDN Global) para multimedia (.opus/.aac)
   - Azure AI Speech (Cognitive Services F0 Free Tier) para Pronunciation Assessment en pt-BR
   - GitHub Self-Hosted Runner ejecutándose en Azure (Azure Container Apps Serverless + opción ACI)
2. Contenedor Docker para el Self-Hosted Runner en Azure (/infra/runner-docker/)
3. Workflows CI/CD de GitHub Actions (/.github/workflows/)
4. Archivos de configuración del proyecto (.gitignore, .env.example, requirements.txt, README.md)
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TF_DIR = BASE_DIR / "infra" / "terraform"
RUNNER_DIR = BASE_DIR / "infra" / "runner-docker"
WF_DIR = BASE_DIR / ".github" / "workflows"
TMP_DIR = BASE_DIR / ".tmp"


PROVIDERS_TF = """terraform {
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
"""


VARIABLES_TF = """variable "project_name" {
  description = "Prefijo corto para los recursos del LMS de Portugués Brasileño"
  type        = string
  default     = "ptbrlms"
}

variable "environment" {
  description = "Entorno de despliegue (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Región principal de Azure para el grupo de recursos, Cosmos DB, Storage y Runner"
  type        = string
  default     = "eastus2"
}

variable "swa_location" {
  description = "Región soportada por Azure Static Web Apps (eastus2, centralus, westeurope, eastasia)"
  type        = string
  default     = "eastus2"
}

variable "swa_sku_tier" {
  description = "SKU de Azure Static Web Apps: 'Free' ($0/mes) o 'Standard' ($9/mes con SLA y Custom Auth)"
  type        = string
  default     = "Free"
}

variable "enable_cosmos_free_tier" {
  description = "Activar el Free Tier de Cosmos DB (1000 RU/s y 25 GB gratis de por vida). Nota: Solo se permite 1 por suscripción."
  type        = bool
  default     = false
}

variable "speech_sku" {
  description = "SKU de Azure AI Speech: 'F0' (Free Tier: 5h STT + 0.5M chars TTS neural pt-BR/mes) o 'S0'"
  type        = string
  default     = "F0"
}

variable "github_repo_owner" {
  description = "Usuario u organización propietaria del repositorio en GitHub"
  type        = string
  default     = "manny864"
}

variable "github_repo_name" {
  description = "Nombre del repositorio en GitHub donde se registrará el Self-Hosted Runner"
  type        = string
  default     = "portugues-br-lms-azure"
}

variable "github_pat" {
  description = "Personal Access Token (PAT) de GitHub con permisos 'repo' y 'workflow' para registrar automáticamente el Self-Hosted Runner en Azure"
  type        = string
  sensitive   = true
  default     = ""
}

variable "runner_deployment_mode" {
  description = "Modo de ejecución del Self-Hosted Runner en Azure: 'ACA' (Azure Container Apps con escalado FinOps) o 'ACI' (Azure Container Instances)"
  type        = string
  default     = "ACA"
}

variable "runner_image" {
  description = "Imagen Docker para el GitHub Actions Self-Hosted Runner con soporte de auto-registro via GITHUB_PAT / ACCESS_TOKEN"
  type        = string
  default     = "myoung34/github-runner:latest"
}

variable "tags" {
  description = "Etiquetas FinOps aplicadas a todos los recursos en Azure"
  type        = map(string)
  default = {
    Project      = "Sotaque-Brasileiro-LMS"
    Language     = "PT-BR"
    Architecture = "Serverless-FinOps"
    ManagedBy    = "Terraform"
  }
}
"""


MAIN_TF = """# ============================================================================
# 0. Sufijo Único y Grupo de Recursos Principal
# ============================================================================
resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
}

locals {
  name_prefix  = "${var.project_name}-${var.environment}-${random_string.suffix.result}"
  storage_name = lower(replace("${var.project_name}${var.environment}${random_string.suffix.result}", "-", ""))
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = var.tags
}

# ============================================================================
# 1. Hosting Web + API Backend + Auth Integrada: Azure Static Web Apps (SWA)
# ============================================================================
resource "azurerm_static_web_app" "lms_web" {
  name                = "swa-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.swa_location
  sku_tier            = var.swa_sku_tier
  sku_size            = var.swa_sku_tier

  app_settings = {
    "COSMOS_DB_ENDPOINT"  = azurerm_cosmosdb_account.lms_cosmos.endpoint
    "COSMOS_DB_KEY"       = azurerm_cosmosdb_account.lms_cosmos.primary_key
    "COSMOS_DB_DATABASE"  = azurerm_cosmosdb_sql_database.lms_db.name
    "COSMOS_DB_CONTAINER" = azurerm_cosmosdb_sql_container.user_progress.name
    "SPEECH_KEY"          = azurerm_cognitive_account.speech_ptbr.primary_access_key
    "SPEECH_REGION"       = azurerm_cognitive_account.speech_ptbr.location
    "MEDIA_CDN_ENDPOINT"  = "https://${azurerm_cdn_frontdoor_endpoint.media_cdn_ep.host_name}/media"
  }

  tags = var.tags
}

# ============================================================================
# 2. Base de Datos para el Progreso: Azure Cosmos DB (NoSQL Serverless)
# ============================================================================
resource "azurerm_cosmosdb_account" "lms_cosmos" {
  name                       = "cosmos-${local.name_prefix}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  offer_type                 = "Standard"
  kind                       = "GlobalDocumentDB"
  free_tier_enabled          = var.enable_cosmos_free_tier
  automatic_failover_enabled = false

  # Enfoque FinOps: Modo Serverless ($0 USD/mes en reposo, cobro solo por RU consumida)
  capabilities {
    name = "EnableServerless"
  }

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  tags = var.tags
}

resource "azurerm_cosmosdb_sql_database" "lms_db" {
  name                = "ptbrLmsDb"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.lms_cosmos.name
}

resource "azurerm_cosmosdb_sql_container" "user_progress" {
  name                  = "userProgress"
  resource_group_name   = azurerm_resource_group.main.name
  account_name          = azurerm_cosmosdb_account.lms_cosmos.name
  database_name         = azurerm_cosmosdb_sql_database.lms_db.name
  partition_key_paths   = ["/userId"]
  partition_key_version = 2

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
  }
}

# ============================================================================
# 3. Almacenamiento Multimedia (.opus / .aac / Imágenes): Azure Blob Storage
# ============================================================================
resource "azurerm_storage_account" "media" {
  name                     = substr(local.storage_name, 0, 24)
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  access_tier              = "Hot"
  min_tls_version          = "TLS1_2"

  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "HEAD", "OPTIONS"]
      allowed_origins    = ["*"]
      exposed_headers    = ["Content-Length", "Content-Type", "Content-Range"]
      max_age_in_seconds = 86400
    }
  }

  tags = var.tags
}

resource "azurerm_storage_container" "media_container" {
  name                  = "media"
  storage_account_name  = azurerm_storage_account.media.name
  container_access_type = "blob"
}

# ============================================================================
# 4. Entrega Global Multimedia y Caché: Azure Front Door (CDN Standard)
# ============================================================================
resource "azurerm_cdn_frontdoor_profile" "media_cdn" {
  name                = "afd-${local.name_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = "Standard_AzureFrontDoor"
  tags                = var.tags
}

resource "azurerm_cdn_frontdoor_endpoint" "media_cdn_ep" {
  name                     = "ep-${local.name_prefix}"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.media_cdn.id
}

resource "azurerm_cdn_frontdoor_origin_group" "media_origin_group" {
  name                     = "og-media-blob"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.media_cdn.id
  session_affinity_enabled = false

  load_balancing {
    sample_size                 = 4
    successful_samples_required = 3
  }
}

resource "azurerm_cdn_frontdoor_origin" "media_blob_origin" {
  name                          = "origin-blob-storage"
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.media_origin_group.id
  enabled                       = true

  certificate_name_check_enabled = true
  host_name                      = azurerm_storage_account.media.primary_blob_host
  origin_host_header             = azurerm_storage_account.media.primary_blob_host
  http_port                      = 80
  https_port                     = 443
  priority                       = 1
  weight                         = 1000
}

resource "azurerm_cdn_frontdoor_route" "media_route" {
  name                          = "route-media-cache"
  cdn_frontdoor_endpoint_id     = azurerm_cdn_frontdoor_endpoint.media_cdn_ep.id
  cdn_frontdoor_origin_group_id = azurerm_cdn_frontdoor_origin_group.media_origin_group.id
  cdn_frontdoor_origin_ids      = [azurerm_cdn_frontdoor_origin.media_blob_origin.id]
  enabled                       = true

  forwarding_protocol    = "HttpsOnly"
  https_redirect_enabled = true
  patterns_to_match      = ["/media/*"]
  supported_protocols    = ["Http", "Https"]

  cache {
    query_string_caching_behavior = "IgnoreQueryString"
    compression_enabled           = true
    content_types_to_compress     = ["application/json", "application/javascript", "text/css", "text/plain", "image/svg+xml"]
  }
}

# ============================================================================
# 5. Evaluación de Pronunciación y Voces Neuronales: Azure AI Speech (pt-BR)
#    Voces recomendadas: pt-BR-FranciscaNeural, pt-BR-AntonioNeural
# ============================================================================
resource "azurerm_cognitive_account" "speech_ptbr" {
  name                = "cog-speech-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "SpeechServices"
  sku_name            = var.speech_sku

  tags = var.tags
}
"""


RUNNER_TF = """# ============================================================================
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
"""


OUTPUTS_TF = """output "resource_group_name" {
  description = "Nombre del Resource Group creado en Azure"
  value       = azurerm_resource_group.main.name
}

output "static_web_app_default_hostname" {
  description = "URL pública del LMS desplegado en Azure Static Web Apps"
  value       = "https://${azurerm_static_web_app.lms_web.default_host_name}"
}

output "static_web_app_api_key" {
  description = "Deployment Token de Azure Static Web Apps (úsalo como secret AZURE_STATIC_WEB_APPS_API_TOKEN en GitHub)"
  value       = azurerm_static_web_app.lms_web.api_key
  sensitive   = true
}

output "cosmosdb_endpoint" {
  description = "Endpoint de Azure Cosmos DB Serverless"
  value       = azurerm_cosmosdb_account.lms_cosmos.endpoint
}

output "blob_storage_primary_endpoint" {
  description = "Endpoint directo del contenedor multimedia en Azure Blob Storage"
  value       = azurerm_storage_account.media.primary_blob_endpoint
}

output "frontdoor_cdn_media_url" {
  description = "URL global de Azure Front Door CDN para los audios (.opus/.aac) e imágenes de las lecciones"
  value       = "https://${azurerm_cdn_frontdoor_endpoint.media_cdn_ep.host_name}/media"
}

output "azure_speech_endpoint" {
  description = "Endpoint de Azure AI Speech para Pronunciation Assessment en pt-BR"
  value       = azurerm_cognitive_account.speech_ptbr.endpoint
}

output "self_hosted_runner_mode" {
  description = "Modo de despliegue activo para el Self-Hosted Runner en Azure"
  value       = var.runner_deployment_mode
}
"""


TFVARS_EXAMPLE = """# Copia este archivo a terraform.tfvars y define tu token de GitHub antes de ejecutar terraform apply
project_name            = "ptbrlms"
environment             = "prod"
location                = "eastus2"
swa_location            = "eastus2"
swa_sku_tier            = "Free"
enable_cosmos_free_tier = false
speech_sku              = "F0"
github_repo_owner       = "manny864"
github_repo_name        = "portugues-br-lms-azure"
runner_deployment_mode  = "ACA"

# Token PAT de GitHub con scope 'repo' y 'workflow' para registrar el Self-Hosted Runner en Azure:
# github_pat            = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
"""


RUNNER_DOCKERFILE = """# Imagen personalizada opcional para el Self-Hosted Runner de GitHub Actions en Azure
# Incluye GitHub Actions Runner + Azure CLI + Terraform + Node.js 20 + Python 3 + FFmpeg (para conversión a .opus)
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ARG RUNNER_VERSION="2.319.1"
ARG TERRAFORM_VERSION="1.9.5"

RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    ca-certificates \\
    git \\
    jq \\
    unzip \\
    gnupg \\
    lsb-release \\
    python3 \\
    python3-pip \\
    ffmpeg \\
    libicu70 \\
    && rm -rf /var/lib/apt/lists/*

# Instalar Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Instalar Terraform
RUN curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" -o terraform.zip \\
    && unzip terraform.zip -d /usr/local/bin \\
    && rm terraform.zip

# Crear usuario no-root para el runner
RUN useradd -m -s /bin/bash runner && mkdir -p /actions-runner && chown -R runner:runner /actions-runner

WORKDIR /actions-runner
USER runner

RUN curl -o actions-runner.tar.gz -L "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" \\
    && tar xzf ./actions-runner.tar.gz \\
    && rm actions-runner.tar.gz

COPY --chown=runner:runner entrypoint.sh /actions-runner/entrypoint.sh
RUN chmod +x /actions-runner/entrypoint.sh

ENTRYPOINT ["/actions-runner/entrypoint.sh"]
"""


RUNNER_ENTRYPOINT = """#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${REPO_URL:-}" || -z "${ACCESS_TOKEN:-}" ]]; then
  echo "ERROR: Debes definir REPO_URL y ACCESS_TOKEN (GitHub PAT)."
  exit 1
fi

OWNER_REPO=$(echo "${REPO_URL}" | sed -E 's#https://github.com/([^/]+/[^/]+).*#\\1#')
echo "Solicitando token de registro para el Self-Hosted Runner en ${OWNER_REPO}..."

REG_TOKEN=$(curl -sX POST \\
  -H "Accept: application/vnd.github+json" \\
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \\
  "https://api.github.com/repos/${OWNER_REPO}/actions/runners/registration-token" | jq -r .token)

./config.sh \\
  --url "${REPO_URL}" \\
  --token "${REG_TOKEN}" \\
  --name "${RUNNER_NAME:-azure-selfhosted-runner}" \\
  --labels "${LABELS:-self-hosted,azure,linux}" \\
  --work "${RUNNER_WORKDIR:-_work}" \\
  --unattended \\
  --replace

cleanup() {
  echo "Desregistrando runner de GitHub..."
  ./config.sh remove --unattended --token "${REG_TOKEN}" || true
}
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

./run.sh & wait $!
"""


WORKFLOW_DEPLOY_SWA = """name: Deploy PT-BR LMS to Azure Static Web Apps

on:
  push:
    branches:
      - main
  workflow_dispatch:
    inputs:
      runner_target:
        description: "Runner donde ejecutar el pipeline ('self-hosted' en Azure o 'ubuntu-latest')"
        required: false
        default: "ubuntu-latest"

jobs:
  validate_and_deploy:
    name: Validate Curriculum & Deploy to Azure SWA
    # Usa el self-hosted runner en Azure cuando se dispara manualmente con 'self-hosted', o ubuntu-latest por defecto
    runs-on: ${{ github.event.inputs.runner_target == 'self-hosted' && 'self-hosted' || 'ubuntu-latest' }}
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Validate Curriculum JSON & Regenerative Scripts
        run: |
          python3 scripts/generate_curriculum.py
          python3 scripts/generate_frontend.py
          python3 -m json.tool data/curriculum.json > /dev/null
          echo "Curriculum JSON validado correctamente."

      - name: Deploy to Azure Static Web Apps (si el token está configurado)
        if: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN != '' }}
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "/"
          api_location: "api"
          output_location: ""
          skip_app_build: true
"""


WORKFLOW_TERRAFORM = """name: Terraform Azure FinOps Infrastructure (Self-Hosted Runner Ready)

on:
  workflow_dispatch:
    inputs:
      action:
        description: "Acción de Terraform a ejecutar"
        required: true
        default: "plan"
        type: choice
        options:
          - validate
          - plan
          - apply
      use_azure_self_hosted:
        description: "Ejecutar en el Self-Hosted Runner alojado en Azure ([self-hosted, azure])"
        required: false
        default: false
        type: boolean

jobs:
  terraform:
    name: Terraform (${{ inputs.action }})
    runs-on: ${{ inputs.use_azure_self_hosted && 'self-hosted' || 'ubuntu-latest' }}
    defaults:
      run:
        working-directory: infra/terraform
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.5

      - name: Terraform Format Check & Init (Backend-less validation)
        run: |
          terraform fmt -check
          terraform init -backend=false
          terraform validate
"""


WORKFLOW_FINOPS_SHIFT_LEFT = """name: Costo de infraestructura (FinOps Shift-Left)

on:
  pull_request:

permissions:
  contents: read
  pull-requests: write # para comentar el impacto en el PR
  id-token: write      # azure/login con OIDC (credencial federada)

jobs:
  costo:
    name: FinOps Shift-Left
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_wrapper: false

      # El plan necesita credenciales de Azure para leer los bloques data y el estado.
      # Credencial federada de la app: subject repo:<organización>/<repo>:pull_request (con guion bajo).
      - uses: azure/login@v3 # OIDC: credencial federada de una app registration
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Generar el plan
        working-directory: infra/terraform
        env:
          ARM_USE_OIDC: "true"
          ARM_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          ARM_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          ARM_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
        run: |
          terraform init -input=false
          terraform plan -input=false -out=tfplan.bin
          terraform show -json tfplan.bin > tfplan.json

      - name: Estimar el costo (FinOps Shift-Left)
        uses: cscloudsolutions/azure-finops-action@v1
        with:
          api-key: ${{ secrets.FINOPS_API_KEY }} # API Key con el permiso write:shift-left
          tool: terraform
          plan-json: infra/terraform/tfplan.json
          api-url: https://finops.cscloudsolutions.com.ar
          script-sha256: 788ffa3bcedc1b413b316d356cf818361a74dade8df86caddde1c9843533b684
          threshold-usd: '300' # umbral de este workflow, en USD por mes
"""


GITIGNORE = """# Espacio temporal para datos intermedios
.tmp/
__pycache__/
*.py[cod]
.venv/
venv/

# Secretos, variables de entorno y credenciales OAuth
.env
.env.*
!.env.example
*credentials*.json
*client_secret*.json
*.pem
*.key

# Estado y artefactos de Terraform
**/.terraform/*
*.tfstate
*.tfstate.*
crash.log
crash.*.log
*.tfvars
!*.tfvars.example
override.tf
override.tf.json
*_override.tf
*_override.tf.json
.terraformrc
terraform.rc

# Node.js (Azure Functions API)
node_modules/
.DS_Store
"""


ENV_EXAMPLE = """# Variables de entorno para desarrollo local y despliegue en Azure
COSMOS_DB_ENDPOINT=https://cosmos-ptbrlms-prod.documents.azure.com:443/
COSMOS_DB_KEY=your_cosmos_primary_key_here
COSMOS_DB_DATABASE=ptbrLmsDb
COSMOS_DB_CONTAINER=userProgress

# Azure AI Speech (Pronunciation Assessment pt-BR)
SPEECH_KEY=your_azure_speech_f0_key_here
SPEECH_REGION=eastus2

# GitHub Personal Access Token para el Self-Hosted Runner en Azure
TF_VAR_github_pat=ghp_your_personal_access_token
"""


REQUIREMENTS_TXT = """# Dependencias deterministas de automatización y scripts locales
# Los generadores en /scripts usan la biblioteca estándar de Python 3.10+
"""


README_MD = """# 🇧🇷 Sotaque Brasileiro — LMS de Portugués Brasileño (A1 a C2) para Hispanohablantes + Azure FinOps & Self-Hosted Runner

Plataforma web educativa completa (LMS ligero tipo SPA) para el aprendizaje contrastivo de **Portugués Brasileño (PT-BR)** dirigida específicamente a hispanohablantes desde el nivel **A1 hasta C2**, construida con **HTML5 semántico, CSS3 (Tailwind CSS + variables nativas Dark/Light) y Vanilla JavaScript (ES6+ modular)**, e integrada con una arquitectura **100% Serverless y FinOps en Microsoft Azure** aprovisionada mediante **Terraform** (incluyendo un **GitHub Self-Hosted Runner ejecutándose en Azure**).

---

## 📁 Estructura del Proyecto

```text
.
├── index.html                        # Contenedor SPA principal (Dashboard, Lección, Imersão Real, Práctica Oral, Azure FinOps)
├── staticwebapp.config.json          # Configuración de rutas y Auth para Azure Static Web Apps
├── css/
│   └── styles.css                    # Estilos modernos (modo claro/oscuro, animaciones 3D flashcards, reproductor sincronizado)
├── data/
│   └── curriculum.json               # Currículo completo estructurado en 3 bloques (A1-A2, B1-B2, C1-C2)
├── js/
│   ├── auth.js                       # AuthService multiusuario (localStorage aislado + Azure SWA /.auth/me & Entra External ID)
│   ├── progress.js                   # ProgressService por usuario + sincronización con /api/progress (Cosmos DB)
│   ├── engine.js                     # Renderizador dinámico, reproductor 0.75x/1x/1.25x y los 5 motores de ejercicios
│   ├── curriculum-fallback.js        # Respaldo automático en módulo ES6 para ejecución offline o sin servidor
│   └── app.js                        # Orquestador SPA y navegación de vistas
├── api/
│   ├── package.json                  # Dependencias de Azure Functions (@azure/cosmos)
│   └── progress/
│       ├── function.json             # Bindings HTTP GET/POST para Azure Static Web Apps Managed Functions
│       └── index.js                  # Endpoint Serverless conectado a Azure Cosmos DB (particionado por /userId)
├── infra/
│   ├── terraform/                    # Infraestructura como Código (IaC) para Azure FinOps + Self-Hosted Runner
│   │   ├── providers.tf
│   │   ├── variables.tf
│   │   ├── main.tf                   # SWA, Cosmos DB Serverless, Blob Storage, Front Door CDN, Azure AI Speech (F0)
│   │   ├── runner.tf                 # Self-Hosted Runner de GitHub Actions en Azure Container Apps (ACA) / ACI
│   │   ├── outputs.tf
│   │   └── terraform.tfvars.example
│   └── runner-docker/                # Dockerfile y script de auto-registro para el Self-Hosted Runner en Azure
│       ├── Dockerfile
│       └── entrypoint.sh
├── directivas/                       # Documentación SOP viva del proyecto
│   ├── directiva_ejemplo.md
│   └── lms_ptbr_azure_SOP.md
├── scripts/                          # Generadores deterministas en Python
│   ├── generate_curriculum.py
│   ├── generate_frontend.py
│   └── generate_infra.py
└── .github/workflows/                # Pipelines CI/CD para Azure SWA y Terraform (compatibles con el Self-Hosted Runner)
    ├── deploy-azure-swa.yml
    └── terraform-infra.yml
```

---

## 🎯 Características Pedagógicas y Técnicas

1. **Enfoque Contrastivo Español ↔ Portugués Brasileño**:
   - **Falsos Amigos (*Falsos Cognatos*)**: Alertas visuales interactivas en cada nivel (*polvo, esquisito, propina, apelido, escritório, copo/vaso, embaraçada, oficina, presunto, borrar, prejuízo, assistir, estafa, lograr*).
   - **Fonética Contrastiva con Síntesis Nativa `pt-BR`**: Palatalización `/dʒi/` y `/tʃi/`, vocales abiertas `/ɛ/ /ɔ/` vs. cerradas `/e/ /o/`, sonidos nasales `ão / ões` y pronunciación de la `R` inicial/doble (`/h/`).
   - **Componente "Imersão Real"**: Reproductor con velocidades `0.75x`, `1x` y `1.25x`, transcripción interactiva sincronizada línea por línea (PT-BR / ES) y glosario de *gírias*.
2. **5 Motores de Ejercicios Interactivos en `js/engine.js`**:
   - `multiple-choice`: Con feedback inmediato anti-portuñol.
   - `fill-in-the-blanks`: Validación de conjugaciones (*Futuro do Subjuntivo*, *Infinitivo Pessoal*, *Crase*).
   - `audio-comprehension`: Comprensión auditiva con velocidad normal o lenta (`0.75x`).
   - `flashcards`: Tarjetas 3D con audio en `pt-BR` y seguimiento de dominio.
   - `speaking-prompt`: Práctica conversacional con micrófono mediante `Web Speech API` (`webkitSpeechRecognition` configurado en `pt-BR`) y modo de evaluación asistida.

---

## ☁️ Despliegue en Azure con Terraform (Incluyendo Self-Hosted Runner)

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edita terraform.tfvars y agrega tu github_pat para que el Self-Hosted Runner se registre automáticamente

terraform init
terraform plan
terraform apply
```

### Recursos creados por Terraform:
- **Azure Static Web App (`azurerm_static_web_app`)**: Hosting web + `/api/progress` Managed Function.
- **Azure Cosmos DB (`azurerm_cosmosdb_account`)**: Base de datos NoSQL en modo **Serverless** ($0 en reposo) con contenedor `userProgress` particionado por `/userId`.
- **Azure Storage Account + Azure Front Door CDN**: Almacenamiento Hot Tier y CDN global con compresión para servir audios `.opus`/`.aac` e imágenes.
- **Azure AI Speech (`F0` Free Tier)**: Servicio cognitivo para evaluación de pronunciación (`pt-BR`) y voces neuronales (*FranciscaNeural*, *AntonioNeural*).
- **GitHub Self-Hosted Runner en Azure (`runner.tf`)**: Desplegado sobre **Azure Container Apps (ACA)** (o **ACI**) con auto-registro contra este repositorio de GitHub y etiquetas `self-hosted,azure,linux,ptbr-lms,finops`.
"""


def main():
    TF_DIR.mkdir(parents=True, exist_ok=True)
    RUNNER_DIR.mkdir(parents=True, exist_ok=True)
    WF_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    # Terraform files
    (TF_DIR / "providers.tf").write_text(PROVIDERS_TF.strip() + "\n", encoding="utf-8")
    (TF_DIR / "variables.tf").write_text(VARIABLES_TF.strip() + "\n", encoding="utf-8")
    (TF_DIR / "main.tf").write_text(MAIN_TF.strip() + "\n", encoding="utf-8")
    (TF_DIR / "runner.tf").write_text(RUNNER_TF.strip() + "\n", encoding="utf-8")
    (TF_DIR / "outputs.tf").write_text(OUTPUTS_TF.strip() + "\n", encoding="utf-8")
    (TF_DIR / "terraform.tfvars.example").write_text(TFVARS_EXAMPLE.strip() + "\n", encoding="utf-8")

    # Docker Self-Hosted Runner files
    (RUNNER_DIR / "Dockerfile").write_text(RUNNER_DOCKERFILE.strip() + "\n", encoding="utf-8")
    ep_path = RUNNER_DIR / "entrypoint.sh"
    ep_path.write_text(RUNNER_ENTRYPOINT.strip() + "\n", encoding="utf-8")
    ep_path.chmod(0o755)

    # GitHub Workflows
    (WF_DIR / "deploy-azure-swa.yml").write_text(WORKFLOW_DEPLOY_SWA.strip() + "\n", encoding="utf-8")
    (WF_DIR / "terraform-infra.yml").write_text(WORKFLOW_TERRAFORM.strip() + "\n", encoding="utf-8")
    (WF_DIR / "finops-shift-left.yml").write_text(WORKFLOW_FINOPS_SHIFT_LEFT.strip() + "\n", encoding="utf-8")

    # Root configuration files
    (BASE_DIR / ".gitignore").write_text(GITIGNORE.strip() + "\n", encoding="utf-8")
    (BASE_DIR / ".env.example").write_text(ENV_EXAMPLE.strip() + "\n", encoding="utf-8")
    (BASE_DIR / "requirements.txt").write_text(REQUIREMENTS_TXT.strip() + "\n", encoding="utf-8")
    (BASE_DIR / "README.md").write_text(README_MD.strip() + "\n", encoding="utf-8")

    with open(TMP_DIR / "infra_validation.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "status": "ok",
                "terraformFiles": [
                    "infra/terraform/providers.tf",
                    "infra/terraform/variables.tf",
                    "infra/terraform/main.tf",
                    "infra/terraform/runner.tf",
                    "infra/terraform/outputs.tf",
                    "infra/terraform/terraform.tfvars.example"
                ],
                "runnerDockerFiles": [
                    "infra/runner-docker/Dockerfile",
                    "infra/runner-docker/entrypoint.sh"
                ],
                "workflows": [
                    ".github/workflows/deploy-azure-swa.yml",
                    ".github/workflows/terraform-infra.yml",
                    ".github/workflows/finops-shift-left.yml"
                ]
            },
            f,
            indent=2
        )


if __name__ == "__main__":
    main()
