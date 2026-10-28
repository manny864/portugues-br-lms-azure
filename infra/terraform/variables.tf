variable "project_name" {
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
