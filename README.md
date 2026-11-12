# Sistema Inteligente de Gestión Ciudadana y Ventanilla Virtual PQRSD
### Alcaldía Distrital de Barranquilla — Distrito Especial, Industrial y Portuario

Plataforma integral de atención al ciudadano y gestión pública distrital basada en un **Sistema Multiagente con LangGraph**, un **RAG Estructurado con Base de Datos Vectorial**, integración segura vía **Model Context Protocol (MCP) con Snowflake**, y doble motor de inteligencia artificial (**Groq Cloud ultrarrápido** y **Ollama local $0 offline**).

---

## 🏛️ 1. Arquitectura Técnica y Herramientas Utilizadas

El sistema fue diseñado bajo estándares de gobierno digital, principios de seguridad de menor privilegio y cumplimiento estricto del marco legal colombiano (**Ley 1755 de 2015** que regula el derecho fundamental de petición y el **Código de Procedimiento Administrativo y de lo Contencioso Administrativo - CPACA**).

```
                      ┌────────────────────────────────────────┐
                      │    Ciudadano / Funcionario Público     │
                      └───────────────────┬────────────────────┘
                                          │
                   HTTPS / WebSocket / Real-Time Event Sync
                                          │
                      ┌───────────────────▼────────────────────┐
                      │    Frontend Institucional (React 18)   │
                      │   - Ventanilla Virtual Ciudadana       │
                      │   - Consola Distrital de Funcionarios  │
                      │   - Comprobante Digital Imprimible     │
                      └───────────────────┬────────────────────┘
                                          │  API REST
                      ┌───────────────────▼────────────────────┐
                      │         FastAPI Backend Server         │
                      │      (Uvicorn ASGI • Puerto 8000)      │
                      └───────────────────┬────────────────────┘
                                          │
                      ┌───────────────────▼────────────────────┐
                      │        Orquestador LangGraph           │
                      │   StateGraph con 12 Nodos Autónomos    │
                      └─┬──────────────┬──────────────┬──────┬─┘
                        │              │              │      │
  ┌─────────────────────▼─┐ ┌──────────▼────────┐ ┌───▼──────▼────────┐
  │  StructuredVectorDB   │ │ Herramientas (8)  │ │ Doble Motor LLM   │
  │  - 384-dim Embeddings │ │ - search_knowledge│ │ 1. Groq Cloud     │
  │  - Similitud Coseno   │ │ - classify_request│ │    (gpt-oss-120b) │
  │  - Metadatos 2026     │ │ - validate_fields │ │ 2. Ollama Local   │
  │  - Cero Alucinaciones │ │ - case_management │ │    (qwen2.5 /     │
  │  - Boost de Entidades │ │ - escalate_human  │ │     llama3)       │
  └───────────────────────┘ └───────────────────┘ └───────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │                                                     │
┌───────────▼──────────────────────────┐  ┌───────────────────────▼────────────────┐
│   Base de Datos SQLite (Persistente) │  │  Servidor Snowflake MCP & Conector     │
│   - Tabla Casos y Solicitudes        │  │  - BARRANQUILLA_CITIZEN_DB (Cloud)     │
│   - Auditoría y Logs de Estado       │  │  - Rol de Solo Lectura y Menor Priv.   │
│   - Biblioteca Normativa Curada      │  │  - Sincronización Bidireccional        │
└──────────────────────────────────────┘  └────────────────────────────────────────┘
```

### Detalle de Tecnologías y Componentes:

