# Arquitectura Técnica — Agente Inteligente de Gestión Ciudadana
**Alcaldía Distrital de Barranquilla (Atlántico, Colombia)**

## 1. Visión General
El **Agente Inteligente de Gestión Ciudadana** es un sistema multiagente autónomo supervisado diseñado para transformar la atención ciudadana y la recepción de solicitudes y PQRSD en la Alcaldía Distrital de Barranquilla. A diferencia de un chatbot conversacional convencional, este sistema implementa un ciclo operativo completo: interpreta peticiones en lenguaje natural, recupera evidencia normativa mediante RAG semántico híbrido, clasifica con base en la taxonomía institucional, valida requisitos obligatorios, crea radicados con trazabilidad inmutable y escala a funcionarios humanos bajo reglas de gobernanza.

---

## 2. Diagrama de Flujo del Grafo Operativo (LangGraph)

```
                       [INICIO: Solicitud Ciudadana]
                                    │
                                    ▼
                         [Nodo de Interpretación]
                         • Extracción de entidades (dirección, barrio, teléfono, id)
                         • Detección de disparadores sensibles (corrupción, disputas)
                                    │
                                    ▼
                         [Nodo de Planificación]
                         • Definición dinámica de secuencia de tareas
                                    │
                                    ▼
                        [Nodo de Recuperación RAG]
                         • Búsqueda híbrida (Ollama nomic-embed-text + BM25)
                         • Cita de fuentes con hash SHA-256 y vigencia 2026
                                    │
                                    ▼
                        [Nodo de Clasificación]
                         • Mapeo a dependencia oficial (Alumbrado, Hacienda, etc.)
                         • Asignación de prioridad y plazo legal SLA
                                    │
                                    ▼
                        [Nodo de Validación]
                         • Comprobación de campos obligatorios según catálogo
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
          ¿Es consulta informativa?          ¿Es radicación de caso?
                  │                                   │
                  │                      ┌────────────┴────────────┐
                  │                      ▼                         ▼
                  │              ¿Faltan requisitos?       ¿Requisitos completos?
                  │                      │                         │
                  │                      ▼                         ▼
                  │            [Aclaración Ciudadano]     ¿Requiere intervención?
                  │            • Pide datos faltantes              │
                  │                                        ┌───────┴───────┐
                  │                                        ▼               ▼
                  │                                       [SÍ]            [NO]
                  │                                        │               │
                  │                                        ▼               ▼
                  │                              [Escalamiento Humano] [Ejecución Caso]
                  │                              • Cola de aprobación   • Radicado BQL-
                  │                              • Prioridad ALTA       • Evento auditoría
                  │                                        │               │
                  └──────────────────────┬─────────────────┴───────────────┘
                                         ▼
                             [Nodo de Verificación]
                             • Control de calidad de respuesta
                             • Verificación de citas y descargo institucional
                                         │
                                         ▼
                                       [FIN]
```

---

## 3. Modelo de Datos y Capas Lógicas Snowflake
El sistema fue diseñado para operar nativamente en **Snowflake** y se ejecuta localmente mediante una capa SQLite 100% compatible bajo las 5 capas de gobernanza de datos:

| Capa Lógica | Tablas / Objetos | Contenido y Propósito |
| :--- | :--- | :--- |
| **RAW** | `raw_documents`, `ingestion_log` | Texto original extraído, URLs de origen, tamaño en bytes, checksum SHA-256 y registro de ingesta. |
| **CURATED** | `curated_documents`, `document_chunks`, `departments`, `procedures`, `requirements` | Documentos oficiales depurados, fragmentos con vectores embeddings de 768 dimensiones, catálogo de dependencias distritales y campos obligatorios. |
| **OPERATIONS** | `cases`, `case_events`, `classifications`, `approvals` | Registros transaccionales de casos con radicado `BQL-2026-XXXXX`, historial inmutable de eventos, clasificaciones asistidas y cola de intervención humana. |
| **ANALYTICS** | `daily_case_metrics`, `sla_metrics` | Vistas agregadas para KPIs, control de vencimiento de términos legales según CPACA y balance de carga por dependencia. |
| **GOVERNANCE** | `source_registry`, `access_audit`, `model_evals` | Registro de fuentes oficiales autorizadas, auditoría de accesos e invocaciones al modelo y registro de pruebas de fidelidad. |

---

## 4. Pipeline RAG Semántico Híbrido
1. **Extracción Multiformato:** PyMuPDF (`pymupdf`) para documentos PDF oficiales y analizador semántico de Markdown.
2. **Chunking Estructurado:** Segmentación orientada a artículos jurídicos y títulos normativos preservando artículos, decretos y resoluciones.
3. **Embeddings 100% Locales ($0):** Modelo `nomic-embed-text` servido a través del runtime local de Ollama (768 dimensiones).
4. **Búsqueda Híbrida:** Ponderación 70% semántica (similitud coseno) + 30% léxica (coincidencia de términos clave BM25).
5. **Citas Formales:** Cada respuesta orientativa incluye código documental, artículo, entidad responsable, enlace al portal distrital y porcentaje de similitud.

---

## 5. Salvaguardas de Seguridad y Human-in-the-Loop
- **Entorno Sandbox Institucional:** Todos los casos creados en esta versión piloto se identifican expresamente como radicaciones de prueba demostrativa, evitando afirmaciones de radicación oficial vinculante sin convenios institucionales.
- **Detección de Disparadores Sensibles:** Palabras clave de alto riesgo (denuncias de soborno, corrupción, tutelas, disputas tributarias bancarias, tramitadores exigiendo dinero) activan automáticamente el nodo de escalamiento humano, asignando el caso a la bandeja de un funcionario público competente.
- **Supervisión de Clasificaciones:** La consola de funcionario permite avalar la clasificación sugerida por el agente o reclasificar a otra dependencia con un solo clic, preservando el registro de quién aprobó la acción.

---

## 6. Base de Datos Vectorial Estructurada (`StructuredVectorDB`) y Doble Motor LLM
- **`StructuredVectorDB`:** Índice semántico denso en memoria (`NumPy`) y persistencia en tabla SQLite `structured_knowledge_items`. Cada ítem indexa entidades clave (`key_facts`), requisitos, plazos legales y canales de atención oficial con vigencia 2026.
- **Doble Motor de Inferencia:**
  - **Motor Primario:** Groq Cloud API (`openai/gpt-oss-120b`) con latencia inferior a 2 segundos y alta empatía caribeña.
  - **Motor Secundario (Fallback $0):** Ollama local (`qwen2.5:0.5b` / `llama3:latest`) para garantizar autonomía total y operación offline.
- **Limpieza y Estructuración de Respuestas:** El filtro `clean_response_text` elimina encabezados markdown, líneas divisorias y asteriscos dobles, produciendo viñetas elegantes (`•`) y pasos numerados limpios.

---

## 7. Despliegue en Contenedores Docker
- **Dockerfile Multi-Stage:**
  - *Etapa 1:* Compilación del frontend React con Node.js 22 Alpine (`npm run build`).
  - *Etapa 2:* Runtime en Python 3.12 Slim con todas las dependencias compiladas y el frontend montado en `/app/frontend/dist`.
- **Servidor Todo-en-Uno:** FastAPI expone en el puerto 8000 tanto la API REST como la aplicación web de producción, permitiendo un despliegue ligero en un único contenedor o mediante `docker-compose.yml`.
