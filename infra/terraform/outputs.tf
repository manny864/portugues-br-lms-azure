output "resource_group_name" {
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
