# Directiva SOP: LMS Portugués Brasileño (PT-BR) para Hispanohablantes + Infraestructura Azure FinOps & Self-Hosted Runner

## 1. Objetivo
Construir una aplicación web educativa completa (LMS ligero tipo SPA) para enseñar Portugués Brasileño (PT-BR) a hispanohablantes desde el nivel A1 hasta C2, utilizando exclusivamente HTML5 semántico, CSS3 (Tailwind CSS + estilos personalizados sobrios inspirados en Brasil con modo oscuro/claro) y Vanilla JavaScript (ES6+ modular). Adicionalmente, aprovisionar mediante Terraform toda la infraestructura Serverless/FinOps en Azure (incluyendo un Self-Hosted Runner de GitHub Actions ejecutándose en Azure Container Apps) y publicar el código en un repositorio de GitHub.

## 2. Entradas (Inputs)
- Especificación pedagógica contrastiva Español vs. Portugués Brasileño (A1-A2, B1-B2, C1-C2).
- Requerimientos de los 5 motores de ejercicios interactivos (`multiple-choice`, `fill-in-the-blanks`, `audio-comprehension`, `flashcards`, `speaking-prompt` con `Web Speech API` `pt-BR` + síntesis neuronal de respaldo `speechSynthesis`).
- Diseño de arquitectura Azure Serverless & FinOps:
  - Azure Static Web Apps (Hosting + Managed Functions `/api/progress` + Auth SWA / Entra External ID).
  - Azure Cosmos DB Serverless / Free Tier (Base de datos NoSQL para progreso por `userId`).
  - Azure Blob Storage (Hot Tier, contenedor multimedia para audios `.opus`/`.aac` e imágenes con acceso mediante SAS / CDN).
  - Azure Front Door Standard/CDN Global (Entrega de baja latencia y protección anti-hotlinking).
  - Azure AI Speech Cognitive Services (`F0` Free Tier / `S0` con soporte para Pronunciation Assessment en `pt-BR`).
  - GitHub Self-Hosted Runner en Azure: Desplegado sobre **Azure Container Apps (ACA)** (o contenedor Docker con `actions/runner`) dentro de un entorno Serverless con escalado a 0 o 1 réplica bajo demanda para minimizar costos FinOps, además de soporte opcional para ACI/VM.

## 3. Lógica y Procedimiento Operativo Estándar (SOP)

### Fase A: Generación del Frontend SPA Modular y Datos (`/data`, `/js`, `/css`, `/api`)
1. **`index.html` y `/css/styles.css`**:
   - Crear una interfaz SPA responsiva con navegación lateral/superior, selector de tema (Modo Oscuro/Claro persistente), selector de usuario/sesión (Login/Registro modal y vista de perfil), y 4 vistas principales:
     1. **Dashboard de Progreso**: Estadísticas de racha, nivel actual CEFR (A1 a C2), porcentaje global, mapa de bloques, acceso rápido a falsos amigos y última lección reproducida.
     2. **Vista de Currículo y Módulo/Lección**: Renderizador dinámico de teoría contrastiva ES vs PT-BR, tabla de fonética con audio TTS nativo en `pt-BR`, tarjetas de alerta de **Falsos Amigos (Falsos Cognatos)**, componente **"Imersão Real"** y los 5 tipos de ejercicios interactivos.
     3. **Reproductor Cultural ("Imersão Real" Hub)**: Reproductor dedicado con control de velocidad (`0.75x`, `1x`, `1.25x`), barra de progreso interactiva, motor de audio dual (soporta archivos `.opus`/`.mp3` desde Azure Blob Storage/CDN y sintetizador multi-voz `pt-BR` integrado para que sea 100% funcional offline/inmediatamente), transcripción sincronizada línea por línea (PT-BR + traducción explicativa ES) y glosario de *gírias* (jerga brasileña).
     4. **Laboratorio de Práctica Conversacional & Fonética (`Speaking Lab`)**: Práctica guiada con micrófono (`webkitSpeechRecognition` / `SpeechRecognition` en `pt-BR`), comparación de similitud fonética/textual (distancia de Levenshtein + evaluación de palabras clave y preparación para Azure AI Speech Pronunciation Assessment).