| Componente | Tecnología | Propósito |
|---|---|---|
| **Orquestación Multiagente** | `LangGraph >= 1.2.0` | Grafo de estados (`StateGraph`) que ejecuta ciclos de vida completos: recepción, interpretación, RAG, clasificación, validación, aclaración, radicación y verificación. |
| **RAG Vectorial Estructurado** | `StructuredVectorDB` (`NumPy` + `SQLite`) | Recuperación semántica de alta precisión con matriz densa de 384 dimensiones, indexación de hechos normativos distritales 2026, requisitos, plazos y canales oficiales. |
| **Motor de Inferencia Primario** | `Groq Cloud` (`openai/gpt-oss-120b`) | Generación en lenguaje natural en menos de 2 segundos, con alta calidez, empatía caribeña y 100% apego a la normativa distrital. |
| **Motor de Inferencia Secundario** | `Ollama Local` (`qwen2.5:0.5b` / `llama3`) | Operación 100% offline y autónoma con costo de \$0 para contingencias o despliegues sin conexión a internet. |
| **Integración Cloud Data Warehouse** | `Snowflake MCP Server` + `snowflake-connector-python` | Conexión e interoperabilidad con Snowflake (`BARRANQUILLA_CITIZEN_DB`) bajo el principio de menor privilegio (`BQL_CITIZEN_READONLY_ROLE`). |
| **Servidor de Aplicación y API** | `FastAPI >= 0.115` + `Uvicorn` | API REST asíncrona de alto rendimiento que sirve los endpoints distritales y sirve el frontend de producción en un único puerto. |
| **Extracción y Parseo Documental** | `PyMuPDF (fitz) >= 1.24` | Ingesta, parseo y segmentación de resoluciones, decretos y documentos PDF de la Alcaldía. |
| **Frontend Institucional** | `React 18` + `Vite` + `TailwindCSS v4` | Interfaz institucional con la identidad visual oficial de la Alcaldía de Barranquilla, sincronización en tiempo real y generación de comprobantes imprimibles. |

---

## 🛠️ 2. Herramientas Operativas del Agente

El agente no es un simple chatbot de conversación libre; es un **agente resolutivo** que ejecuta 8 herramientas especializadas:

1. **`search_knowledge`**: Recupera fragmentos de la base vectorial estructurada con código de documento, vigencia, entidad distrital y citas legales verificadas.
2. **`classify_request`**: Analiza el texto del ciudadano y lo clasifica automáticamente en la taxonomía distrital (Hacienda, Gestión Social / Sisbén, Alumbrado K-YENA, Control Urbano, Salud Pública, Secretaría General).
3. **`validate_required_fields`**: Valida los campos obligatorios para cada trámite y solicita aclaración cortés al ciudadano en caso de datos faltantes (dirección, teléfono, código de poste, etc.).
4. **`create_case_draft`**: Formaliza la solicitud en la base de datos asignando el número oficial de radicado (`BQL-2026-XXXXX`), token de seguridad criptográfico y plazo reglamentario de atención (SLA).
5. **`get_case_status`**: Consulta en tiempo real el expediente de una solicitud, su dependencia asignada, historial de actuaciones y alertas de vencimiento de términos legales.
6. **`escalate_to_human`**: Activa salvaguardas de gobernanza y ética institucional cuando se detectan indicios de irregularidades, cohecho, solicitudes de dinero por tramitadores o disputas complejas, trasladando el caso a un funcionario humano.
7. **`query_analytics`**: Genera métricas de gestión pública, distribución por dependencias y porcentajes de efectividad en cumplimiento de plazos.
8. **`generate_report`**: Sintetiza reportes ejecutivos exportables en CSV para comités directivos de la Alcaldía.

---

## 📂 3. Estructura del Repositorio

