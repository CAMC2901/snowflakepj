from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.core.snowflake_adapter import snowflake_adapter
from backend.app.core.database import (
    get_db, Case, CaseEvent, CuratedDocument, DocumentChunk, Department, Procedure, RawDocument, IngestionLog, SourceRegistry, AccessAudit
)
from backend.app.core.config import BASE_DIR

router = APIRouter(prefix="/snowflake", tags=["Snowflake"])

class SnowflakeConfigRequest(BaseModel):
    account: str
    user: str
    password: str
    warehouse: Optional[str] = "COMPUTE_WH"
    database: Optional[str] = "BARRANQUILLA_CITIZEN_DB"
    schema_name: Optional[str] = "OPERATIONS"

@router.get("/status")
def get_snowflake_status():
    return snowflake_adapter.get_status()

@router.get("/schema_preview")
def get_schema_preview(db: Session = Depends(get_db)):
    """Devuelve la estructura completa de las 5 capas lógicas de Snowflake con conteo de registros."""
    raw_docs_count = db.query(RawDocument).count()
    ingest_count = db.query(IngestionLog).count()
    curated_docs_count = db.query(CuratedDocument).count()
    chunks_count = db.query(DocumentChunk).count()
    dept_count = db.query(Department).count()
    proc_count = db.query(Procedure).count()
    cases_count = db.query(Case).count()
    events_count = db.query(CaseEvent).count()
    sources_count = db.query(SourceRegistry).count()
    audit_count = db.query(AccessAudit).count()

    # Muestra de los últimos casos en la capa OPERATIONS.CASES
    sample_cases = db.query(Case).order_by(Case.id.desc()).limit(10).all()
    sample_data = [
        {
            "RADICADO": c.radicado,
            "CITIZEN_NAME": c.citizen_name or "Ciudadano",
            "CATEGORY": c.category,
            "STATUS": c.status,
            "ASSIGNED_TO": c.assigned_to,
            "SLA_DUE_DATE": c.sla_due_date.strftime("%Y-%m-%d") if c.sla_due_date else "N/A"
        }
        for c in sample_cases
    ]

    return {
        "database_name": snowflake_adapter.database,
        "warehouse": snowflake_adapter.warehouse,
        "is_configured": snowflake_adapter.is_configured(),
        "account": snowflake_adapter.account if snowflake_adapter.is_configured() else "No conectada",
        "schemas": [
            {
                "schema_name": "RAW",
                "description": "Capa de ingesta cruda de documentos y bitácoras de extracción",
                "tables": [
                    {"table_name": "RAW_DOCUMENTS", "rows": raw_docs_count, "columns": ["ID", "TITLE", "URL", "ENTITY", "FORMAT", "CHECKSUM", "RAW_CONTENT"]},
                    {"table_name": "INGESTION_LOG", "rows": ingest_count, "columns": ["ID", "FILENAME", "ACTION", "CHUNKS_COUNT", "STATUS", "DURATION_MS"]}
                ]
            },
            {
                "schema_name": "CURATED",
                "description": "Capa de conocimiento depurado, catálogo distrital y fragmentos RAG",
                "tables": [
                    {"table_name": "CURATED_DOCUMENTS", "rows": curated_docs_count, "columns": ["ID", "DOC_CODE", "TITLE", "CATEGORY", "AUTHORITY", "VALIDITY_DATE"]},
                    {"table_name": "DOCUMENT_CHUNKS", "rows": chunks_count, "columns": ["ID", "DOCUMENT_ID", "CHUNK_INDEX", "CONTENT", "EMBEDDING (768)"]},
                    {"table_name": "DEPARTMENTS", "rows": dept_count, "columns": ["ID", "CODE", "NAME", "CONTACT_EMAIL", "PHONE", "RESPONSIBLE_OFFICER"]},
                    {"table_name": "PROCEDURES", "rows": proc_count, "columns": ["ID", "CODE", "NAME", "SLA_DAYS", "LEGAL_BASIS"]}
                ]
            },
            {
                "schema_name": "OPERATIONS",
                "description": "Capa transaccional de solicitudes ciudadanas y eventos inmutables",
                "tables": [
                    {"table_name": "CASES", "rows": cases_count, "columns": ["ID", "RADICADO", "CITIZEN_NAME", "CATEGORY", "STATUS", "PRIORITY", "SLA_DUE_DATE"]},
                    {"table_name": "CASE_EVENTS", "rows": events_count, "columns": ["ID", "CASE_ID", "EVENT_TYPE", "ACTOR", "ACTOR_ROLE", "DESCRIPTION"]},
                    {"table_name": "CLASSIFICATIONS", "rows": cases_count, "columns": ["ID", "CASE_ID", "PREDICTED_CATEGORY", "CONFIDENCE", "APPROVED_BY_HUMAN"]}
                ]
            },
            {
                "schema_name": "ANALYTICS",
                "description": "Vistas agregadas de control de términos (SLA) y balance de carga",
                "tables": [
                    {"table_name": "V_CASES_BY_DEPARTMENT", "type": "VIEW", "columns": ["DEPARTMENT_NAME", "TOTAL_CASES", "RESOLVED_CASES", "ESCALATED_CASES"]},
                    {"table_name": "V_SLA_RISK_MONITOR", "type": "VIEW", "columns": ["RADICADO", "TITLE", "SLA_DUE_DATE", "HOURS_REMAINING", "SLA_STATUS"]}
                ]
            },
            {
                "schema_name": "GOVERNANCE",
                "description": "Registro de fuentes oficiales autorizadas y auditoría de accesos",
                "tables": [
                    {"table_name": "SOURCE_REGISTRY", "rows": sources_count, "columns": ["ID", "NAME", "ENTITY", "BASE_URL", "ACCESS_TYPE", "STATUS"]},
                    {"table_name": "ACCESS_AUDIT", "rows": audit_count, "columns": ["ID", "USER_OR_SESSION", "ACTION", "RESOURCE", "IP_ADDRESS", "TIMESTAMP"]}
                ]
            }
        ],
        "sample_cases": sample_data
    }

