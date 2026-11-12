from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.core.database import Department, Procedure

KEYWORDS_MAPPING = {
    "DEP_ALUMBRADO": {
        "keywords": ["alumbrado", "luminaria", "bombilla", "foco", "poste", "luz de la calle", "k-yena", "kyena", "a oscuras", "lampara de la calle", "cables de la luz"],
        "category": "Alumbrado Público",
        "urgency_keywords": {"poste en el suelo": "ALTA", "cables echando chispas": "ALTA", "riesgo de caida": "ALTA", "sector a oscuras": "ALTA"},
        "default_priority": "MEDIA"
    },
    "DEP_ESPACIO_PUBLICO": {
        "keywords": ["espacio publico", "anden", "andén", "ocupacion", "ocupación", "escombros", "vendedor informal", "taller mecanico", "taller en la calle", "reja en la acera", "cerramiento", "bloqueando el paso", "invasión"],
        "category": "Espacio Público",
        "urgency_keywords": {"bloqueo total": "ALTA", "obstruccion ambulancia": "ALTA", "amenaza": "ALTA"},
        "default_priority": "MEDIA"
    },
    "DEP_HACIENDA": {
        "keywords": ["predial", "impuesto", "hacienda", "factura predial", "pago pse", "descuento pronto pago", "ica", "acuerdo de pago", "paz y salvo", "tributario", "avaluo", "catastro"],
        "category": "Hacienda Distrital",
        "urgency_keywords": {"embargo": "ALTA", "cobro coactivo": "ALTA", "vence hoy": "ALTA"},
        "default_priority": "MEDIA"
    },
    "DEP_GESTION_SOCIAL": {
        "keywords": ["sisben", "sisbén", "encuesta", "puntaje sisben", "grupo a", "grupo b", "grupo c", "subsidio", "renta ciudadana", "adulto mayor", "colombia mayor", "gestion social"],
        "category": "Gestión Social",
        "urgency_keywords": {"desalojo": "ALTA", "madre cabeza de familia": "MEDIA"},
        "default_priority": "BAJA"
    },
    "DEP_SALUD": {
        "keywords": ["dengue", "mosquito", "aedes", "criadero", "lote enmontado", "aguas estancadas", "alberca", "salud", "fumigacion", "fumigación", "hospital", "clinica", "eps", "ips", "inspeccion sanitaria"],
        "urgency_keywords": {"dengue grave": "ALTA", "hemorragico": "ALTA", "brote": "ALTA", "menor hospitalizado": "ALTA"},
        "default_priority": "MEDIA"
    }
}

def tool_classify_request(text: str, db: Session) -> Dict[str, Any]:
    """Herramienta classify_request: Identifica categoría, dependencia responsable, urgencia y justificación."""
    text_lower = text.lower()
    
    scores = {}
    priorities = {}
    
    for dept_code, info in KEYWORDS_MAPPING.items():
        score = 0
        for kw in info["keywords"]:
            if kw in text_lower:
                score += 1
                
        priority = info["default_priority"]
        for uk, prio_val in info["urgency_keywords"].items():
            if uk in text_lower:
                priority = prio_val
                score += 2
                
        scores[dept_code] = score
        priorities[dept_code] = priority
        
    best_dept_code = max(scores, key=scores.get)
    max_score = scores[best_dept_code]
    
    if max_score == 0:
        # Default a Secretaría General
        best_dept_code = "DEP_SECRETARIA_GENERAL"
        category = "Peticiones y Atención General"
        priority = "MEDIA"
        confidence = 0.55
        justification = "La solicitud no se ajusta a un trámite especializado unívoco; direccionada a la Ventanilla Única PQRSD según Decreto 0412."
    else:
        dept_info = KEYWORDS_MAPPING[best_dept_code]
        category = dept_info["category"]
        priority = priorities[best_dept_code]
        confidence = min(0.70 + (max_score * 0.08), 0.98)
        justification = f"Identificadas coincidencias temáticas con la competencia institucional de {category}."

    department = db.query(Department).filter(Department.code == best_dept_code).first()
    procedure = None
    if department:
        procedure = db.query(Procedure).filter(Procedure.department_id == department.id).first()

    return {
        "status": "SUCCESS",
        "predicted_category": category,
        "department_code": best_dept_code,
        "department_name": department.name if department else "Secretaría General",
        "department_id": department.id if department else None,
        "procedure_code": procedure.code if procedure else None,
        "procedure_id": procedure.id if procedure else None,
        "procedure_name": procedure.name if procedure else "Trámite General PQRSD",
        "sla_days": procedure.sla_days if procedure else 15,
        "priority": priority,
        "confidence_score": round(confidence, 2),
        "justification": justification
    }
