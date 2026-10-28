# ============================================================================
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
