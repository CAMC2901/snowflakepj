import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.core.database import (
    get_db, Case, CaseEvent, Classification, Department, Procedure
)

router = APIRouter(prefix="/cases", tags=["Casos"])

class ApproveClassificationRequest(BaseModel):
    officer_id: str = "OFICIAL_OPERACIONES_01"
    override_department_code: Optional[str] = None
    notes: Optional[str] = "Clasificación revisada y avalada por operador institucional."

class UpdateStatusRequest(BaseModel):
    new_status: str # PENDIENTE_REVISION, EN_GESTION, ESCALADO_HUMANO, RESUELTO
    officer_id: str = "OFICIAL_OPERACIONES_01"
    notes: str = "Actualización de estado operativa."

@router.get("/")
def list_cases(
    status: Optional[str] = None,
    department_id: Optional[int] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Case)
    
    if status:
        query = query.filter(Case.status == status)
    if department_id:
        query = query.filter(Case.department_id == department_id)
    if priority:
        query = query.filter(Case.priority == priority)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Case.radicado.ilike(search_filter),
                Case.citizen_name.ilike(search_filter),
                Case.neighborhood.ilike(search_filter),
                Case.title.ilike(search_filter)
            )
        )
        
    cases = query.order_by(Case.created_at.desc()).limit(limit).all()
    
    output = []
    now = datetime.utcnow()
    for c in cases:
        is_at_risk = False
        if c.sla_due_date and c.status != "RESUELTO":
            is_at_risk = (c.sla_due_date - now).total_seconds() <= (2 * 86400)
            
        output.append({
            "id": c.id,
            "radicado": c.radicado,
            "citizen_name": c.citizen_name,
            "citizen_phone": c.citizen_phone,
            "address": c.address,
            "neighborhood": c.neighborhood,
            "category": c.category,
            "title": c.title,
            "description": c.description,
            "status": c.status,
            "priority": c.priority,
            "confidence_score": round(c.confidence_score or 0.85, 2),
            "assigned_to": c.assigned_to,
            "requires_human_approval": c.requires_human_approval,
            "escalation_reason": c.escalation_reason,
            "sla_due_date": c.sla_due_date.strftime("%Y-%m-%d") if c.sla_due_date else None,
            "is_at_risk": is_at_risk,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M")
        })
        
    return {"total": len(output), "cases": output}

@router.get("/{identifier}")
def get_case_detail(identifier: str, db: Session = Depends(get_db)):
    case = None
    if identifier.isdigit():
        case = db.query(Case).filter(Case.id == int(identifier)).first()
    if not case:
        case = db.query(Case).filter(Case.radicado == identifier.upper()).first()
        
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")
        
    events = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).order_by(CaseEvent.created_at.asc()).all()
    classification = db.query(Classification).filter(Classification.case_id == case.id).first()
    dept = db.query(Department).filter(Department.id == case.department_id).first()
    
    return {
        "id": case.id,
        "radicado": case.radicado,
        "citizen_name": case.citizen_name,
        "citizen_id": case.citizen_id,
        "citizen_email": case.citizen_email,
        "citizen_phone": case.citizen_phone,
        "address": case.address,
        "neighborhood": case.neighborhood,
        "category": case.category,
        "title": case.title,
        "description": case.description,
        "status": case.status,
        "priority": case.priority,
        "confidence_score": case.confidence_score,
        "assigned_to": case.assigned_to,
        "department": {
            "name": dept.name if dept else case.assigned_to,
            "code": dept.code if dept else "DEP_GENERAL",
            "contact_email": dept.contact_email if dept else "atencion@barranquilla.gov.co"
        },
        "requires_human_approval": case.requires_human_approval,
        "escalation_reason": case.escalation_reason,
        "sla_due_date": case.sla_due_date.strftime("%Y-%m-%d") if case.sla_due_date else None,
        "created_at": case.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "classification_suggestion": {
            "predicted_category": classification.predicted_category if classification else case.category,
            "predicted_department": classification.predicted_department_code if classification else "DEP_GENERAL",
            "confidence": classification.confidence if classification else case.confidence_score,
            "justification": classification.justification if classification else "Clasificación asistida por IA",
            "approved_by_human": classification.approved_by_human if classification else False,
            "human_officer_id": classification.human_officer_id if classification else None
        },
        "events": [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "actor": ev.actor,
                "actor_role": ev.actor_role,
                "description": ev.description,
                "timestamp": ev.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for ev in events
        ]
    }

@router.post("/{case_id}/approve_classification")
def approve_classification(case_id: int, req: ApproveClassificationRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")
        
    classification = db.query(Classification).filter(Classification.case_id == case.id).first()
    if not classification:
        classification = Classification(
            case_id=case.id,
            predicted_category=case.category,
            predicted_department_code="DEP_GENERAL",
            confidence=case.confidence_score or 0.85
        )
        db.add(classification)

    classification.approved_by_human = True
    classification.human_officer_id = req.officer_id
    
    if req.override_department_code:
        override_dept = db.query(Department).filter(Department.code == req.override_department_code).first()
        if override_dept:
            classification.human_override_department_code = req.override_department_code
            case.department_id = override_dept.id
            case.assigned_to = override_dept.name
            case.category = override_dept.name
            
    if case.status in ["PENDIENTE_REVISION", "ESCALADO_HUMANO", "RADICADO_SIMULADO"]:
        case.status = "EN_GESTION"
        case.requires_human_approval = False
        
    event = CaseEvent(
        case_id=case.id,
        event_type="APROBACION_HUMANA",
        actor=req.officer_id,
        actor_role="FUNCIONARIO_PUBLICO",
        description=f"Clasificación y direccionamiento avalados por el funcionario {req.officer_id}. {req.notes}",
        details_json=json.dumps({"override": req.override_department_code, "notas": req.notes})
    )
    db.add(event)
    db.commit()

    return {
        "status": "SUCCESS",
        "message": f"Clasificación del caso {case.radicado} aprobada por {req.officer_id}.",
        "new_case_status": case.status,
        "assigned_to": case.assigned_to
    }

@router.post("/{case_id}/status")
def update_case_status(case_id: int, req: UpdateStatusRequest, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")
        
    old_status = case.status
    case.status = req.new_status
    if req.new_status == "RESUELTO":
        case.requires_human_approval = False

    event = CaseEvent(
        case_id=case.id,
        event_type="CAMBIO_ESTADO",
        actor=req.officer_id,
        actor_role="FUNCIONARIO_PUBLICO",
        description=f"Estado modificado de '{old_status}' a '{req.new_status}'. Notas: {req.notes}",
        details_json=json.dumps({"anterior": old_status, "nuevo": req.new_status})
    )
    db.add(event)
    db.commit()

    return {
        "status": "SUCCESS",
        "radicado": case.radicado,
        "old_status": old_status,
        "new_status": case.status
    }