@router.post("/test_connection")
def test_snowflake_connection(req: SnowflakeConfigRequest):
    result = snowflake_adapter.test_connection(
        account=req.account,
        user=req.user,
        password=req.password,
        warehouse=req.warehouse,
        database=req.database
    )
    
    # Si la conexión tuvo éxito, persistir en el archivo .env
    if result.get("success"):
        env_path = BASE_DIR / ".env"
        try:
            content = ""
            if env_path.exists():
                with open(env_path, "r", encoding="utf-8") as f:
                    content = f.read()

            lines = [l for l in content.split("\n") if l.strip()]
            new_lines = []
            keys_updated = set()
            for line in lines:
                if line.startswith("SNOWFLAKE_ACCOUNT="):
                    new_lines.append(f'SNOWFLAKE_ACCOUNT="{snowflake_adapter.account}"')
                    keys_updated.add("SNOWFLAKE_ACCOUNT")
                elif line.startswith("SNOWFLAKE_USER="):
                    new_lines.append(f'SNOWFLAKE_USER="{snowflake_adapter.user}"')
                    keys_updated.add("SNOWFLAKE_USER")
                elif line.startswith("SNOWFLAKE_PASSWORD="):
                    new_lines.append(f'SNOWFLAKE_PASSWORD="{snowflake_adapter.password}"')
                    keys_updated.add("SNOWFLAKE_PASSWORD")
                elif line.startswith("SNOWFLAKE_DATABASE="):
                    new_lines.append(f'SNOWFLAKE_DATABASE="{snowflake_adapter.database}"')
                    keys_updated.add("SNOWFLAKE_DATABASE")
                elif line.startswith("SNOWFLAKE_WAREHOUSE="):
                    new_lines.append(f'SNOWFLAKE_WAREHOUSE="{snowflake_adapter.warehouse}"')
                    keys_updated.add("SNOWFLAKE_WAREHOUSE")
                else:
                    new_lines.append(line)

            if "SNOWFLAKE_ACCOUNT" not in keys_updated:
                new_lines.append(f'SNOWFLAKE_ACCOUNT="{snowflake_adapter.account}"')
            if "SNOWFLAKE_USER" not in keys_updated:
                new_lines.append(f'SNOWFLAKE_USER="{snowflake_adapter.user}"')
            if "SNOWFLAKE_PASSWORD" not in keys_updated:
                new_lines.append(f'SNOWFLAKE_PASSWORD="{snowflake_adapter.password}"')
            if "SNOWFLAKE_DATABASE" not in keys_updated:
                new_lines.append(f'SNOWFLAKE_DATABASE="{snowflake_adapter.database}"')
            if "SNOWFLAKE_WAREHOUSE" not in keys_updated:
                new_lines.append(f'SNOWFLAKE_WAREHOUSE="{snowflake_adapter.warehouse}"')

            with open(env_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")
        except Exception as e:
            print("Error guardando .env:", e)

    return result

@router.post("/sync")
def sync_cases():
    return snowflake_adapter.sync_cases_to_snowflake()

@router.get("/download_sql")
def download_snowflake_sql():
    sql_path = BASE_DIR / "app" / "core" / "snowflake_schema.sql"
    if not sql_path.exists():
        sql_path = BASE_DIR / "backend" / "app" / "core" / "snowflake_schema.sql"
    return FileResponse(sql_path, media_type="application/sql", filename="snowflake_barranquilla_complete.sql")
