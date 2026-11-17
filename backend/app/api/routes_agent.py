from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.core.database import get_db, AccessAudit
from backend.app.agent.graph import citizen_agent_graph
from backend.app.agent.task_policy import build_task_policy

router = APIRouter(prefix="/agent", tags=["Agente"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "session-web-default"
    history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    response: str
    status: str
    intent: str
    case_result: Optional[Dict[str, Any]] = None
    classification: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    citations: List[Dict[str, Any]] = []
    thoughts: List[Dict[str, Any]] = []
    requires_human_approval: bool = False
    task_policy: Optional[Dict[str, Any]] = None

@router.get("/task_policy")
async def get_task_policy():
    return build_task_policy()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    # Registrar auditoría de gobernanza
    audit = AccessAudit(
        user_or_session=req.session_id,
        action="AGENT_INVOKE",
        resource="/api/agent/chat",
        status="AUTHORIZED"
    )
    db.add(audit)
    db.commit()

    initial_state = {
        "citizen_input": req.message,
        "session_id": req.session_id,
        "messages": req.history or [],
        "extracted_entities": {},
        "intent": "",
        "plan": [],
        "task_policy": {},
        "current_step": 0,
        "search_results": [],
        "classification": {},
        "validation": {},
        "requires_human_approval": False,
        "escalation_reason": None,
        "case_result": None,
        "final_response": "",
        "citations": [],
        "agent_thoughts": [],
        "status": "PROCESSING"
    }

    try:
        final_state = citizen_agent_graph.invoke(initial_state)
        
        return ChatResponse(
            response=final_state.get("final_response", "Procesado sin respuesta de texto."),
            status=final_state.get("status", "SUCCESS"),
            intent=final_state.get("intent", "CONSULTA"),
            case_result=final_state.get("case_result"),
            classification=final_state.get("classification"),
            validation=final_state.get("validation"),
            citations=final_state.get("citations", []),
            thoughts=final_state.get("agent_thoughts", []),
            requires_human_approval=final_state.get("requires_human_approval", False),
            task_policy=final_state.get("task_policy")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la ejecución del grafo multiagente: {str(e)}")

@router.get("/suggested_prompts")
async def get_suggested_prompts():
    return {
        "suggestions": [
            {
                "title": "💡 Reportar Luminaria Apagada",
                "prompt": "Quiero reportar que la luminaria frente a la Carrera 53 # 79-112 en el barrio Alto Prado está apagada. Mi celular es 3004567890.",
                "category": "Alumbrado Público"
            },
            {
                "title": "💰 Descuentos Impuesto Predial 2026",
                "prompt": "¿Cuáles son las fechas y porcentajes de descuento por pronto pago del Impuesto Predial Unificado 2026 en Barranquilla?",
                "category": "Hacienda Distrital"
            },
            {
                "title": "🔍 Consultar Estado de Caso",
                "prompt": "Deseo consultar el estado de mi caso con radicado BQL-2026-00101.",
                "category": "Seguimiento"
            },
            {
                "title": "📋 Requisitos Sisbén IV",
                "prompt": "¿Qué documentos y requisitos necesito para solicitar una nueva encuesta del Sisbén IV en Barranquilla?",
                "category": "Gestión Social"
            },
            {
                "title": "⚠️ Denuncia Ocupación de Andén",
                "prompt": "Denuncio que un taller colocó escombros y carros viejos sobre el andén peatonal en la Calle 45 # 21B-40 en San José impidiendo el paso.",
                "category": "Espacio Público"
            }
        ]
    }