```text
aereonexAI/
├── Dockerfile                         # Contenedor unificado multi-stage (Node 22 + Python 3.12)
├── docker-compose.yml                 # Orquestación de servicios (App Unificada + Ollama)
├── .dockerignore                      # Filtros de exclusión para imágenes Docker livianas
├── .env.example                       # Plantilla de variables de entorno
├── .env                               # Configuración activa del entorno
├── README.md                          # Guía completa de arquitectura, instalación y uso
├── data_barranquilla.db               # Base de datos relacional y vectorial SQLite
├── backend/
│   ├── main.py                        # Punto de entrada unificado FastAPI + SPA Frontend
│   ├── requirements.txt               # Dependencias de Python certificadas
│   ├── app/
│   │   ├── agent/                     # Motor LangGraph (Grafo, Nodos, Estado, Cliente LLM)
│   │   │   ├── graph.py               # Definición del flujo StateGraph de 12 nodos
│   │   │   ├── state.py               # Esquema de memoria tipado (AgentState)
│   │   │   └── llm_client.py          # Cliente multi-proveedor (Groq 120B + Ollama fallback)
│   │   ├── api/                       # Controladores y rutas REST (Chat, Casos, Snowflake, Analítica)
│   │   │   ├── routes_agent.py        # Endpoint de mensajería con el agente
│   │   │   ├── routes_cases.py        # Gestión de radicados y estados
│   │   │   ├── routes_snowflake.py    # Conexión, prueba y sincronización con Snowflake
│   │   │   ├── routes_analytics.py    # KPIs y tableros de control
│   │   │   └── routes_knowledge.py    # Explorador de biblioteca normativa
│   │   ├── core/                      # Configuración y base de datos
│   │   │   ├── config.py              # Variables de configuración con Pydantic Settings
│   │   │   ├── database.py            # Modelos ORM SQLAlchemy
│   │   │   ├── seed_data.py           # Catálogos de dependencias y trámites
│   │   │   ├── snowflake_schema.sql   # Script DDL oficial para Snowflake Snowsight
│   │   │   └── snowflake_sync.py      # Sincronizador de casos a Snowflake
│   │   ├── mcp/                       # Servidor MCP (Model Context Protocol) para Snowflake
│   │   │   └── snowflake_server.py    # Herramientas de solo lectura y consulta MCP
│   │   ├── rag/                       # Base de datos vectorial estructurada
│   │   │   ├── structured_vector_db.py# Base vectorial densa con trámites 2026 curados
│   │   │   ├── vector_store.py        # Almacén híbrido clásico
│   │   │   ├── parser.py              # Extractor de texto en PDFs con PyMuPDF
│   │   │   ├── chunker.py             # Fragmentador semántico
│   │   │   └── ingest_all.py          # Pipeline de ingesta masiva de resoluciones
│   │   └── tools/                     # Las 8 herramientas funcionales del agente
│   └── tests/
│       └── test_faq_and_flows.py      # Suite automatizada de 11 pruebas (100% PASS)
├── frontend/                          # Interfaz de usuario React + Vite
│   ├── package.json                   # Dependencias de Node.js
│   ├── vite.config.js                 # Configuración de empaquetado Vite
│   ├── src/
│   │   ├── App.jsx                    # Contenedor raíz y pie de página institucional
│   │   ├── index.css                  # Estilos y temas de la Alcaldía
│   │   └── components/
│   │       ├── Header.jsx             # Cabecera institucional con insignia distrital
│   │       ├── CitizenPortal.jsx      # Ventanilla virtual para ciudadanos con chips FAQ
│   │       ├── AdminDashboard.jsx     # Consola administrativa sincronizada en tiempo real
│   │       ├── CaseTrackerModal.jsx   # Modal de consulta rápida de estado de radicado
│   │       └── ComprobanteModal.jsx   # Comprobante digital oficial descargable e imprimible
│   └── dist/                          # Compilado de producción servido por FastAPI
```

---

## 🐳 4. Despliegue con Docker y Docker Compose (Recomendado)

El proyecto incluye un **contenedor Docker unificado multi-stage** que compila el frontend en Node.js, empaqueta el backend en Python 3.12 y levanta tanto la Ventanilla Virtual Ciudadana como la Consola Administrativa y la API REST en un solo contenedor liviano y seguro.

### Requisitos Previos
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y en ejecución en Windows, Linux o macOS.
* Soporte para `docker compose`.

---

### Opción 1: Despliegue Completo con Docker Compose (App + Ollama)

Este comando levanta la aplicación unificada y el servicio local de Ollama en una red aislada:

```bash
# 1. Clonar el repositorio y ubicarse en la raíz
cd aereonexAI

# 2. Configurar variables de entorno (copiar la plantilla)
cp .env.example .env

# 3. Construir y levantar todos los servicios en segundo plano
docker compose up -d --build
```

#### Servicios Levantados:
* **Ventanilla Virtual y API (App Unificada):** `http://localhost:8000/`
* **Documentación Interactiva Swagger:** `http://localhost:8000/docs`
* **Verificación de Salud (Healthcheck):** `http://localhost:8000/health`
* **Motor Ollama Local ($0):** `http://localhost:11434/`

Para ver los registros en tiempo real:
```bash
docker compose logs -f barranquilla-agente
```

Para detener los contenedores:
```bash
docker compose down
```

---

### Opción 2: Ejecutar Solo el Contenedor de la Aplicación (Modo Standalone)

Si prefieres ejecutar únicamente el contenedor de la aplicación utilizando **Groq Cloud** para la inferencia rápida de IA:

