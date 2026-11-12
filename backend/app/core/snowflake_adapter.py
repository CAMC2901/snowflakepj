import os
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
import snowflake.connector
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, Case, CaseEvent, CuratedDocument, Department

EXPORT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "snowflake_exports"

class SnowflakeAdapter:
    """Adaptador oficial para conectar y sincronizar con Snowflake.

    Permite conexión directa a cuentas activas de Snowflake o sincronización
    desde la capa local.
    """

    def __init__(self):
        self.account = settings.SNOWFLAKE_ACCOUNT or os.getenv("SNOWFLAKE_ACCOUNT", "")
        self.user = settings.SNOWFLAKE_USER or os.getenv("SNOWFLAKE_USER", "")
        self.password = settings.SNOWFLAKE_PASSWORD or os.getenv("SNOWFLAKE_PASSWORD", "")
        self.database = settings.SNOWFLAKE_DATABASE or os.getenv("SNOWFLAKE_DATABASE", "BARRANQUILLA_CITIZEN_DB")
        self.schema = settings.SNOWFLAKE_SCHEMA or os.getenv("SNOWFLAKE_SCHEMA", "OPERATIONS")
        self.warehouse = settings.SNOWFLAKE_WAREHOUSE or os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")

    def is_configured(self) -> bool:
        return bool(self.account and self.user and self.password)

    def test_connection(self, account: str = None, user: str = None, password: str = None, warehouse: str = None, database: str = None) -> Dict[str, Any]:
        acc = account or self.account
        usr = user or self.user
        pwd = password or self.password
        wh = warehouse or self.warehouse
        db = database or self.database

        if not acc or not usr or not pwd:
            return {
                "success": False,
                "message": "Faltan credenciales obligatorias (account, user, password) para conectar con Snowflake."
            }

        # Normalizar account eliminando posibles prefijos https:// o sufijos .snowflakecomputing.com
        acc_clean = acc.strip().replace("https://", "").replace("http://", "")
        if ".snowflakecomputing.com" in acc_clean:
            acc_clean = acc_clean.split(".snowflakecomputing.com")[0]

        try:
            # Conexión inicial sin forzar existencia previa de la base de datos
            conn = snowflake.connector.connect(
                user=usr.strip(),
                password=pwd.strip(),
                account=acc_clean,
                warehouse=wh.strip() if wh else "COMPUTE_WH",
                login_timeout=25
            )
            cs = conn.cursor()

            # Asegurar la creación de la base de datos si tiene permisos, o simplemente usarla si es rol de solo lectura
            try:
                cs.execute(f"CREATE DATABASE IF NOT EXISTS {db};")
                cs.execute(f"CREATE SCHEMA IF NOT EXISTS {db}.OPERATIONS;")
                cs.execute(f"CREATE SCHEMA IF NOT EXISTS {db}.RAW;")
                cs.execute(f"CREATE SCHEMA IF NOT EXISTS {db}.CURATED;")
                cs.execute(f"CREATE SCHEMA IF NOT EXISTS {db}.ANALYTICS;")
                cs.execute(f"CREATE SCHEMA IF NOT EXISTS {db}.GOVERNANCE;")
            except Exception:
                # Si el rol es de solo lectura (ej: BQL_CITIZEN_READONLY_ROLE), no tiene CREATE DATABASE y procede directo
                pass

            cs.execute(f"USE DATABASE {db};")

            cs.execute("SELECT CURRENT_VERSION(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE();")
            row = cs.fetchone()
            version, role, cur_wh, cur_db = row if row else ("Desconocido", "", "", "")
            cs.close()
            conn.close()

            # Actualizar configuración en memoria si la prueba fue exitosa
            self.account = acc_clean
            self.user = usr.strip()
            self.password = pwd.strip()
            self.warehouse = wh.strip() if wh else "COMPUTE_WH"
            self.database = db

            return {
                "success": True,
                "version": version,
                "role": role,
                "warehouse": cur_wh,
                "database": cur_db,
                "message": f"Conexión exitosa con Snowflake (Versión: {version}, Rol: {role}, Base de Datos provisionada: {cur_db})."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error al conectar con Snowflake: {str(e)}"
            }

    def sync_cases_to_snowflake(self) -> Dict[str, Any]:
        """Sincroniza los casos registrados localmente hacia la tabla OPERATIONS.CASES en Snowflake."""
        if not self.is_configured():
            return {
                "success": False,
                "message": "Snowflake no está configurado con credenciales activas. Ingrese cuenta, usuario y contraseña primero."
            }

        db = SessionLocal()
        try:
            cases = db.query(Case).all()
            departments = db.query(Department).all()

            acc_clean = self.account.strip().replace("https://", "").replace("http://", "")
            if ".snowflakecomputing.com" in acc_clean:
                acc_clean = acc_clean.split(".snowflakecomputing.com")[0]

            conn = snowflake.connector.connect(
                user=self.user.strip(),
                password=self.password.strip(),
                account=acc_clean,
                warehouse=self.warehouse or "COMPUTE_WH",
                login_timeout=25
            )
            cs = conn.cursor()

            # Asegurar base de datos y esquemas
            cs.execute(f"CREATE DATABASE IF NOT EXISTS {self.database};")
            cs.execute(f"CREATE SCHEMA IF NOT EXISTS {self.database}.OPERATIONS;")
            cs.execute(f"CREATE SCHEMA IF NOT EXISTS {self.database}.CURATED;")
            cs.execute(f"CREATE SCHEMA IF NOT EXISTS {self.database}.ANALYTICS;")
            cs.execute(f"USE DATABASE {self.database};")
            cs.execute("USE SCHEMA OPERATIONS;")

            # Crear tabla CASES si no existe
            cs.execute("""
            CREATE TABLE IF NOT EXISTS CASES (
                RADICADO VARCHAR(50) PRIMARY KEY,
                CITIZEN_NAME VARCHAR(150),
                CITIZEN_PHONE VARCHAR(50),
                CATEGORY VARCHAR(100),
                TITLE VARCHAR(255),
                DESCRIPTION TEXT,
                STATUS VARCHAR(50),
                PRIORITY VARCHAR(20),
                ASSIGNED_TO VARCHAR(100),
                SLA_DUE_DATE TIMESTAMP_NTZ,
                CREATED_AT TIMESTAMP_NTZ
            );
            """)

            synced_count = 0
            for c in cases:
                cs.execute("""
                MERGE INTO CASES t
                USING (SELECT %s AS radicado, %s AS citizen_name, %s AS citizen_phone, %s AS category,
                              %s AS title, %s AS description, %s AS status, %s AS priority,
                              %s AS assigned_to, %s AS sla_due_date, %s AS created_at) s
                ON t.RADICADO = s.radicado
                WHEN MATCHED THEN
                    UPDATE SET t.STATUS = s.status, t.PRIORITY = s.priority, t.ASSIGNED_TO = s.assigned_to
                WHEN NOT MATCHED THEN
                    INSERT (RADICADO, CITIZEN_NAME, CITIZEN_PHONE, CATEGORY, TITLE, DESCRIPTION, STATUS, PRIORITY, ASSIGNED_TO, SLA_DUE_DATE, CREATED_AT)
                    VALUES (s.radicado, s.citizen_name, s.citizen_phone, s.category, s.title, s.description, s.status, s.priority, s.assigned_to, s.sla_due_date, s.created_at);
                """, (
                    c.radicado, c.citizen_name, c.citizen_phone, c.category,
                    c.title, c.description, c.status, c.priority, c.assigned_to,
                    c.sla_due_date.strftime("%Y-%m-%d %H:%M:%S") if c.sla_due_date else None,
                    c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else None
                ))
                synced_count += 1

            # Sincronizar catálogo de dependencias en CURATED.DEPARTMENTS
            cs.execute("""
            CREATE TABLE IF NOT EXISTS CURATED.DEPARTMENTS (
                CODE VARCHAR(50) PRIMARY KEY,
                NAME VARCHAR(150),
                CONTACT_EMAIL VARCHAR(100),
                PHONE VARCHAR(50),
                RESPONSIBLE_OFFICER VARCHAR(150)
            );
            """)

            for d in departments:
                cs.execute("""
                MERGE INTO CURATED.DEPARTMENTS t
                USING (SELECT %s AS code, %s AS name, %s AS contact_email, %s AS phone, %s AS responsible_officer) s
                ON t.CODE = s.code
                WHEN MATCHED THEN
                    UPDATE SET t.NAME = s.name, t.CONTACT_EMAIL = s.contact_email, t.RESPONSIBLE_OFFICER = s.responsible_officer
                WHEN NOT MATCHED THEN
                    INSERT (CODE, NAME, CONTACT_EMAIL, PHONE, RESPONSIBLE_OFFICER)
                    VALUES (s.code, s.name, s.contact_email, s.phone, s.responsible_officer);
                """, (d.code, d.name, d.contact_email, d.phone, d.responsible_officer))

            # Crear Vistas Analíticas en ANALYTICS
            cs.execute("""
            CREATE OR REPLACE VIEW ANALYTICS.V_CASES_BY_DEPARTMENT AS
            SELECT 
                ASSIGNED_TO AS DEPARTMENT_NAME,
                COUNT(*) AS TOTAL_CASES,
                COUNT(CASE WHEN STATUS = 'RESUELTO' THEN 1 END) AS RESOLVED_CASES,
                COUNT(CASE WHEN STATUS = 'ESCALADO_HUMANO' THEN 1 END) AS ESCALATED_CASES
            FROM OPERATIONS.CASES
            GROUP BY ASSIGNED_TO;
            """)

            conn.commit()
            cs.close()
            conn.close()

            return {
                "success": True,
                "synced_count": synced_count,
                "message": f"Se sincronizaron exitosamente {synced_count} casos y dependencias en Snowflake (Base BARRANQUILLA_CITIZEN_DB, esquemas OPERATIONS, CURATED y ANALYTICS)."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error durante la sincronización a Snowflake: {str(e)}"
            }
        finally:
            db.close()

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_configured": self.is_configured(),
            "account": self.account if self.account else "No configurada",
            "user": self.user if self.user else "No configurado",
            "database": self.database,
            "warehouse": self.warehouse,
            "schema": self.schema,
            "mode": "SNOWFLAKE_CLOUD_READY" if self.is_configured() else "SNOWFLAKE_LOCAL_EMULATION"
        }

snowflake_adapter = SnowflakeAdapter()
