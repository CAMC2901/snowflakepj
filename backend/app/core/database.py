import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from backend.app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 1. RAW SCHEMA (Ingesta cruda y auditoría)
# ==========================================

class RawDocument(Base):
    __tablename__ = "raw_documents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    url = Column(String(500), nullable=True)
    entity = Column(String(100), default="Alcaldía Distrital de Barranquilla")
    format = Column(String(20), default="PDF")
    checksum = Column(String(64), nullable=True)
    file_size = Column(Integer, default=0)
    raw_content = Column(Text, nullable=True)
    status = Column(String(50), default="CAPTURED")
    captured_at = Column(DateTime, default=datetime.utcnow)

class IngestionLog(Base):
    __tablename__ = "ingestion_log"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    action = Column(String(50), default="INDEX")
    chunks_count = Column(Integer, default=0)
    status = Column(String(50), default="SUCCESS")
    duration_ms = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==========================================
# 2. CURATED SCHEMA (Conocimiento depurado)
# ==========================================

class CuratedDocument(Base):
    __tablename__ = "curated_documents"
    id = Column(Integer, primary_key=True, index=True)
    doc_code = Column(String(50), unique=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), index=True)
    authority = Column(String(150), default="Alcaldía Distrital de Barranquilla")
    validity_date = Column(String(50), default="2026 Vigente")
    source_url = Column(String(500), nullable=True)
    checksum = Column(String(64), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("curated_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    article_reference = Column(String(100), nullable=True)
    page_number = Column(Integer, default=1)
    token_count = Column(Integer, default=0)
    embedding_json = Column(Text, nullable=True)  # JSON array with 768 dims
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("CuratedDocument", back_populates="chunks")

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    contact_email = Column(String(150), nullable=True)
    phone = Column(String(50), nullable=True)
    responsible_officer = Column(String(150), nullable=True)
    address = Column(String(255), nullable=True)
    active = Column(Boolean, default=True)

    procedures = relationship("Procedure", back_populates="department")
    cases = relationship("Case", back_populates="department")

class Procedure(Base):
    __tablename__ = "procedures"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    legal_basis = Column(Text, nullable=True)
    sla_days = Column(Integer, default=15)
    active = Column(Boolean, default=True)

    department = relationship("Department", back_populates="procedures")
    requirements = relationship("Requirement", back_populates="procedure", cascade="all, delete-orphan")

class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(Integer, primary_key=True, index=True)
    procedure_id = Column(Integer, ForeignKey("procedures.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    field_type = Column(String(50), default="string")  # string, email, phone, location
    is_mandatory = Column(Boolean, default=True)
    validation_regex = Column(String(200), nullable=True)
    help_text = Column(String(255), nullable=True)

    procedure = relationship("Procedure", back_populates="requirements")

# ==========================================
# 3. OPERATIONS SCHEMA (Casos y flujo real)
# ==========================================

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    radicado = Column(String(50), unique=True, index=True)  # ej. BQL-2026-00101
    citizen_name = Column(String(150), nullable=True)
    citizen_id = Column(String(50), nullable=True)
    citizen_email = Column(String(150), nullable=True)
    citizen_phone = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    neighborhood = Column(String(100), nullable=True)  # Barrio en Barranquilla
    category = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    procedure_id = Column(Integer, ForeignKey("procedures.id"), nullable=True)
    status = Column(String(50), default="RADICADO_SIMULADO") # PENDIENTE_REVISION, EN_GESTION, ESCALADO_HUMANO, RESUELTO
    priority = Column(String(20), default="MEDIA") # ALTA, MEDIA, BAJA
    confidence_score = Column(Float, default=0.85)
    requires_human_approval = Column(Boolean, default=False)
    escalation_reason = Column(Text, nullable=True)
    assigned_to = Column(String(100), default="Agente Inteligente Barranquilla")
    sla_due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="cases")
    events = relationship("CaseEvent", back_populates="case", cascade="all, delete-orphan")
    classification = relationship("Classification", back_populates="case", uselist=False, cascade="all, delete-orphan")

class CaseEvent(Base):
    __tablename__ = "case_events"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    event_type = Column(String(50), nullable=False) # CREACION, CLASIFICACION, VALIDACION, ESCALAMIENTO, ACTUALIZACION
    actor = Column(String(100), default="Agente_LangGraph")
    actor_role = Column(String(50), default="SISTEMA_IA")
    description = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="events")

class Classification(Base):
    __tablename__ = "classifications"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    predicted_category = Column(String(100), nullable=False)
    predicted_department_code = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0)
    justification = Column(Text, nullable=True)
    approved_by_human = Column(Boolean, default=False)
    human_officer_id = Column(String(100), nullable=True)
    human_override_department_code = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="classification")

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    requested_action = Column(String(100), nullable=False)
    justification = Column(Text, nullable=False)
    status = Column(String(50), default="PENDIENTE") # PENDIENTE, APROBADO, RECHAZADO
    officer_id = Column(String(100), nullable=True)
    decision_notes = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==========================================
# 4. GOVERNANCE & AUDIT SCHEMA
# ==========================================

class SourceRegistry(Base):
    __tablename__ = "source_registry"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    entity = Column(String(150), default="Alcaldía Distrital de Barranquilla")
    base_url = Column(String(500), nullable=False)
    access_type = Column(String(50), default="PÚBLICA")
    license = Column(String(100), default="Datos Abiertos Colombia")
    last_verified_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="VIGENTE")

class AccessAudit(Base):
    __tablename__ = "access_audit"
    id = Column(Integer, primary_key=True, index=True)
    user_or_session = Column(String(100), default="ciudadano_anonimo")
    action = Column(String(100), nullable=False)
    resource = Column(String(200), nullable=False)
    ip_address = Column(String(50), default="127.0.0.1")
    status = Column(String(50), default="AUTHORIZED")
    timestamp = Column(DateTime, default=datetime.utcnow)

class ModelEval(Base):
    __tablename__ = "model_evals"
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(String(50), nullable=False)
    query = Column(Text, nullable=False)
    expected_department = Column(String(50), nullable=False)
    predicted_department = Column(String(50), nullable=False)
    correct = Column(Boolean, default=False)
    retrieved_chunk_ids = Column(String(255), nullable=True)
    confidence_score = Column(Float, default=0.0)
    evaluated_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
