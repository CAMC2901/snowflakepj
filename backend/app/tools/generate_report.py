from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.core.database import Case, Department

def tool_generate_report(report_type: str, db: Session, target_id: Any = None) -> Dict[str, Any]:
    """Herramienta generate_report: Genera resúmenes e informes ejecutivos de casos y solicitudes."""
    if report_type == "citizen_case_summary":
        case = db.query(Case).filter((Case.radicado == str(target_id)) | (Case.id == target_id)).first()
        if not case:
            return {"status": "ERROR", "message": "Caso no encontrado para informe."}
            
        summary = (
            f"INFORME OFICIAL DE CASO - ALCALDÍA DE BARRANQUILLA\n"
            f"Radicado: {case.radicado}\n"
            f"Categoría: {case.category}\n"
            f"Dependencia Asignada: {case.assigned_to}\n"
            f"Estado Actual: {case.status}\n"
            f"Prioridad: {case.priority}\n"
            f"Fecha de Vencimiento SLA: {case.sla_due_date.strftime('%Y-%m-%d') if case.sla_due_date else 'Pendiente'}\n"
            f"Requiere Intervención Humana: {'SÍ' if case.requires_human_approval else 'NO'}\n"
            f"Descripción: {case.description}\n"
        )
        return {
            "status": "SUCCESS",
            "report_type": report_type,
            "summary_text": summary,
            "case_data": {
                "radicado": case.radicado,
                "status": case.status,
                "category": case.category,
                "assigned_to": case.assigned_to
            }
        }
    else:
        # Informe global del sistema
        total = db.query(Case).count()
        escalated = db.query(Case).filter(Case.status == "ESCALADO_HUMANO").count()
        summary = (
            f"INFORME EJECUTIVO DE GESTIÓN CIUDADANA - ALCALDÍA DE BARRANQUILLA\n"
            f"Total de solicitudes registradas en la plataforma: {total}\n"
            f"Casos en revisión o escalamiento humano: {escalated}\n"
            f"Tasa de intervención humana requerida: {round((escalated / max(total, 1)) * 100, 1)}%\n"
            f"Entorno operativo: SANDBOX DE EVALUACIÓN (Presupuesto $0 - Ollama Local)\n"
        )
        return {
            "status": "SUCCESS",
            "report_type": report_type,
            "summary_text": summary,
            "metrics": {"total": total, "escalated": escalated}
        }
