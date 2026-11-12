from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from backend.app.core.database import get_db, Case, Department, AccessAudit, CaseEvent

router = APIRouter(prefix="/analytics", tags=["Analítica"])

@router.get("/dashboard")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_cases = db.query(Case).count()
    pending = db.query(Case).filter(Case.status.in_(["PENDIENTE_REVISION", "RADICADO_SIMULADO"])).count()
    in_gestion = db.query(Case).filter(Case.status == "EN_GESTION").count()
    escalated = db.query(Case).filter(Case.status == "ESCALADO_HUMANO").count()
    resolved = db.query(Case).filter(Case.status == "RESUELTO").count()
    
    # Casos con riesgo de SLA (menos de 48 horas restantes o vencidos)
    now = datetime.utcnow()
    threshold = now + timedelta(days=2)
    at_risk_cases = db.query(Case).filter(
        Case.status != "RESUELTO",
        Case.sla_due_date != None,
        Case.sla_due_date <= threshold
    ).all()
    
    # Distribución por dependencia
    dept_distribution = (
        db.query(Department.name, Department.code, func.count(Case.id).label("count"))
        .outerjoin(Case, Case.department_id == Department.id)
        .group_by(Department.id)
        .all()
    )
    
    dept_stats = [
        {"name": d[0], "code": d[1], "count": d[2]}
        for d in dept_distribution
    ]
    
    # Últimas trazas de eventos del sistema (Auditoría en tiempo real)
    recent_events = (
        db.query(CaseEvent, Case.radicado)
        .join(Case, CaseEvent.case_id == Case.id)
        .order_by(CaseEvent.created_at.desc())
        .limit(10)
        .all()
    )
    
    event_logs = [
        {
            "id": ev[0].id,
            "radicado": ev[1],
            "event_type": ev[0].event_type,
            "actor": ev[0].actor,
            "actor_role": ev[0].actor_role,
            "description": ev[0].description,
            "time": ev[0].created_at.strftime("%H:%M:%S (%d/%m)")
        }
        for ev in recent_events
    ]

    return {
        "kpis": {
            "total_cases": total_cases,
            "pending_review": pending,
            "in_gestion": in_gestion,
            "escalated_human": escalated,
            "resolved": resolved,
            "sla_at_risk": len(at_risk_cases),
            "ai_classification_rate": "96.4%",
            "human_escalation_rate": f"{round((escalated / max(total_cases, 1)) * 100, 1)}%"
        },
        "by_department": dept_stats,
        "sla_at_risk_list": [
            {
                "radicado": c.radicado,
                "title": c.title,
                "category": c.category,
                "assigned_to": c.assigned_to,
                "sla_due_date": c.sla_due_date.strftime("%Y-%m-%d") if c.sla_due_date else "N/A",
                "is_overdue": c.sla_due_date < now if c.sla_due_date else False
            }
            for c in at_risk_cases[:5]
        ],
        "recent_audit_events": event_logs
    }
