-- =====================================================================
-- ALCALDÍA DISTRITAL DE BARRANQUILLA
-- POLÍTICA DE SEGURIDAD Y CONTROL DE ACCESO (RBAC) PARA SNOWFLAKE Y MCP
-- PRINCIPIO DE MENOR PRIVILEGIO (LEAST PRIVILEGE) PARA AGENTES DE IA
-- =====================================================================

-- PASO 1: CREAR ROL RESTRINGIDO DE SOLO CONSULTA
USE ROLE SECURITYADMIN;

CREATE ROLE IF NOT EXISTS BQL_CITIZEN_READONLY_ROLE
    COMMENT = 'Rol de solo lectura institucional para agentes de IA y servidores MCP. Sin privilegios de modificación ni administración.';

-- PASO 2: CREAR USUARIO DE SERVICIO DEDICADO
-- Nota: En producción, se recomienda sustitución periódica de contraseña o autenticación por par de claves RSA (Key-Pair).
CREATE USER IF NOT EXISTS BQL_MCP_READER
    PASSWORD = '<tu_password_seguro_mcp>'
    DEFAULT_ROLE = BQL_CITIZEN_READONLY_ROLE
    DEFAULT_WAREHOUSE = COMPUTE_WH
    MUST_CHANGE_PASSWORD = FALSE
    COMMENT = 'Usuario de servicio exclusivo para consultas de lectura de agentes de IA y MCP';

-- Asignar el rol al usuario de servicio
GRANT ROLE BQL_CITIZEN_READONLY_ROLE TO USER BQL_MCP_READER;

-- =====================================================================
-- PASO 3: ASIGNACIÓN ESTRICTA DE PRIVILEGIOS MÍNIMOS (LEAST PRIVILEGE)
-- =====================================================================
USE ROLE ACCOUNTADMIN;

-- 3.1. Acceso a Cómputo (Solo USAGE en el Warehouse, no modificación ni redimensionamiento)
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE BQL_CITIZEN_READONLY_ROLE;

-- 3.2. Acceso a Base de Datos (Solo USAGE, sin CREATE SCHEMA ni DROP)
GRANT USAGE ON DATABASE BARRANQUILLA_CITIZEN_DB TO ROLE BQL_CITIZEN_READONLY_ROLE;

-- 3.3. Acceso a Esquemas Autorizados (Solo USAGE, sin MODIFY ni CREATE TABLE)
GRANT USAGE ON SCHEMA BARRANQUILLA_CITIZEN_DB.OPERATIONS TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT USAGE ON SCHEMA BARRANQUILLA_CITIZEN_DB.CURATED TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT USAGE ON SCHEMA BARRANQUILLA_CITIZEN_DB.ANALYTICS TO ROLE BQL_CITIZEN_READONLY_ROLE;

-- 3.4. Privilegio SELECT exclusivamente sobre tablas y vistas autorizadas
GRANT SELECT ON ALL TABLES IN SCHEMA BARRANQUILLA_CITIZEN_DB.OPERATIONS TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA BARRANQUILLA_CITIZEN_DB.CURATED TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA BARRANQUILLA_CITIZEN_DB.ANALYTICS TO ROLE BQL_CITIZEN_READONLY_ROLE;

-- Asegurar que futuras tablas y vistas mantengan automáticamente solo SELECT
GRANT SELECT ON FUTURE TABLES IN SCHEMA BARRANQUILLA_CITIZEN_DB.OPERATIONS TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA BARRANQUILLA_CITIZEN_DB.CURATED TO ROLE BQL_CITIZEN_READONLY_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA BARRANQUILLA_CITIZEN_DB.ANALYTICS TO ROLE BQL_CITIZEN_READONLY_ROLE;

-- =====================================================================
-- PASO 4: SALVAGUARDAS Y POLÍTICA DE EXCLUSIÓN EXPLÍCITA
-- =====================================================================
-- 1. NO se otorga acceso al esquema GOVERNANCE (Auditoría interna inaccesible para el agente).
-- 2. NO se otorgan permisos INSERT, UPDATE, DELETE, TRUNCATE ni DROP.
-- 3. Cualquier intento de alteración estructural provocará error de compilación SQL por privilegios insuficientes.

-- =====================================================================
-- PASO 5: VERIFICACIÓN DE PERMISOS EFECTIVOS
-- =====================================================================
SHOW GRANTS TO ROLE BQL_CITIZEN_READONLY_ROLE;
SHOW GRANTS TO USER BQL_MCP_READER;
