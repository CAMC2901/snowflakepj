import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.core.database import Case, CaseEvent, Approval

SENSITIVE_TRIGGERS = [
    "corrupcion", "corrupción", "soborno", "cohecho", "coima", "tramitador",
    "pidiendo plata", "pidiendo dinero", "cobrando plata", "cobrando dinero",
    "demanda", "tutela", "abogado", "coactivo", "embargo", "disputa bancaria",
    "amenaza", "hablar con humano", "persona real", "funcionario humano", "supervisor"
]

def check_sensitive_triggers(text: str) -> Optional[str]:
    text_lower = text.lower()
    for trigger in SENSITIVE_TRIGGERS:
        if trigger in text_lower:
            return f"Activación de salvaguarda de gobernanza por término sensible detectado: '{trigger}'"
    return None

def tool_escalate_to_human(
    case_id: int,
    reason: str,
    evidence: str,
    db: Session,
    actor: str = "Agente_LangGraph"
) -> Dict[str, Any]:
    """Herramienta escalate_to_human: Envía una solicitud o caso a revisión humana obligatoria."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return {
            "status": "ERROR",
            "message": f"Caso ID {case_id} no encontrado para escalamiento."
        }
        
    case.status = "ESCALADO_HUMANO"
    case.requires_human_approval = True
    case.escalation_reason = reason
    case.updated_at = datetime.utcnow()
    
    # Registrar evento de auditoría
    event = CaseEvent(
        case_id=case.id,
        event_type="ESCALAMIENTO_HUMANO",
        actor=actor,
        actor_role="SUPERVISOR_IA",
        description=f"Caso remitido a bandeja de funcionario humano. Motivo: {reason}",
        details_json=json.dumps({"motivo": reason, "evidencia": evidence[:300]})
    )
    db.add(event)
    
    # Crear registro en la tabla de aprobaciones
    approval = Approval(
        case_id=case.id,
        requested_action="VALIDACION_Y_DECISION_HUMANA",
        justification=reason,
        status="PENDIENTE"
    )
    db.add(approval)
    db.commit()

    return {
        "status": "SUCCESS",
        "case_id": case.id,
        "radicado": case.radicado,
        "current_status": "ESCALADO_HUMANO",
        "reason": reason,
        "message": f"El caso {case.radicado} ha sido puesto en cola de supervisión humana para validación por un funcionario competente."
    }