2. **`/data/curriculum.json`**:
   - Estructurar los 3 bloques completos:
     - **Bloque Inicial (A1 - A2): Supervivencia y Cotidianidad** (Módulos A1 y A2, con lecciones completas jugables de saludos, fonética nasal `ão`/`ões`, `/dʒi/` y `/tʃi/`, verbos clave `ser/estar/ter/ir/fazer/poder`, pretérito perfeito, falsos amigos como *escritório, polvo, apelido, propina, esquisito* e inmersión musical Bossa Nova / MPB).
     - **Bloque Intermedio (B1 - B2): Fluidez y Espontaneidad** (Módulos B1 y B2, con lecciones completas jugables de contraste Perfeito vs Imperfeito, `Futuro do Subjuntivo` —*Quando você chegar, Se você quiser*—, colocación pronominal brasileña con próclise real, *gírias* laborales y cotidianas, falsos amigos como *embaraçada, borrar, oficina, presunto* e inmersión de Podcast Brasileño).
     - **Bloque Avanzado (C1 - C2): Dominio, Argumentación y Matices** (Módulos C1 y C2, con lecciones completas jugables de `Infinitivo Pessoal`, dominio de la **Crase** `à`/`àquelas`, voz pasiva y concordancia avanzada, argumentación ejecutiva/económica, falsos amigos cultos como *prejuízo, lograr, estafa, assistir* e inmersión de Debate / Serie Brasileña).
3. **`/js/auth.js` (`AuthService`)**:
   - Implementar gestión multiusuario con `async/await`.
   - Soportar modo Local (`localStorage` con múltiples perfiles aislados por ID/Email y usuario demo precargado) y modo Cloud Azure (`/.auth/me`, `/.auth/login/google`, `/.auth/login/aad` para Azure Static Web Apps + Microsoft Entra External ID).
4. **`/js/progress.js` (`ProgressService`)**:
   - Gestionar estado por usuario: `completedLessons`, `quizScores`, `exerciseAttempts`, `lastAudioPlayed`, `studyStreak`, `xpPoints`, `flashcardsMastered`.
   - Sincronizar automáticamente en `localStorage` por `userId` y exponer métodos `async syncWithCloud()` listos para realizar `fetch('/api/progress')` hacia Azure Functions + Cosmos DB.
5. **`/js/engine.js` (`CourseEngine`)**:
   - Orquestar el renderizado del JSON, el reproductor de audio personalizado (`0.75x`, `1x`, `1.25x`) con resaltado de transcripción sincronizada en tiempo real, y los validadores deterministas de los 5 tipos de ejercicios (`multiple-choice`, `fill-in-the-blanks`, `audio-comprehension`, `flashcards`, `speaking-prompt`).
6. **`/api/progress/index.js` (Azure Functions Backend Listo)**:
   - Incluir la Azure Function real para el directorio `/api` de Azure Static Web Apps que conecta con Azure Cosmos DB (`GET /api/progress` y `POST /api/progress`) y lee el header `x-ms-client-principal` de SWA Auth.

### Fase B: Infraestructura como Código en Terraform (`infra/terraform/`) + Self-Hosted Runner en Azure
1. Crear módulos y configuración limpia de Terraform (`providers.tf`, `variables.tf`, `main.tf`, `runner.tf`, `outputs.tf`, `terraform.tfvars.example`) y el `Dockerfile` + `entrypoint.sh` del runner en `infra/runner-docker/`:
   - **Resource Group**: Agrupador lógico con tags de FinOps (`Environment`, `Project`, `CostCenter`).
   - **Azure Static Web App (`azurerm_static_web_app`)**: Tier Free/Standard para alojar el frontend y las Managed Functions.
   - **Azure Cosmos DB (`azurerm_cosmosdb_account`, `azurerm_cosmosdb_sql_database`, `azurerm_cosmosdb_sql_container`)**: Modo `Serverless` (y opción de `enable_free_tier`) con partition key `/userId`.
   - **Azure Storage Account & Blob Container (`azurerm_storage_account`, `azurerm_storage_container`)**: Hot Tier con CORS configurado para servir archivos multimedia `.opus`, `.m4a` e imágenes.
   - **Azure Front Door CDN (`azurerm_cdn_frontdoor_profile`, `azurerm_cdn_frontdoor_endpoint`, `azurerm_cdn_frontdoor_origin_group`, `azurerm_cdn_frontdoor_origin`, `azurerm_cdn_frontdoor_route`)**: CDN global delante del Blob Storage para caché de audio/multimedia y ahorro de Data Egress.
   - **Azure AI Speech (`azurerm_cognitive_account`)**: `kind = "SpeechServices"`, SKU `F0` (Free Tier) para evaluación de pronunciación (`pt-BR`) y voces neuronales.
   - **Self-Hosted GitHub Runner en Azure (`runner.tf`)**:
     - Implementado sobre **Azure Container Apps (`azurerm_container_app` + `azurerm_container_app_environment` + `azurerm_log_analytics_workspace`)** y opción alternativa con **Azure Container Instances (`azurerm_container_group`)**, utilizando la imagen de GitHub Actions Runner (`ghcr.io/actions/actions-runner` / contenedor custom con Terraform, Azure CLI y Node.js) que se registra automáticamente en el repositorio de GitHub mediante `github_pat` / token de registro y ejecuta los workflows con `runs-on: [self-hosted, azure]`.