```bash
# 1. Construir la imagen Docker
docker build -t barranquilla-agente:latest .

# 2. Ejecutar el contenedor pasando tu clave de Groq
docker run -d \
  --name barranquilla-agente-app \
  -p 8000:8000 \
  -e GROQ_API_KEY="tu_clave_groq_aqui" \
  -e GROQ_MODEL="openai/gpt-oss-120b" \
  -e SNOWFLAKE_ACCOUNT="PIHDEYB-PR83338" \
  -e SNOWFLAKE_USER="BQL_MCP_READER" \
  -e SNOWFLAKE_PASSWORD="tu_password_seguro" \
  -v barranquilla-data:/app \
  barranquilla-agente:latest
```

El aplicativo estará listo inmediatamente en `http://localhost:8000/`.

---

## 💻 5. Instalación y Ejecución Local (Sin Docker)

Si deseas ejecutar el proyecto directamente en tu máquina host para desarrollo activo:

### Requisitos del Sistema
* **Python 3.10 o superior** (certificado en Python 3.12 y 3.13).
* **Node.js 18 o superior** y gestor `npm`.

### Paso 1: Configurar el Backend
```bash
# 1. Crear y activar entorno virtual
python -m venv venv

# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

# 2. Instalar dependencias requeridas
pip install --upgrade pip
pip install -r backend/requirements.txt

# 3. Inicializar base de datos y catálogo oficial de Barranquilla
python -m backend.app.core.seed_data

# 4. Iniciar servidor FastAPI (backend)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Paso 2: Iniciar el Frontend (en otra terminal)
```bash
cd frontend
npm install
npm run dev
```
* **Frontend de desarrollo:** `http://127.0.0.1:5173/`
* **Backend API:** `http://127.0.0.1:8000/`

*(Nota: En modo producción, puedes ejecutar `npm run build` dentro de `frontend/` y el servidor FastAPI en el puerto 8000 servirá el frontend automáticamente sin requerir el proceso dev de Vite).*

---

## ❄️ 6. Conexión a Snowflake (MCP y Snowsight)

El sistema soporta persistencia e interoperabilidad analítica con **Snowflake Cloud**, cumpliendo con las mejores prácticas de seguridad de la industria (principio de menor privilegio y cuentas de solo consulta).

