from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.core.database import Requirement, Procedure

def tool_validate_required_fields(
    procedure_id: int,
    extracted_data: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Herramienta validate_required_fields: Comprueba campos y documentos obligatorios según catálogo oficial."""
    requirements = db.query(Requirement).filter(
        Requirement.procedure_id == procedure_id,
        Requirement.is_mandatory == True
    ).all()
    
    missing_fields = []
    validated_fields = {}
    
    for req in requirements:
        val = extracted_data.get(req.field_name)
        if not val or str(val).strip() == "" or str(val).lower() == "desconocido" or str(val).lower() == "null":
            missing_fields.append({
                "field_name": req.field_name,
                "label": req.label,
                "help_text": req.help_text,
                "field_type": req.field_type
            })
        else:
            validated_fields[req.field_name] = str(val).strip()
            
    is_valid = len(missing_fields) == 0
    
    if not is_valid:
        fields_names = [f["label"] for f in missing_fields]
        msg = f"Para formalizar el registro del caso, se requiere completar los siguientes datos obligatorios: {', '.join(fields_names)}."
    else:
        msg = "Todos los campos obligatorios han sido verificados satisfactoriamente."

    return {
        "status": "SUCCESS",
        "is_valid": is_valid,
        "procedure_id": procedure_id,
        "missing_fields": missing_fields,
        "missing_count": len(missing_fields),
        "validated_fields": validated_fields,
        "message": msg
    }
