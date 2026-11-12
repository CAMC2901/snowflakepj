from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from backend.app.core.database import Case, Department

AUTHORIZED_TEMPLATES = [
    "case_distribution_by_department",
    "cases_by_status",
    "sla_risk_summary",
    "general_kpis"
]

def tool_query_analytics(
    template_name: str,
    db: Session,
    parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Herramienta query_analytics: Ejecuta consultas estructuradas sobre vistas analíticas predefinidas sin SQL arbitrario."""
    if template_name not in AUTHORIZED_TEMPLATES:
        return {
            "status": "ERROR",
            "message": f"Plantilla analítica no autorizada: '{template_name}'. Lista blanca permitida: {AUTHORIZED_TEMPLATES}"
        }
        
    try:
        if template_name == "general_kpis":
            total = db.query(Case).count()
            pending = db.query(Case).filter(Case.status.in_(["PENDIENTE_REVISION", "RADICADO_SIMULADO"])).count()
            in_progress = db.query(Case).filter(Case.status == "EN_GESTION").count()
            escalated = db.query(Case).filter(Case.status == "ESCALADO_HUMANO").count()
            resolved = db.query(Case).filter(Case.status == "RESUELTO").count()
            
            # SLA en riesgo
            now = datetime.utcnow()
            threshold = now + timedelta(days=2)
            at_risk = db.query(Case).filter(
                Case.status.notin_(["RESUELTO"]),
                Case.sla_due_date <= threshold
            ).count()
            
            return {
                "status": "SUCCESS",
                "template": template_name,
                "data": {
                    "total_cases": total,
                    "pending_cases": pending,
                    "in_progress_cases": in_progress,
                    "escalated_cases": escalated,
                    "resolved_cases": resolved,
                    "sla_at_risk_cases": at_risk
                }
            }

        elif template_name == "case_distribution_by_department":
            results = (
                db.query(Department.name, Department.code, func.count(Case.id).label("count"))
                .outerjoin(Case, Case.department_id == Department.id)
                .group_by(Department.id)
                .all()
            )
            data = [
                {"department_name": r[0], "department_code": r[1], "cases_count": r[2]}
                for r in results
            ]
            return {
                "status": "SUCCESS",
                "template": template_name,
                "data": data
            }

        elif template_name == "cases_by_status":
            results = (
                db.query(Case.status, func.count(Case.id).label("count"))
                .group_by(Case.status)
                .all()
            )
            data = [{"status": r[0], "count": r[1]} for r in results]
            return {
                "status": "SUCCESS",
                "template": template_name,
                "data": data
            }

        elif template_name == "sla_risk_summary":
            now = datetime.utcnow()
            threshold = now + timedelta(days=2)
            cases_risk = db.query(Case).filter(
                Case.status.notin_(["RESUELTO"]),
                Case.sla_due_date <= threshold
            ).all()
            
            data = [
                {
                    "radicado": c.radicado,
                    "category": c.category,
                    "assigned_to": c.assigned_to,
                    "sla_due_date": c.sla_due_date.strftime("%Y-%m-%d") if c.sla_due_date else "",
                    "is_overdue": c.sla_due_date < now if c.sla_due_date else False
                }
                for c in cases_risk
            ]
            return {
                "status": "SUCCESS",
                "template": template_name,
                "data": data
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "template": template_name,
            "error": str(e)
        }
