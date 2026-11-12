-- =====================================================================
-- ESQUEMA COMPLETO DE BASE DE DATOS EN SNOWFLAKE
-- AGENTE INTELIGENTE DE GESTIÓN CIUDADANA - ALCALDÍA DE BARRANQUILLA
-- =====================================================================

-- 1. Crear Base de Datos y Warehouse
CREATE DATABASE IF NOT EXISTS BARRANQUILLA_CITIZEN_DB;
USE DATABASE BARRANQUILLA_CITIZEN_DB;

CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH
    WITH WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

-- =====================================================================
-- ESQUEMA 1: RAW (Ingesta cruda de documentos y bitácoras)
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS RAW;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS RAW_DOCUMENTS (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    TITLE VARCHAR(255) NOT NULL,
    URL VARCHAR(500),
    ENTITY VARCHAR(100) DEFAULT 'Alcaldía Distrital de Barranquilla',
    FORMAT VARCHAR(20) DEFAULT 'PDF',
    CHECKSUM VARCHAR(64),
    FILE_SIZE NUMBER,
    RAW_CONTENT TEXT,
    STATUS VARCHAR(50) DEFAULT 'CAPTURED',
    CAPTURED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS INGESTION_LOG (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    FILENAME VARCHAR(255) NOT NULL,
    ACTION VARCHAR(50) DEFAULT 'INDEX',
    CHUNKS_COUNT NUMBER DEFAULT 0,
    STATUS VARCHAR(50) DEFAULT 'SUCCESS',
    DURATION_MS NUMBER DEFAULT 0,
    ERROR_MESSAGE TEXT,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- =====================================================================
-- ESQUEMA 2: CURATED (Conocimiento estructurado y vectores de búsqueda)
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS CURATED;
USE SCHEMA CURATED;

CREATE TABLE IF NOT EXISTS CURATED_DOCUMENTS (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    DOC_CODE VARCHAR(50) UNIQUE NOT NULL,
    TITLE VARCHAR(255) NOT NULL,
    CATEGORY VARCHAR(100),
    AUTHORITY VARCHAR(150) DEFAULT 'Alcaldía Distrital de Barranquilla',
    VALIDITY_DATE VARCHAR(50) DEFAULT '2026 Vigente',
    SOURCE_URL VARCHAR(500),
    CHECKSUM VARCHAR(64),
    SUMMARY TEXT,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS DOCUMENT_CHUNKS (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    DOCUMENT_ID NUMBER REFERENCES CURATED_DOCUMENTS(ID),
    CHUNK_INDEX NUMBER NOT NULL,
    CONTENT TEXT NOT NULL,
    ARTICLE_REFERENCE VARCHAR(100),
    PAGE_NUMBER NUMBER DEFAULT 1,
    TOKEN_COUNT NUMBER DEFAULT 0,
    EMBEDDING VECTOR(FLOAT, 768), -- Soporte vectorial nativo Snowflake Cortex
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS DEPARTMENTS (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    CODE VARCHAR(50) UNIQUE NOT NULL,
    NAME VARCHAR(200) NOT NULL,
    DESCRIPTION TEXT,
    CONTACT_EMAIL VARCHAR(150),
    PHONE VARCHAR(50),
    RESPONSIBLE_OFFICER VARCHAR(150),
    ADDRESS VARCHAR(255),
    ACTIVE BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS PROCEDURES (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    CODE VARCHAR(50) UNIQUE NOT NULL,
    DEPARTMENT_ID NUMBER REFERENCES DEPARTMENTS(ID),
    NAME VARCHAR(200) NOT NULL,
    DESCRIPTION TEXT,
    LEGAL_BASIS TEXT,
    SLA_DAYS NUMBER DEFAULT 15,
    ACTIVE BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS REQUIREMENTS (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    PROCEDURE_ID NUMBER REFERENCES PROCEDURES(ID),
    FIELD_NAME VARCHAR(100) NOT NULL,
    LABEL VARCHAR(200) NOT NULL,
    FIELD_TYPE VARCHAR(50) DEFAULT 'string',
    IS_MANDATORY BOOLEAN DEFAULT TRUE,
    VALIDATION_REGEX VARCHAR(200),
    HELP_TEXT VARCHAR(255)
);

-- =====================================================================
-- ESQUEMA 3: OPERATIONS (Casos ciudadanos y flujo transaccional)
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS OPERATIONS;
USE SCHEMA OPERATIONS;

CREATE TABLE IF NOT EXISTS CASES (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    RADICADO VARCHAR(50) UNIQUE NOT NULL,
    CITIZEN_NAME VARCHAR(150),
    CITIZEN_ID VARCHAR(50),
    CITIZEN_EMAIL VARCHAR(150),
    CITIZEN_PHONE VARCHAR(50),
    ADDRESS VARCHAR(255),
    NEIGHBORHOOD VARCHAR(100),
    CATEGORY VARCHAR(100) NOT NULL,
    TITLE VARCHAR(255) NOT NULL,
    DESCRIPTION TEXT NOT NULL,
    DEPARTMENT_ID NUMBER,
    PROCEDURE_ID NUMBER,
    STATUS VARCHAR(50) DEFAULT 'RADICADO_SIMULADO',
    PRIORITY VARCHAR(20) DEFAULT 'MEDIA',
    CONFIDENCE_SCORE FLOAT DEFAULT 0.85,
    REQUIRES_HUMAN_APPROVAL BOOLEAN DEFAULT FALSE,
    ESCALATION_REASON TEXT,
    ASSIGNED_TO VARCHAR(100),
    SLA_DUE_DATE TIMESTAMP_NTZ,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS CASE_EVENTS (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    CASE_ID NUMBER REFERENCES CASES(ID),
    EVENT_TYPE VARCHAR(50) NOT NULL,
    ACTOR VARCHAR(100) DEFAULT 'Agente_LangGraph',
    ACTOR_ROLE VARCHAR(50) DEFAULT 'SISTEMA_IA',
    DESCRIPTION TEXT NOT NULL,
    DETAILS_JSON VARIANT,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS CLASSIFICATIONS (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    CASE_ID NUMBER REFERENCES CASES(ID),
    PREDICTED_CATEGORY VARCHAR(100) NOT NULL,
    PREDICTED_DEPARTMENT_CODE VARCHAR(50) NOT NULL,
    CONFIDENCE FLOAT DEFAULT 0.0,
    JUSTIFICATION TEXT,
    APPROVED_BY_HUMAN BOOLEAN DEFAULT FALSE,
    HUMAN_OFFICER_ID VARCHAR(100),
    HUMAN_OVERRIDE_DEPARTMENT_CODE VARCHAR(50),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS APPROVALS (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    CASE_ID NUMBER REFERENCES CASES(ID),
    REQUESTED_ACTION VARCHAR(100) NOT NULL,
    JUSTIFICATION TEXT NOT NULL,
    STATUS VARCHAR(50) DEFAULT 'PENDIENTE',
    OFFICER_ID VARCHAR(100),
    DECISION_NOTES TEXT,
    DECIDED_AT TIMESTAMP_NTZ,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- =====================================================================
-- ESQUEMA 4: ANALYTICS (Vistas y métricas de desempeño y SLA)
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS ANALYTICS;
USE SCHEMA ANALYTICS;

CREATE OR REPLACE VIEW V_CASES_BY_DEPARTMENT AS
SELECT 
    d.NAME AS DEPARTMENT_NAME,
    d.CODE AS DEPARTMENT_CODE,
    COUNT(c.ID) AS TOTAL_CASES,
    SUM(CASE WHEN c.STATUS = 'RESUELTO' THEN 1 ELSE 0 END) AS RESOLVED_CASES,
    SUM(CASE WHEN c.STATUS = 'ESCALADO_HUMANO' THEN 1 ELSE 0 END) AS ESCALATED_CASES
FROM CURATED.DEPARTMENTS d
LEFT JOIN OPERATIONS.CASES c ON c.DEPARTMENT_ID = d.ID
GROUP BY d.ID, d.NAME, d.CODE;

CREATE OR REPLACE VIEW V_SLA_RISK_MONITOR AS
SELECT 
    c.RADICADO,
    c.TITLE,
    c.CATEGORY,
    c.ASSIGNED_TO,
    c.SLA_DUE_DATE,
    DATEDIFF('hour', CURRENT_TIMESTAMP(), c.SLA_DUE_DATE) AS HOURS_REMAINING,
    CASE 
        WHEN c.SLA_DUE_DATE < CURRENT_TIMESTAMP() THEN 'VENCIDO'
        WHEN DATEDIFF('hour', CURRENT_TIMESTAMP(), c.SLA_DUE_DATE) <= 48 THEN 'PROXIMO_A_VENCER'
        ELSE 'EN_TERMINO'
    END AS SLA_STATUS
FROM OPERATIONS.CASES c
WHERE c.STATUS != 'RESUELTO' AND c.SLA_DUE_DATE IS NOT NULL;

-- =====================================================================
-- ESQUEMA 5: GOVERNANCE (Auditoría, trazabilidad y control de acceso)
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS GOVERNANCE;
USE SCHEMA GOVERNANCE;

CREATE TABLE IF NOT EXISTS SOURCE_REGISTRY (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    NAME VARCHAR(150) NOT NULL,
    ENTITY VARCHAR(150) DEFAULT 'Alcaldía Distrital de Barranquilla',
    BASE_URL VARCHAR(500) NOT NULL,
    ACCESS_TYPE VARCHAR(50) DEFAULT 'PÚBLICA',
    LICENSE VARCHAR(100) DEFAULT 'Datos Abiertos Colombia',
    LAST_VERIFIED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    STATUS VARCHAR(50) DEFAULT 'VIGENTE'
);

CREATE TABLE IF NOT EXISTS ACCESS_AUDIT (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    USER_OR_SESSION VARCHAR(100) DEFAULT 'ciudadano_anonimo',
    ACTION VARCHAR(100) NOT NULL,
    RESOURCE VARCHAR(200) NOT NULL,
    IP_ADDRESS VARCHAR(50) DEFAULT '127.0.0.1',
    STATUS VARCHAR(50) DEFAULT 'AUTHORIZED',
    TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- =====================================================================
-- POBLACIÓN OFICIAL DE DATOS PARA SNOWSIGHT (CARGA COMPLETA)
-- =====================================================================
USE DATABASE BARRANQUILLA_CITIZEN_DB;
USE SCHEMA CURATED;

MERGE INTO CURATED.DEPARTMENTS t USING (SELECT 'DEP_ALUMBRADO' as code, 'Concesión de Alumbrado Público / K-YENA' as name, 'Entidad operadora a cargo del mantenimiento, expansión y reparación de luminarias y postes de alumbrado público en el Distrito de Barranquilla.' as description, 'atencion@kyena.co' as contact_email, '(605) 339 9999' as phone, 'Ing. Carlos Mendoza (Gerente Operativo)' as responsible_officer, 'Vía 40 No. 67-12, Barranquilla' as address) s ON t.CODE = s.code WHEN MATCHED THEN UPDATE SET t.NAME = s.name, t.CONTACT_EMAIL = s.contact_email, t.RESPONSIBLE_OFFICER = s.responsible_officer WHEN NOT MATCHED THEN INSERT (CODE, NAME, DESCRIPTION, CONTACT_EMAIL, PHONE, RESPONSIBLE_OFFICER, ADDRESS) VALUES (s.code, s.name, s.description, s.contact_email, s.phone, s.responsible_officer, s.address);
MERGE INTO CURATED.DEPARTMENTS t USING (SELECT 'DEP_ESPACIO_PUBLICO' as code, 'Secretaría de Control Urbano y Espacio Público' as name, 'Dependencia responsable de la recuperación, preservación, control de ocupación indebida y licencias de uso temporal del espacio público distrital.' as description, 'espaciopublico@barranquilla.gov.co' as contact_email, '(605) 370 3300 Ext. 120' as phone, 'Dra. Shirley Ruiz (Secretaria Distrital)' as responsible_officer, 'Paseo Bolívar, Calle 34 No. 43-31, Piso 3' as address) s ON t.CODE = s.code WHEN MATCHED THEN UPDATE SET t.NAME = s.name, t.CONTACT_EMAIL = s.contact_email, t.RESPONSIBLE_OFFICER = s.responsible_officer WHEN NOT MATCHED THEN INSERT (CODE, NAME, DESCRIPTION, CONTACT_EMAIL, PHONE, RESPONSIBLE_OFFICER, ADDRESS) VALUES (s.code, s.name, s.description, s.contact_email, s.phone, s.responsible_officer, s.address);
MERGE INTO CURATED.DEPARTMENTS t USING (SELECT 'DEP_HACIENDA' as code, 'Secretaría Distrital de Hacienda' as name, 'Administración, recaudo, fiscalización y cobro de los tributos distritales: Impuesto Predial Unificado, Industria y Comercio (ICA) y sobretasas.' as description, 'atencionalciudadanotributario@barranquilla.gov.co' as contact_email, '(605) 370 3300 Ext. 210' as phone, 'Dr. Fidel Cassiani (Secretario de Hacienda)' as responsible_officer, 'Alcaldía Paseo Bolívar, Calle 34 No. 43-31, Piso 1' as address) s ON t.CODE = s.code WHEN MATCHED THEN UPDATE SET t.NAME = s.name, t.CONTACT_EMAIL = s.contact_email, t.RESPONSIBLE_OFFICER = s.responsible_officer WHEN NOT MATCHED THEN INSERT (CODE, NAME, DESCRIPTION, CONTACT_EMAIL, PHONE, RESPONSIBLE_OFFICER, ADDRESS) VALUES (s.code, s.name, s.description, s.contact_email, s.phone, s.responsible_officer, s.address);
MERGE INTO CURATED.DEPARTMENTS t USING (SELECT 'DEP_GESTION_SOCIAL' as code, 'Secretaría de Gestión Social (Sisbén Distrital)' as name, 'Coordinación del programa Sisbén IV, focalización socioeconómica de hogares, encuestas, actualización de fichas y programas sociales distritales.' as description, 'sisben@barranquilla.gov.co' as contact_email, '(605) 370 3300 Ext. 350' as phone, 'Dra. Ismaelina Restrepo (Directora Sisbén)' as responsible_officer, 'Carrera 43 No. 35-38, Barranquilla' as address) s ON t.CODE = s.code WHEN MATCHED THEN UPDATE SET t.NAME = s.name, t.CONTACT_EMAIL = s.contact_email, t.RESPONSIBLE_OFFICER = s.responsible_officer WHEN NOT MATCHED THEN INSERT (CODE, NAME, DESCRIPTION, CONTACT_EMAIL, PHONE, RESPONSIBLE_OFFICER, ADDRESS) VALUES (s.code, s.name, s.description, s.contact_email, s.phone, s.responsible_officer, s.address);
MERGE INTO CURATED.DEPARTMENTS t USING (SELECT 'DEP_SALUD' as code, 'Secretaría Distrital de Salud' as name, 'Vigilancia epidemiológica distrital, inspección, vigilancia y control sanitario, prevención de enfermedades transmitidas por vectores (dengue) y quejas de atención médica.' as description, 'saludpublica@barranquilla.gov.co' as contact_email, '(605) 379 3333' as phone, 'Dr. Stephanie Araujo (Secretaria de Salud)' as responsible_officer, 'Carrera 45 No. 54-55, Barranquilla' as address) s ON t.CODE = s.code WHEN MATCHED THEN UPDATE SET t.NAME = s.name, t.CONTACT_EMAIL = s.contact_email, t.RESPONSIBLE_OFFICER = s.responsible_officer WHEN NOT MATCHED THEN INSERT (CODE, NAME, DESCRIPTION, CONTACT_EMAIL, PHONE, RESPONSIBLE_OFFICER, ADDRESS) VALUES (s.code, s.name, s.description, s.contact_email, s.phone, s.responsible_officer, s.address);
MERGE INTO CURATED.DEPARTMENTS t USING (SELECT 'DEP_SECRETARIA_GENERAL' as code, 'Secretaría General - Ventanilla Única PQRSD' as name, 'Recepción central, radicación oficial, direccionamiento de peticiones generales, derechos de petición CPACA y quejas institucionales distritales.' as description, 'atencionalciudadano@barranquilla.gov.co' as contact_email, '(605) 370 3300' as phone, 'Dra. María Patricia Dávila' as responsible_officer, 'Calle 34 No. 43-31, Ventanilla Única, Barranquilla' as address) s ON t.CODE = s.code WHEN MATCHED THEN UPDATE SET t.NAME = s.name, t.CONTACT_EMAIL = s.contact_email, t.RESPONSIBLE_OFFICER = s.responsible_officer WHEN NOT MATCHED THEN INSERT (CODE, NAME, DESCRIPTION, CONTACT_EMAIL, PHONE, RESPONSIBLE_OFFICER, ADDRESS) VALUES (s.code, s.name, s.description, s.contact_email, s.phone, s.responsible_officer, s.address);

USE SCHEMA OPERATIONS;

MERGE INTO OPERATIONS.CASES t USING (SELECT 'BQL-2026-00101' as radicado, 'Ana Sofía Polo' as citizen_name, '3004567890' as citizen_phone, 'Alumbrado Público' as category, 'Luminaria apagada intermitente en esquina residencial' as title, 'La luminaria ubicada frente a la carrera 53 # 79-112 lleva 4 días titilando y se apaga a las 8pm dejando la cuadra a oscuras.' as description, 'EN_GESTION' as status, 'MEDIA' as priority, 'Agente Inteligente Barranquilla' as assigned_to, '2026-11-13 10:04:32' as sla_due_date, '2026-11-10 10:04:32' as created_at) s ON t.RADICADO = s.radicado WHEN MATCHED THEN UPDATE SET t.STATUS = s.status, t.PRIORITY = s.priority, t.ASSIGNED_TO = s.assigned_to WHEN NOT MATCHED THEN INSERT (RADICADO, CITIZEN_NAME, CITIZEN_PHONE, CATEGORY, TITLE, DESCRIPTION, STATUS, PRIORITY, ASSIGNED_TO, SLA_DUE_DATE, CREATED_AT) VALUES (s.radicado, s.citizen_name, s.citizen_phone, s.category, s.title, s.description, s.status, s.priority, s.assigned_to, s.sla_due_date, s.created_at);
MERGE INTO OPERATIONS.CASES t USING (SELECT 'BQL-2026-00102' as radicado, 'José David Martínez' as citizen_name, '3102345678' as citizen_phone, 'Espacio Público' as category, 'Ocupación indebida de andén peatonal con taller mecánico informal' as title, 'Un taller mecánico colocó carros dañados y llantas sobre todo el andén peatonal impidiendo el paso seguro de peatones y personas en silla de ruedas.' as description, 'PENDIENTE_REVISION' as status, 'ALTA' as priority, 'Agente Inteligente Barranquilla' as assigned_to, '2026-11-18 10:04:32' as sla_due_date, '2026-11-10 20:04:32' as created_at) s ON t.RADICADO = s.radicado WHEN MATCHED THEN UPDATE SET t.STATUS = s.status, t.PRIORITY = s.priority, t.ASSIGNED_TO = s.assigned_to WHEN NOT MATCHED THEN INSERT (RADICADO, CITIZEN_NAME, CITIZEN_PHONE, CATEGORY, TITLE, DESCRIPTION, STATUS, PRIORITY, ASSIGNED_TO, SLA_DUE_DATE, CREATED_AT) VALUES (s.radicado, s.citizen_name, s.citizen_phone, s.category, s.title, s.description, s.status, s.priority, s.assigned_to, s.sla_due_date, s.created_at);
MERGE INTO OPERATIONS.CASES t USING (SELECT 'BQL-2026-00103' as radicado, 'Marta Cecilia Osorio' as citizen_name, '3019876543' as citizen_phone, 'Hacienda Distrital' as category, 'Solicitud de revisión por cobro duplicado en factura de impuesto predial' as title, 'Realicé el pago del impuesto predial 2026 mediante PSE el 15 de enero y me continúa llegando la factura con cobro de intereses moratorios no correspondientes.' as description, 'ESCALADO_HUMANO' as status, 'ALTA' as priority, 'Agente Inteligente Barranquilla' as assigned_to, '2026-11-23 10:04:32' as sla_due_date, '2026-11-09 10:04:32' as created_at) s ON t.RADICADO = s.radicado WHEN MATCHED THEN UPDATE SET t.STATUS = s.status, t.PRIORITY = s.priority, t.ASSIGNED_TO = s.assigned_to WHEN NOT MATCHED THEN INSERT (RADICADO, CITIZEN_NAME, CITIZEN_PHONE, CATEGORY, TITLE, DESCRIPTION, STATUS, PRIORITY, ASSIGNED_TO, SLA_DUE_DATE, CREATED_AT) VALUES (s.radicado, s.citizen_name, s.citizen_phone, s.category, s.title, s.description, s.status, s.priority, s.assigned_to, s.sla_due_date, s.created_at);
MERGE INTO OPERATIONS.CASES t USING (SELECT 'BQL-2026-1004' as radicado, 'Ciudadano Barranquillero' as citizen_name, '3001234567' as citizen_phone, 'Alumbrado Público' as category, 'Reporte de Alumbrado Público en Alto Prado' as title, 'Quiero reportar que la luminaria frente a la Carrera 53 # 72-10 en el barrio Alto Prado esta apagada, mi celular es 3001234567 y poste BQ-4412.' as description, 'RADICADO_SIMULADO' as status, 'MEDIA' as priority, 'Concesión de Alumbrado Público / K-YENA' as assigned_to, '2026-11-14 10:37:32' as sla_due_date, '2026-11-11 10:37:32' as created_at) s ON t.RADICADO = s.radicado WHEN MATCHED THEN UPDATE SET t.STATUS = s.status, t.PRIORITY = s.priority, t.ASSIGNED_TO = s.assigned_to WHEN NOT MATCHED THEN INSERT (RADICADO, CITIZEN_NAME, CITIZEN_PHONE, CATEGORY, TITLE, DESCRIPTION, STATUS, PRIORITY, ASSIGNED_TO, SLA_DUE_DATE, CREATED_AT) VALUES (s.radicado, s.citizen_name, s.citizen_phone, s.category, s.title, s.description, s.status, s.priority, s.assigned_to, s.sla_due_date, s.created_at);
MERGE INTO OPERATIONS.CASES t USING (SELECT 'BQL-2026-1005' as radicado, 'Ciudadano Solicitante' as citizen_name, 'N/A' as citizen_phone, 'Peticiones y Atención General' as category, 'Caso escalado: Activación de salvaguarda de gobernanza por término sensible' as title, 'Quiero denunciar por presunta corrupcion a un funcionario que me pidio soborno en la alcaldia.' as description, 'ESCALADO_HUMANO' as status, 'ALTA' as priority, 'Secretaría General - Ventanilla Única PQRSD' as assigned_to, '2026-11-16 10:38:24' as sla_due_date, '2026-11-11 10:38:24' as created_at) s ON t.RADICADO = s.radicado WHEN MATCHED THEN UPDATE SET t.STATUS = s.status, t.PRIORITY = s.priority, t.ASSIGNED_TO = s.assigned_to WHEN NOT MATCHED THEN INSERT (RADICADO, CITIZEN_NAME, CITIZEN_PHONE, CATEGORY, TITLE, DESCRIPTION, STATUS, PRIORITY, ASSIGNED_TO, SLA_DUE_DATE, CREATED_AT) VALUES (s.radicado, s.citizen_name, s.citizen_phone, s.category, s.title, s.description, s.status, s.priority, s.assigned_to, s.sla_due_date, s.created_at);
MERGE INTO OPERATIONS.CASES t USING (SELECT 'BQL-2026-1006' as radicado, 'Ciudadano Barranquillero' as citizen_name, '3015557788' as citizen_phone, 'Alumbrado Público' as category, 'Reporte de Alumbrado Público en Boston' as title, 'Deseo reportar que la luminaria frente a la Calle 72 # 44-32 en el barrio Boston está rota y apagada. Mi celular es 3015557788 y poste BQ-9912.' as description, 'EN_GESTION' as status, 'MEDIA' as priority, 'Concesión de Alumbrado Público / K-YENA' as assigned_to, '2026-11-14 11:23:02' as sla_due_date, '2026-11-11 11:23:02' as created_at) s ON t.RADICADO = s.radicado WHEN MATCHED THEN UPDATE SET t.STATUS = s.status, t.PRIORITY = s.priority, t.ASSIGNED_TO = s.assigned_to WHEN NOT MATCHED THEN INSERT (RADICADO, CITIZEN_NAME, CITIZEN_PHONE, CATEGORY, TITLE, DESCRIPTION, STATUS, PRIORITY, ASSIGNED_TO, SLA_DUE_DATE, CREATED_AT) VALUES (s.radicado, s.citizen_name, s.citizen_phone, s.category, s.title, s.description, s.status, s.priority, s.assigned_to, s.sla_due_date, s.created_at);
MERGE INTO OPERATIONS.CASES t USING (SELECT 'BQL-2026-1007' as radicado, 'Ciudadano Solicitante' as citizen_name, '3015557788' as citizen_phone, 'Alumbrado Público' as category, 'Reporte de Alumbrado Público en Boston' as title, 'Deseo reportar que la luminaria frente a la Calle 72 # 44-32 en el barrio Boston está rota y apagada. Mi celular es 3015557788 y poste BQ-9912.' as description, 'EN_GESTION' as status, 'MEDIA' as priority, 'Concesión de Alumbrado Público / K-YENA' as assigned_to, '2026-11-14 12:33:25' as sla_due_date, '2026-11-11 12:33:25' as created_at) s ON t.RADICADO = s.radicado WHEN MATCHED THEN UPDATE SET t.STATUS = s.status, t.PRIORITY = s.priority, t.ASSIGNED_TO = s.assigned_to WHEN NOT MATCHED THEN INSERT (RADICADO, CITIZEN_NAME, CITIZEN_PHONE, CATEGORY, TITLE, DESCRIPTION, STATUS, PRIORITY, ASSIGNED_TO, SLA_DUE_DATE, CREATED_AT) VALUES (s.radicado, s.citizen_name, s.citizen_phone, s.category, s.title, s.description, s.status, s.priority, s.assigned_to, s.sla_due_date, s.created_at);
MERGE INTO OPERATIONS.CASES t USING (SELECT 'BQL-2026-1008' as radicado, 'Ciudadano Solicitante' as citizen_name, '3015557788' as citizen_phone, 'Alumbrado Público' as category, 'Reporte de Alumbrado Público en Boston' as title, 'Deseo reportar que la luminaria frente a la Calle 72 # 44-32 en el barrio Boston está rota y apagada. Mi celular es 3015557788 y poste BQ-9912.' as description, 'EN_GESTION' as status, 'MEDIA' as priority, 'Concesión de Alumbrado Público / K-YENA' as assigned_to, '2026-11-14 13:14:08' as sla_due_date, '2026-11-11 13:14:08' as created_at) s ON t.RADICADO = s.radicado WHEN MATCHED THEN UPDATE SET t.STATUS = s.status, t.PRIORITY = s.priority, t.ASSIGNED_TO = s.assigned_to WHEN NOT MATCHED THEN INSERT (RADICADO, CITIZEN_NAME, CITIZEN_PHONE, CATEGORY, TITLE, DESCRIPTION, STATUS, PRIORITY, ASSIGNED_TO, SLA_DUE_DATE, CREATED_AT) VALUES (s.radicado, s.citizen_name, s.citizen_phone, s.category, s.title, s.description, s.status, s.priority, s.assigned_to, s.sla_due_date, s.created_at);

-- =====================================================================
-- CONSULTAS DE VERIFICACIÓN EN SNOWSIGHT
-- =====================================================================
SELECT * FROM OPERATIONS.CASES ORDER BY CREATED_AT DESC;
SELECT * FROM ANALYTICS.V_CASES_BY_DEPARTMENT;
SELECT * FROM ANALYTICS.V_SLA_RISK_MONITOR;
