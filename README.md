# 🇧🇷 Sotaque Brasileiro — LMS de Portugués Brasileño (A1 a C2) para Hispanohablantes + Azure FinOps & Self-Hosted Runner

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
