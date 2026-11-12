# Guía de Conexión Segura vía MCP con Snowflake
### Alcaldía Distrital de Barranquilla — Agente Inteligente de Gestión Ciudadana

Esta guía técnica documenta la integración entre el **Model Context Protocol (MCP)** y la plataforma de datos en la nube **Snowflake**, aplicando de forma estricta el **Principio de Menor Privilegio (*Least Privilege*)**, aislamiento por esquemas y salvaguardas de gobernanza para el sector público.

---

## 🛡️ 1. Principio Rector: Seguridad y Menor Privilegio

En sistemas de inteligencia artificial para la administración pública, **un agente de IA o servidor MCP jamás debe conectarse con roles administrativos** (`ACCOUNTADMIN`, `SYSADMIN`, `SECURITYADMIN`), ni con cuentas personales.

### ¿Por qué?
- **Riesgo de Inyección de Prompts (*Prompt Injection*):** Si un atacante intenta manipular al modelo para ejecutar comandos destructivos (`DROP TABLE`, `DELETE FROM`), el motor criptográfico de Snowflake rechazará la consulta de inmediato al carecer de privilegios.
- **Aislamiento de Información Sensible:** El agente solo tiene visibilidad sobre las tablas necesarias para responder a la ciudadanía (`CASES`, `DEPARTMENTS`, `ANALYTICS`), quedando **bloqueado el acceso a la auditoría interna y credenciales** (`GOVERNANCE.ACCESS_AUDIT`).
- **Trazabilidad Institucional:** Todas las consultas ejecutadas por el servidor MCP quedan registradas en la vista de auditoría `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` bajo el usuario dedicado `BQL_MCP_READER`.

---

## 🏛️ 2. Arquitectura de Permisos RBAC en Snowflake

```text
[Cliente MCP: Antigravity / Claude / Cursor]
                 │
                 ▼ Autenticación restringida
       [Usuario: BQL_MCP_READER]
                 │
                 ▼ Rol exclusivo
   [Rol: BQL_CITIZEN_READONLY_ROLE]
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
[OPERATIONS.CASES]   [ANALYTICS.V_*]
 (Solo SELECT)        (Solo SELECT)
       │                   │
       ✕                   ✕
  (NO INSERT)         (NO MODIFY)
  (NO UPDATE)         (NO DROP)
  (NO DELETE)
```

---

## 📋 3. Despliegue de la Política de Seguridad en Snowsight

Ejecuta el script oficial ubicado en [`backend/app/core/snowflake_security_rbac.sql`](../backend/app/core/snowflake_security_rbac.sql) dentro de una hoja de trabajo de Snowflake (**Worksheets**):

```sql
-- 1. Crear el Rol de Solo Lectura
USE ROLE SECURITYADMIN;
CREATE ROLE IF NOT EXISTS BQL_CITIZEN_READONLY_ROLE
    COMMENT = 'Rol restringido de solo consulta para servidor MCP de IA';

-- 2. Crear el Usuario de Servicio
CREATE USER IF NOT EXISTS BQL_MCP_READER
    PASSWORD = '<tu_password_seguro_mcp>'
    DEFAULT_ROLE = BQL_CITIZEN_READONLY_ROLE
    DEFAULT_WAREHOUSE = COMPUTE_WH
    MUST_CHANGE_PASSWORD = FALSE;

GRANT ROLE BQL_CITIZEN_READONLY_ROLE TO USER BQL_MCP_READER;

-- 3. Otorgar ÚNICAMENTE permisos de uso y consulta (SELECT)
USE ROLE ACCOUNTADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT USAGE ON DATABASE BARRANQUILLA_CITIZEN_DB TO ROLE BQL_CITIZEN_READONLY_ROLE;

GRANT USAGE ON SCHEMA BARRANQUILLA_CITIZEN_DB.OPERATIONS TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT USAGE ON SCHEMA BARRANQUILLA_CITIZEN_DB.CURATED TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT USAGE ON SCHEMA BARRANQUILLA_CITIZEN_DB.ANALYTICS TO ROLE BQL_CITIZEN_READONLY_ROLE;

GRANT SELECT ON ALL TABLES IN SCHEMA BARRANQUILLA_CITIZEN_DB.OPERATIONS TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA BARRANQUILLA_CITIZEN_DB.CURATED TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA BARRANQUILLA_CITIZEN_DB.ANALYTICS TO ROLE BQL_CITIZEN_READONLY_ROLE;

GRANT SELECT ON FUTURE TABLES IN SCHEMA BARRANQUILLA_CITIZEN_DB.OPERATIONS TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA BARRANQUILLA_CITIZEN_DB.ANALYTICS TO ROLE BQL_CITIZEN_READONLY_ROLE;
```

---

## ⚙️ 4. Configuración del Servidor MCP

### Opción A: Configuración en `mcp_servers.json` (Antigravity IDE / Claude Desktop / Cursor)

Agrega la siguiente definición a tu archivo de configuración de servidores MCP:

```json
{
  "mcpServers": {
    "snowflake-barranquilla": {
      "command": "npx",
      "args": ["-y", "snowflake-mcp"],
      "env": {
        "SNOWFLAKE_ACCOUNT": "tu_identificador_de_cuenta",
        "SNOWFLAKE_USERNAME": "BQL_MCP_READER",
        "SNOWFLAKE_PASSWORD": "<tu_password_seguro_mcp>",
        "SNOWFLAKE_ROLE": "BQL_CITIZEN_READONLY_ROLE",
        "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
        "SNOWFLAKE_DATABASE": "BARRANQUILLA_CITIZEN_DB",
        "SNOWFLAKE_SCHEMA": "OPERATIONS"
      }
    }
  }
}
```

---

## 🧪 5. Verificación Automatizada de Seguridad

El sistema incluye una herramienta de auditoría automatizada para verificar el cumplimiento del principio de menor privilegio:

```bash
python backend/app/core/test_snowflake_security.py <cuenta> BQL_MCP_READER <tu_password_seguro_mcp> COMPUTE_WH
```

Esta prueba verifica en vivo contra Snowflake 5 vectores de seguridad:
1. **Lectura de Casos:** `SELECT COUNT(*) FROM OPERATIONS.CASES` $\rightarrow$ **PERMITIDO**.
2. **Lectura Analítica:** `SELECT * FROM ANALYTICS.V_CASES_BY_DEPARTMENT` $\rightarrow$ **PERMITIDO**.
3. **Protección Destructiva:** `DROP TABLE OPERATIONS.CASES` $\rightarrow$ **BLOQUEADO POR SNOWFLAKE**.
4. **Protección de Inserción:** `INSERT INTO OPERATIONS.CASES` $\rightarrow$ **BLOQUEADO POR SNOWFLAKE**.
5. **Aislamiento de Gobernanza:** `SELECT * FROM GOVERNANCE.ACCESS_AUDIT` $\rightarrow$ **DENEGADO POR SNOWFLAKE**.

---

## ⚖️ 6. Cumplimiento Normativo

Esta arquitectura se alinea rigurosamente con:
- **Ley Estatutaria 1581 de 2012:** Protección de datos personales de los ciudadanos.
- **Ley 1712 de 2014:** Transparencia y acceso a la información pública nacional.
- **Marco de Seguridad y Privacidad de la Información (MSPI - MinTIC Colombia).**
- **CIS Snowflake Foundations Benchmark v1.0:** Estándar internacional de configuración segura para Snowflake.
