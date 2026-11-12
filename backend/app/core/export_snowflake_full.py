from pathlib import Path
from backend.app.core.database import SessionLocal, Department, Case
from backend.app.core.config import BASE_DIR

SCHEMA_SQL_PATH = BASE_DIR / "app" / "core" / "snowflake_schema.sql"

def append_seed_data():
    db = SessionLocal()
    depts = db.query(Department).all()
    cases = db.query(Case).all()

    sql_lines = [
        "",
        "-- =====================================================================",
        "-- POBLACIÓN OFICIAL DE DATOS PARA SNOWSIGHT (CARGA COMPLETA)",
        "-- =====================================================================",
        "USE DATABASE BARRANQUILLA_CITIZEN_DB;",
        "USE SCHEMA CURATED;",
        ""
    ]

    for d in depts:
        code = d.code
        name = (d.name or "").replace("'", "''")
        desc = (d.description or "").replace("'", "''")
        email = (d.contact_email or "").replace("'", "''")
        phone = (d.phone or "").replace("'", "''")
        officer = (d.responsible_officer or "").replace("'", "''")
        addr = (d.address or "").replace("'", "''")
        sql_lines.append(
            f"MERGE INTO CURATED.DEPARTMENTS t "
            f"USING (SELECT '{code}' as code, '{name}' as name, '{desc}' as description, '{email}' as contact_email, '{phone}' as phone, '{officer}' as responsible_officer, '{addr}' as address) s "
            f"ON t.CODE = s.code "
            f"WHEN MATCHED THEN UPDATE SET t.NAME = s.name, t.CONTACT_EMAIL = s.contact_email, t.RESPONSIBLE_OFFICER = s.responsible_officer "
            f"WHEN NOT MATCHED THEN INSERT (CODE, NAME, DESCRIPTION, CONTACT_EMAIL, PHONE, RESPONSIBLE_OFFICER, ADDRESS) "
            f"VALUES (s.code, s.name, s.description, s.contact_email, s.phone, s.responsible_officer, s.address);"
        )

    sql_lines.extend([
        "",
        "USE SCHEMA OPERATIONS;",
        ""
    ])

    for cs in cases:
        rad = cs.radicado
        name = (cs.citizen_name or "Ciudadano").replace("'", "''")
        title = (cs.title or "").replace("'", "''")
        desc = (cs.description or "").replace("'", "''")
        phone = cs.citizen_phone or "N/A"
        cat = (cs.category or "").replace("'", "''")
        status = cs.status or "EN_GESTION"
        prio = cs.priority or "MEDIA"
        ass = (cs.assigned_to or "").replace("'", "''")
        sla_val = f"'{cs.sla_due_date.strftime('%Y-%m-%d %H:%M:%S')}'" if cs.sla_due_date else "NULL"
        created_val = f"'{cs.created_at.strftime('%Y-%m-%d %H:%M:%S')}'" if cs.created_at else "CURRENT_TIMESTAMP()"
        sql_lines.append(
            f"MERGE INTO OPERATIONS.CASES t "
            f"USING (SELECT '{rad}' as radicado, '{name}' as citizen_name, '{phone}' as citizen_phone, '{cat}' as category, '{title}' as title, '{desc}' as description, '{status}' as status, '{prio}' as priority, '{ass}' as assigned_to, {sla_val} as sla_due_date, {created_val} as created_at) s "
            f"ON t.RADICADO = s.radicado "
            f"WHEN MATCHED THEN UPDATE SET t.STATUS = s.status, t.PRIORITY = s.priority, t.ASSIGNED_TO = s.assigned_to "
            f"WHEN NOT MATCHED THEN INSERT (RADICADO, CITIZEN_NAME, CITIZEN_PHONE, CATEGORY, TITLE, DESCRIPTION, STATUS, PRIORITY, ASSIGNED_TO, SLA_DUE_DATE, CREATED_AT) "
            f"VALUES (s.radicado, s.citizen_name, s.citizen_phone, s.category, s.title, s.description, s.status, s.priority, s.assigned_to, s.sla_due_date, s.created_at);"
        )

    # También consultas de verificación final
    sql_lines.extend([
        "",
        "-- =====================================================================",
        "-- CONSULTAS DE VERIFICACIÓN EN SNOWSIGHT",
        "-- =====================================================================",
        "SELECT * FROM OPERATIONS.CASES ORDER BY CREATED_AT DESC;",
        "SELECT * FROM ANALYTICS.V_CASES_BY_DEPARTMENT;",
        "SELECT * FROM ANALYTICS.V_SLA_RISK_MONITOR;"
    ])

    with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
        existing_content = f.read()

    marker = "-- POBLACIÓN OFICIAL DE DATOS PARA SNOWSIGHT"
    if marker in existing_content:
        base_part = existing_content.split(marker)[0]
        new_content = base_part.strip() + "\n\n" + "\n".join(sql_lines).strip() + "\n"
    else:
        new_content = existing_content.strip() + "\n\n" + "\n".join(sql_lines).strip() + "\n"

    with open(SCHEMA_SQL_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    db.close()
    print("snowflake_schema.sql actualizado con éxito con los datos completos.")

if __name__ == "__main__":
    append_seed_data()
