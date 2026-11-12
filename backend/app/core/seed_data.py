from datetime import datetime, timedelta
import json
from backend.app.core.database import (
    SessionLocal, Department, Procedure, Requirement, Case, CaseEvent,
    Classification, SourceRegistry
)

def seed_database():
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Department).first():
            return

        print("--> Inicializando Catálogo Oficial de la Alcaldía Distrital de Barranquilla...")

        # 1. Dependencias
        dept_alumbrado = Department(
            code="DEP_ALUMBRADO",
            name="Concesión de Alumbrado Público / K-YENA",
            description="Entidad operadora a cargo del mantenimiento, expansión y reparación de luminarias y postes de alumbrado público en el Distrito de Barranquilla.",
            contact_email="atencion@kyena.co",
            phone="(605) 339 9999",
            responsible_officer="Ing. Carlos Mendoza (Gerente Operativo)",
            address="Vía 40 No. 67-12, Barranquilla",
            active=True
        )

        dept_espacio = Department(
            code="DEP_ESPACIO_PUBLICO",
            name="Secretaría de Control Urbano y Espacio Público",
            description="Dependencia responsable de la recuperación, preservación, control de ocupación indebida y licencias de uso temporal del espacio público distrital.",
            contact_email="espaciopublico@barranquilla.gov.co",
            phone="(605) 370 3300 Ext. 120",
            responsible_officer="Dra. Shirley Ruiz (Secretaria Distrital)",
            address="Paseo Bolívar, Calle 34 No. 43-31, Piso 3",
            active=True
        )

        dept_hacienda = Department(
            code="DEP_HACIENDA",
            name="Secretaría Distrital de Hacienda",
            description="Administración, recaudo, fiscalización y cobro de los tributos distritales: Impuesto Predial Unificado, Industria y Comercio (ICA) y sobretasas.",
            contact_email="atencionalciudadanotributario@barranquilla.gov.co",
            phone="(605) 370 3300 Ext. 210",
            responsible_officer="Dr. Fidel Cassiani (Secretario de Hacienda)",
            address="Alcaldía Paseo Bolívar, Calle 34 No. 43-31, Piso 1",
            active=True
        )

        dept_gestion_social = Department(
            code="DEP_GESTION_SOCIAL",
            name="Secretaría de Gestión Social (Sisbén Distrital)",
            description="Coordinación del programa Sisbén IV, focalización socioeconómica de hogares, encuestas, actualización de fichas y programas sociales distritales.",
            contact_email="sisben@barranquilla.gov.co",
            phone="(605) 370 3300 Ext. 350",
            responsible_officer="Dra. Ismaelina Restrepo (Directora Sisbén)",
            address="Carrera 43 No. 35-38, Barranquilla",
            active=True
        )

        dept_salud = Department(
            code="DEP_SALUD",
            name="Secretaría Distrital de Salud",
            description="Vigilancia epidemiológica distrital, inspección, vigilancia y control sanitario, prevención de enfermedades transmitidas por vectores (dengue) y quejas de atención médica.",
            contact_email="saludpublica@barranquilla.gov.co",
            phone="(605) 379 3333",
            responsible_officer="Dr. Stephanie Araujo (Secretaria de Salud)",
            address="Carrera 45 No. 54-55, Barranquilla",
            active=True
        )

        dept_general = Department(
            code="DEP_SECRETARIA_GENERAL",
            name="Secretaría General - Ventanilla Única PQRSD",
            description="Recepción central, radicación oficial, direccionamiento de peticiones generales, derechos de petición CPACA y quejas institucionales distritales.",
            contact_email="atencionalciudadano@barranquilla.gov.co",
            phone="(605) 370 3300",
            responsible_officer="Dra. María Patricia Dávila",
            address="Calle 34 No. 43-31, Ventanilla Única, Barranquilla",
            active=True
        )

        db.add_all([dept_alumbrado, dept_espacio, dept_hacienda, dept_gestion_social, dept_salud, dept_general])
        db.commit()

        # 2. Procedimientos
        proc_alumbrado = Procedure(
            code="PROC_ALUMBRADO_FALLA",
            department_id=dept_alumbrado.id,
            name="Reporte de Falla o Daño en Luminaria de Alumbrado Público",
            description="Recepción y trámite de reportes ciudadanos por luminarias apagadas, postes con riesgo de caída o sectores a oscuras en Barranquilla.",
            legal_basis="Decreto Distrital 0180 de 2017 y Contrato de Concesión K-YENA",
            sla_days=3,
            active=True
        )

        proc_espacio = Procedure(
            code="PROC_ESPACIO_OCUPACION",
            department_id=dept_espacio.id,
            name="Denuncia por Ocupación Indebida o Bloqueo de Espacio Público",
            description="Atención a quejas por andenes invadidos por escombros, cerramientos no autorizados o ventas informales sin permiso distrital.",
            legal_basis="Código Nacional de Seguridad y Convivencia Ciudadana (Ley 1801 de 2016)",
            sla_days=10,
            active=True
        )

        proc_predial = Procedure(
            code="PROC_PREDIAL_CONSULTA",
            department_id=dept_hacienda.id,
            name="Consulta, Liquidación y Facturación de Impuesto Predial Unificado",
            description="Orientación tributaria, expedición de factura predial, información de fechas de descuento por pronto pago y acuerdos de pago.",
            legal_basis="Estatuto Tributario Distrital - Decreto 0119 de 2019",
            sla_days=15,
            active=True
        )

        proc_sisben = Procedure(
            code="PROC_SISBEN_ENCUESTA",
            department_id=dept_gestion_social.id,
            name="Solicitud de Nueva Encuesta o Modificación de Ficha Sisbén IV",
            description="Registro y agendamiento de visita socioeconómica para asignación o reclasificación en grupos A, B, C o D de Sisbén IV.",
            legal_basis="CONPES 3877 y Resolución DNP 1254",
            sla_days=20,
            active=True
        )

        proc_salud = Procedure(
            code="PROC_SALUD_VECTORES",
            department_id=dept_salud.id,
            name="Reporte de Foco Sanitario e Inspección para Prevención de Dengue",
            description="Visita de técnicos de salud ambiental para control de criaderos de mosquitos Aedes aegypti y fumigación focalizada.",
            legal_basis="Ley 9 de 1979 - Código Sanitario Nacional",
            sla_days=5,
            active=True
        )

        db.add_all([proc_alumbrado, proc_espacio, proc_predial, proc_sisben, proc_salud])
        db.commit()

        # 3. Requisitos por Procedimiento
        reqs = [
            # Alumbrado
            Requirement(procedure_id=proc_alumbrado.id, field_name="address", label="Dirección exacta del poste o luminaria", field_type="location", is_mandatory=True, help_text="Ejemplo: Calle 72 # 44-32"),
            Requirement(procedure_id=proc_alumbrado.id, field_name="neighborhood", label="Barrio", field_type="string", is_mandatory=True, help_text="Ejemplo: Boston, El Prado, Riomar"),
            Requirement(procedure_id=proc_alumbrado.id, field_name="pole_number", label="Número de poste o referencia visible", field_type="string", is_mandatory=False, help_text="Placa amarilla o metálica en el poste"),
            Requirement(procedure_id=proc_alumbrado.id, field_name="citizen_phone", label="Teléfono de contacto", field_type="phone", is_mandatory=True, help_text="Celular de 10 dígitos para seguimiento"),

            # Espacio Público
            Requirement(procedure_id=proc_espacio.id, field_name="address", label="Ubicación exacta del predio o andén ocupado", field_type="location", is_mandatory=True, help_text="Calle, Carrera o intersección"),
            Requirement(procedure_id=proc_espacio.id, field_name="neighborhood", label="Barrio", field_type="string", is_mandatory=True, help_text="Barrio de Barranquilla"),
            Requirement(procedure_id=proc_espacio.id, field_name="infraction_type", label="Tipo de ocupación indebida", field_type="string", is_mandatory=True, help_text="Escombros, reja fija, caseta informal, talleres en vía pública"),

            # Predial
            Requirement(procedure_id=proc_predial.id, field_name="cadastral_code", label="Referencia Catastral o Dirección del Predio", field_type="string", is_mandatory=True, help_text="Código de 15 dígitos o dirección que figura en la escritura"),
            Requirement(procedure_id=proc_predial.id, field_name="citizen_id", label="Cédula de Ciudadanía del Propietario", field_type="string", is_mandatory=True, help_text="Documento de identidad"),

            # Sisbén
            Requirement(procedure_id=proc_sisben.id, field_name="citizen_name", label="Nombre completo del solicitante", field_type="string", is_mandatory=True, help_text="Nombres y apellidos"),
            Requirement(procedure_id=proc_sisben.id, field_name="citizen_id", label="Cédula de Ciudadanía", field_type="string", is_mandatory=True, help_text="Número de documento"),
            Requirement(procedure_id=proc_sisben.id, field_name="address", label="Dirección de residencia en Barranquilla", field_type="location", is_mandatory=True, help_text="Dirección donde habita el hogar a encuestar"),
            Requirement(procedure_id=proc_sisben.id, field_name="neighborhood", label="Barrio", field_type="string", is_mandatory=True, help_text="Barrio residencial"),
        ]
        db.add_all(reqs)
        db.commit()

        # 4. Registro de Fuentes Oficiales (Governance)
        sources = [
            SourceRegistry(
                name="Portal Oficial Alcaldía de Barranquilla",
                entity="Alcaldía Distrital de Barranquilla",
                base_url="https://www.barranquilla.gov.co/",
                access_type="PÚBLICA",
                license="Gobierno Digital Colombia",
                status="VIGENTE"
            ),
            SourceRegistry(
                name="Portal Datos Abiertos Colombia",
                entity="MinTIC / Alcaldía Distrital de Barranquilla",
                base_url="https://www.datos.gov.co/",
                access_type="PÚBLICA",
                license="Open Data Commons",
                status="VIGENTE"
            ),
            SourceRegistry(
                name="Sistema Único de Información de Trámites (SUIT)",
                entity="Departamento Administrativo de la Función Pública",
                base_url="https://www.funcionpublica.gov.co/web/suit",
                access_type="PÚBLICA",
                license="Oficial Institucional",
                status="VIGENTE"
            ),
            SourceRegistry(
                name="Operación Concesión de Alumbrado Público K-YENA",
                entity="Alcaldía de Barranquilla / K-YENA SAS",
                base_url="https://kyena.co/canales-atencion",
                access_type="PÚBLICA",
                license="Contrato 0180-2017",
                status="VIGENTE"
            )
        ]
        db.add_all(sources)
        db.commit()

        # 5. Casos de Demostración para el Panel Administrativo (Historial real)
        case1 = Case(
            radicado="BQL-2026-00101",
            citizen_name="Ana Sofía Polo",
            citizen_id="1143229871",
            citizen_email="aspolo@gmail.com",
            citizen_phone="3004567890",
            address="Carrera 53 # 79-112",
            neighborhood="Alto Prado",
            category="Alumbrado Público",
            title="Luminaria apagada intermitente en esquina residencial",
            description="La luminaria ubicada frente a la carrera 53 # 79-112 lleva 4 días titilando y se apaga a las 8pm dejando la cuadra a oscuras.",
            department_id=dept_alumbrado.id,
            procedure_id=proc_alumbrado.id,
            status="EN_GESTION",
            priority="MEDIA",
            confidence_score=0.96,
            requires_human_approval=False,
            sla_due_date=datetime.utcnow() + timedelta(days=2),
            created_at=datetime.utcnow() - timedelta(days=1)
        )

        case2 = Case(
            radicado="BQL-2026-00102",
            citizen_name="José David Martínez",
            citizen_id="72198453",
            citizen_email="josedavid.m@outlook.com",
            citizen_phone="3102345678",
            address="Calle 45 # 21B-40",
            neighborhood="San José",
            category="Espacio Público",
            title="Ocupación indebida de andén peatonal con taller mecánico informal",
            description="Un taller mecánico colocó carros dañados y llantas sobre todo el andén peatonal impidiendo el paso seguro de peatones y personas en silla de ruedas.",
            department_id=dept_espacio.id,
            procedure_id=proc_espacio.id,
            status="PENDIENTE_REVISION",
            priority="ALTA",
            confidence_score=0.92,
            requires_human_approval=False,
            sla_due_date=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow() - timedelta(hours=14)
        )

        case3 = Case(
            radicado="BQL-2026-00103",
            citizen_name="Marta Cecilia Osorio",
            citizen_id="32876543",
            citizen_email="marta.osorio@yahoo.es",
            citizen_phone="3019876543",
            address="Calle 84 # 42D-15",
            neighborhood="Los Alpes",
            category="Hacienda Distrital",
            title="Solicitud de revisión por cobro duplicado en factura de impuesto predial",
            description="Realicé el pago del impuesto predial 2026 mediante PSE el 15 de enero y me continúa llegando la factura con cobro de intereses moratorios no correspondientes.",
            department_id=dept_hacienda.id,
            procedure_id=proc_predial.id,
            status="ESCALADO_HUMANO",
            priority="ALTA",
            confidence_score=0.88,
            requires_human_approval=True,
            escalation_reason="Disputa tributaria y verificación financiera que requiere autorización de funcionario de Hacienda según marco normativo CPACA.",
            sla_due_date=datetime.utcnow() + timedelta(days=12),
            created_at=datetime.utcnow() - timedelta(days=2)
        )

        db.add_all([case1, case2, case3])
        db.commit()

        # Eventos para los casos de prueba
        ev1 = CaseEvent(
            case_id=case1.id,
            event_type="CREACION",
            actor="Agente_LangGraph",
            actor_role="SISTEMA_IA",
            description="Solicitud interpretada y clasificada automáticamente como Alumbrado Público.",
            details_json=json.dumps({"poste": "Desconocido", "barrio": "Alto Prado", "canal": "Portal Ciudadano"})
        )
        ev2 = CaseEvent(
            case_id=case1.id,
            event_type="ASIGNACION",
            actor="Agente_LangGraph",
            actor_role="SISTEMA_IA",
            description="Caso enrutado a K-YENA SAS con SLA operativo de 72 horas.",
            details_json=json.dumps({"concesion": "K-YENA", "sla_horas": 72})
        )

        ev3 = CaseEvent(
            case_id=case3.id,
            event_type="ESCALAMIENTO",
            actor="Agente_LangGraph",
            actor_role="SISTEMA_IA",
            description="Caso escalado a funcionario humano: cobro tributario y revisión de soporte bancario.",
            details_json=json.dumps({"regla": "REGLA_GOBERNANZA_04_DISPUTA_FINANCIERA"})
        )

        db.add_all([ev1, ev2, ev3])
        db.commit()

        # Clasificaciones vinculadas
        cl1 = Classification(
            case_id=case1.id,
            predicted_category="Alumbrado Público",
            predicted_department_code="DEP_ALUMBRADO",
            confidence=0.96,
            justification="Luminaria intermitente y sector a oscuras en vía pública.",
            approved_by_human=True,
            human_officer_id="OP_BARRANQUILLA_01"
        )
        cl3 = Classification(
            case_id=case3.id,
            predicted_category="Hacienda Distrital",
            predicted_department_code="DEP_HACIENDA",
            confidence=0.88,
            justification="Reclamo sobre pago predial PSE no aplicado.",
            approved_by_human=False
        )
        db.add_all([cl1, cl3])
        db.commit()

        print("--> Catálogo y datos iniciales de Barranquilla creados con éxito.")
    finally:
        db.close()

if __name__ == "__main__":
    from backend.app.core.database import init_db
    init_db()
    seed_database()