### Opción A: Despliegue en Snowsight Worksheets (Recomendado)
1. Inicia sesión en tu cuenta de Snowflake en [app.snowflake.com](https://app.snowflake.com).
2. Ve al menú lateral **Projects → Worksheets → `+ Worksheet`**.
3. Abre el archivo [`backend/app/core/snowflake_schema.sql`](file:///c:/Users/Camco/aereonexAI/backend/app/core/snowflake_schema.sql) de este repositorio o descárgalo directamente desde el endpoint: `http://localhost:8000/api/snowflake/download_sql`.
4. Pega todo el contenido en la hoja de trabajo.
5. Selecciona todo (`Ctrl + A`) y presiona el botón **Run** (`Ctrl + Enter`).
6. El script creará automáticamente:
   * Base de datos: `BARRANQUILLA_CITIZEN_DB`
   * Almacén de cómputo: `COMPUTE_WH`
   * Esquemas lógicos: `RAW`, `CURATED`, `OPERATIONS`, `ANALYTICS`, `GOVERNANCE`.
   * Rol de menor privilegio: `BQL_CITIZEN_READONLY_ROLE` (permisos exclusivos de `USAGE` y `SELECT`, sin permisos de administrador).
   * Usuario de consulta: `BQL_MCP_READER`.

### Opción B: Sincronización desde la Consola Administrativa
1. Abre la **Consola Distrital** en `http://localhost:8000/` y selecciona la pestaña **"Conexión Snowflake"**.
2. Verifica tu identificador de cuenta (ej. `PIHDEYB-PR83338`) y usuario `BQL_MCP_READER`.
3. Haz clic en **"Probar y Guardar Conexión"**.
4. Haz clic en **"Sincronizar Casos a Snowflake"** para transferir en tiempo real todas las solicitudes radicadas.

---

## 🧪 7. Suite de Pruebas Automatizadas (11 de 11 Aprobadas)

El proyecto cuenta con una suite de pruebas exhaustiva que valida el RAG estructurado, la ausencia de símbolos markdown ruidosos, el cumplimiento de salvaguardas y el funcionamiento de los trámites:

```bash
python backend/tests/test_faq_and_flows.py
```

### Resultados de la Suite:

| Test | Caso de Prueba | Validación Realizada | Resultado |
|:---:|---|---|:---:|
| **1** | FAQ Sisbén IV | Consulta requisitos sin forzar radicación de caso ni solicitar datos de dirección. | **100% PASS** |
| **2** | FAQ Descuentos Predial 2026 | Verifica citas exactas: 10% hasta 31 marzo 2026 y 5% hasta 31 mayo 2026. | **100% PASS** |
| **3** | FAQ Paz y Salvo Predial | Explica trámite 100% digital, gratuito y con Referencia Catastral. | **100% PASS** |
| **4** | FAQ Alumbrado K-YENA | Orienta canales de atención, código de poste y tiempos SLA (48-72h). | **100% PASS** |
| **5** | FAQ Espacio Público | Informa marco normativo contra invasión de andenes y talleres en vía. | **100% PASS** |
| **6** | Radicación Completa (Happy Path) | Genera radicado `BQL-2026-XXXXX`, código digital de verificación y SLA. | **100% PASS** |
| **7** | Validación de Campos Faltantes | Solicita educadamente teléfono o dirección cuando el ciudadano intenta radicar sin ellos. | **100% PASS** |
| **8** | Consulta de Estado de Caso | Recupera el historial de actuaciones oficiales para el radicado emitido. | **100% PASS** |
| **9** | Salvaguarda de Gobernanza | Detecta palabras sensibles (dinero, cohecho, tramitador) y escala a humano. | **100% PASS** |
| **10** | Filtro de Alcance Institucional | Declina cortésmente temas ajenos a la Alcaldía (recetas, código, tareas). | **100% PASS** |
| **11** | Verificación Snowflake | Comprueba conectividad bajo el principio de menor privilegio. | **100% PASS** |

---

## 📋 8. Catálogo Oficial de Trámites y Hechos Clave 2026

La base de datos vectorial estructurada contiene la información normativa oficial vigente para el Distrito de Barranquilla:

* **Impuesto Predial Unificado (Hacienda Distrital):**
  * `10% de descuento`: Pago total hasta el 31 de marzo de 2026.
  * `5% de descuento`: Pago total entre el 1 de abril y el 31 de mayo de 2026.
  * `Pago sin descuento ni sanción`: Hasta el 30 de junio de 2026.
  * `Intereses moratorios`: A partir del 1 de julio de 2026.
  * `Paz y Salvo`: Gratuito, descarga digital inmediata en PDF con código QR ingresando la Referencia Catastral (15 a 30 dígitos).
* **Sisbén IV (Secretaría de Gestión Social):**
  * Trámite gratuito sin intermediarios.
  * Requiere cédula de ciudadanía del jefe de hogar y documentos de identidad de todos los miembros del hogar + recibo de servicio público reciente.
  * Visita domiciliaria de verificación: 15 a 30 días hábiles.
* **Alumbrado Público (K-YENA):**
  * Reportes de bombillas apagadas, postes caídos o luminarias intermitentes.
  * Tiempo reglamentario de atención técnica: 48 a 72 horas hábiles.
  * Canales: Línea 195, conmutador distrital y ventanilla virtual.
* **Control Urbano y Espacio Público (Secretaría de Control Urbano):**
  * Prohibición de ocupación de andenes peatonales con talleres mecánicos, venta ambulante no autorizada o depósito de escombros.
  * Inspección ocular y remoción: 10 a 15 días hábiles.
* **Salud Ambiental (Secretaría Distrital de Salud):**
  * Prevención y control del mosquito transmisor del dengue (*Aedes aegypti*).
  * Inspección larvaria y jornadas de fumigación comunitaria.

---

## 🛡️ 9. Gobernanza, Privacidad y Licencia

* **Protección de Datos:** Cumplimiento de la Ley Estatutaria 1581 de 2012 de Protección de Datos Personales en Colombia.
* **Decisiones Humanas en el Bucle (Human-in-the-loop):** Las decisiones de fondo sobre sanciones, exoneraciones tributarias o cierres policivos están reservadas legalmente a funcionarios públicos titulados. El agente asiste en la recepción, preclasificación, orientación ciudadana y estructuración formal del expediente.
* **Licencia:** Plataforma desarrollada para el Distrito Especial, Industrial y Portuario de Barranquilla.
