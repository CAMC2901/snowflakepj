import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.core.database import Case, CaseEvent, Classification, Department, Procedure

def generate_radicado_number(db: Session) -> str:
    count = db.query(Case).count()
    return f"BQL-2026-{1000 + count + 1}"

def tool_create_case_draft(
    payload: Dict[str, Any],
    db: Session,
    actor: str = "Agente_LangGraph"
) -> Dict[str, Any]:
    """Herramienta create_case_draft: Registra un caso en modo simulación (Sandbox) con número de radicado trazable."""
    radicado = generate_radicado_number(db)
    
    sla_days = payload.get("sla_days", 15)
    sla_due = datetime.utcnow() + timedelta(days=sla_days)
    
    requires_approval = payload.get("requires_human_approval", False)
    initial_status = "ESCALADO_HUMANO" if requires_approval else "RADICADO_SIMULADO"
    
    new_case = Case(
        radicado=radicado,
        citizen_name=payload.get("citizen_name", "Ciudadano Solicitante"),
        citizen_id=payload.get("citizen_id", ""),
        citizen_email=payload.get("citizen_email", ""),
        citizen_phone=payload.get("citizen_phone", ""),
        address=payload.get("address", ""),
        neighborhood=payload.get("neighborhood", ""),
        category=payload.get("category", "General"),
        title=payload.get("title", payload.get("description", "Solicitud Ciudadana")[:80]),
        description=payload.get("description", ""),
        department_id=payload.get("department_id"),
        procedure_id=payload.get("procedure_id"),
        status=initial_status,
        priority=payload.get("priority", "MEDIA"),
        confidence_score=payload.get("confidence_score", 0.85),
        requires_human_approval=requires_approval,
        escalation_reason=payload.get("escalation_reason", None),
        assigned_to=payload.get("department_name", "Dependencia Competente"),
        sla_due_date=sla_due
    )
    
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    
    # Registrar evento de creación
    event = CaseEvent(
        case_id=new_case.id,
        event_type="CREACION_SIMULADA",
        actor=actor,
        actor_role="AGENTE_IA",
        description=f"Caso generado en entorno sandbox con radicado provisional {radicado}.",
        details_json=json.dumps({
            "entorno": "SANDBOX_DEMO",
            "sla_dias": sla_days,
            "categoria": new_case.category,
            "requiere_aprobacion": requires_approval
        })
    )
    db.add(event)
    
    # Registrar clasificación
    classification = Classification(
        case_id=new_case.id,
        predicted_category=new_case.category,
        predicted_department_code=payload.get("department_code", "DEP_GENERAL"),
        confidence=new_case.confidence_score,
        justification=payload.get("justification", "Clasificado automáticamente por el agente."),
        approved_by_human=False
    )
    db.add(classification)
    db.commit()

    return {
        "status": "SUCCESS",
        "radicado": radicado,
        "case_id": new_case.id,
        "category": new_case.category,
        "department_name": new_case.assigned_to,
        "sla_due_date": sla_due.strftime("%Y-%m-%d"),
        "sla_days": sla_days,
        "current_status": new_case.status,
        "requires_human_approval": requires_approval,
        "message": f"Caso registrado exitosamente en el entorno de demostración con radicado {radicado}. Nota: Operación en modo Sandbox (sin efectos jurídicos vinculantes hasta integración oficial)."
    }

def tool_get_case_status(radicado: str, db: Session) -> Dict[str, Any]:
    """Herramienta get_case_status: Consulta el estado por radicado, trazabilidad y estado de SLA."""
    radicado_clean = radicado.strip().upper()
    case = db.query(Case).filter(Case.radicado == radicado_clean).first()
    
    if not case:
        return {
            "status": "NOT_FOUND",
            "radicado": radicado,
            "message": f"No se encontró ningún caso registrado con el radicado {radicado}."
        }
        
    events = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).order_by(CaseEvent.created_at.asc()).all()
    events_data = [
        {
            "event_type": ev.event_type,
            "actor": ev.actor,
            "description": ev.description,
            "timestamp": ev.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for ev in events
    ]
    
    # Cálculo de alerta de SLA
    now = datetime.utcnow()
    is_at_risk = False
    sla_status_str = "DENTRO_DEL_TERMINO"
    if case.sla_due_date:
        remaining_days = (case.sla_due_date - now).total_seconds() / 86400.0
        if remaining_days < 0:
            sla_status_str = "VENCIDO"
            is_at_risk = True
        elif remaining_days <= 2:
            sla_status_str = "PROXIMO_A_VENCER"
            is_at_risk = True
            
    return {
        "status": "SUCCESS",
        "radicado": case.radicado,
        "title": case.title,
        "citizen_name": case.citizen_name,
        "category": case.category,
        "current_status": case.status,
        "priority": case.priority,
        "assigned_to": case.assigned_to,
        "created_at": case.created_at.strftime("%Y-%m-%d %H:%M"),
        "sla_due_date": case.sla_due_date.strftime("%Y-%m-%d") if case.sla_due_date else "No definida",
        "sla_status": sla_status_str,
        "is_at_risk": is_at_risk,
        "requires_human_approval": case.requires_human_approval,
        "events_count": len(events_data),
        "history": events_data
    }