### Fase C: Creación del Repositorio en GitHub y Despliegue de Código
1. Inicializar repositorio Git local con `.gitignore` seguro (excluyendo `.tmp/`, `.env`, `.terraform/`, `*.tfstate*`, credenciales OAuth).
2. Crear el repositorio remoto en GitHub (`portugues-br-lms-azure`) mediante `gh repo create` y hacer push de toda la estructura, incluyendo workflows de GitHub Actions (`.github/workflows/deploy-azure-swa.yml` y `.github/workflows/terraform-infra.yml` configurados para usar el self-hosted runner o `ubuntu-latest`).

## 4. Salidas (Outputs)
- Aplicación web completa en la raíz del proyecto (`index.html`, `css/styles.css`, `js/auth.js`, `js/progress.js`, `js/engine.js`, `js/app.js`, `data/curriculum.json`).
- Backend Serverless en `api/progress/` para Azure Static Web Apps + Cosmos DB.
- Infraestructura Terraform completa en `infra/terraform/` y Docker del Self-Hosted Runner en `infra/runner-docker/`.
- Workflows CI/CD en `.github/workflows/`.
- Repositorio publicado en GitHub.

## 5. Restricciones y Casos Borde (Memoria Viva)
- *Nota sobre ES Modules y CORS local:* Si un usuario abre `index.html` directamente con `file://`, el navegador puede bloquear `fetch('./data/curriculum.json')` o módulos ES6 por políticas CORS. Para evitar que la app falle si se abre sin servidor HTTP local, además de escribir `/data/curriculum.json` como archivo puro e independiente, proveeremos un fallback automático en memoria o carga resiliente en `engine.js` para que funcione tanto en un servidor web (Azure SWA / `python3 -m http.server`) como abriendo el archivo localmente.
- *Nota sobre Audios Multimedia sin conexión a Azure Blob:* Para que las lecciones y el reproductor "Imersão Real" funcionen desde el segundo cero antes de subir MP3/Opus reales a Azure Blob Storage, el reproductor de `engine.js` debe intentar reproducir el archivo multimedia de Azure CDN y, si es un placeholder o aún no existe el blob, activar automáticamente un motor de **Síntesis de Voz Nativa Brasileña (`Web Speech API` `speechSynthesis` `pt-BR`) con temporizador sincronizado a velocidad `0.75x`, `1x` y `1.25x`** que lee los diálogos y letras en portugués mientras ilumina la transcripción interactiva línea por línea.
- *Nota sobre Web Speech API (`SpeechRecognition`):* `webkitSpeechRecognition` está disponible en Chrome/Edge/Safari modernos. En navegadores sin soporte de micrófono o sin permisos concedidos, el componente `speaking-prompt` debe ofrecer un modo de simulación/autoevaluación fonética asistida para nunca bloquear el progreso del estudiante.
- *Nota sobre Azure Cosmos DB Free Tier en Terraform:* Solo se permite 1 cuenta con `free_tier_enabled = true` por suscripción de Azure. Nota: No hacer uso de `enable_free_tier` en `azurerm_cosmosdb_account`, porque causa warning de deprecación en `azurerm >= 3.110` y se elimina en `v4.0`. En su lugar, usar `free_tier_enabled = var.enable_cosmos_free_tier`.
- *Nota sobre Azure Front Door (`azurerm_cdn_frontdoor_route`):* No hacer inclusión de tipos MIME de audio comprimido (`audio/ogg`, `audio/opus`, `audio/mp4`) en `content_types_to_compress`, porque causa error de validación del esquema en el proveedor `azurerm` (los formatos `.opus` y `.aac` ya están comprimidos en el origen). En su lugar, incluir únicamente tipos compresibles en borde soportados por Azure Front Door (`application/json`, `application/javascript`, `text/css`, `text/plain`, `image/svg+xml`).

