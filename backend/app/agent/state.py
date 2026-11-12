from typing import TypedDict, List, Dict, Any, Optional

class AgentThought(TypedDict):
    step_name: str
    action: str
    detail: str
    status: str # RUNNING, COMPLETED, WARNING, ERROR
    timestamp: str

class AgentState(TypedDict):
    citizen_input: str
    session_id: str
    messages: List[Dict[str, str]]
    extracted_entities: Dict[str, Any]
    intent: str # CONSULTA, RADICACION, CONSULTA_ESTADO, ANALITICA, ESCALAMIENTO
    plan: List[str]
    current_step: int
    search_results: List[Dict[str, Any]]
    classification: Dict[str, Any]
    validation: Dict[str, Any]
    requires_human_approval: bool
    escalation_reason: Optional[str]
    case_result: Optional[Dict[str, Any]]
    final_response: str
    citations: List[Dict[str, Any]]
    agent_thoughts: List[AgentThought]
    status: str # SUCCESS, PENDING_INFO, ESCALATED, ERROR
