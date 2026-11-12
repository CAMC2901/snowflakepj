import re
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END

from backend.app.agent.state import AgentState, AgentThought
from backend.app.agent.llm_client import llm_client
from backend.app.tools.search_knowledge import tool_search_knowledge
from backend.app.tools.classify_request import tool_classify_request
from backend.app.tools.validate_required_fields import tool_validate_required_fields
from backend.app.tools.case_management import tool_create_case_draft, tool_get_case_status
from backend.app.tools.escalate_to_human import check_sensitive_triggers, tool_escalate_to_human
from backend.app.core.database import SessionLocal, Department, Procedure

OUT_OF_SCOPE_TRIGGERS = [
    "receta", "pizza", "hacer comida", "ensayo sobre", "codigo python", "programacion",
    "programar", "desarrollo web", "horoscopo", "chiste", "tarea escolar", "ejercicio matematico",
    "partido de futbol", "champions league", "pelicula", "cancion", "letra de", "viaje a europa",
    "consejo amoroso", "filosofia", "poema", "cuento", "reparar computador", "videojuego"
]

def clean_response_text(text: str) -> str:
    """Elimina símbolos markdown ruidosos (###, ####, ---, **, `) y asegura una estructura limpia y ordenada."""
    if not text:
        return ""
    
    # 1. Eliminar encabezados markdown (###, ####, ##, #)
    text = re.sub(r'^[ \t]*#{1,6}[ \t]*', '', text, flags=re.MULTILINE)
    
    # 2. Eliminar líneas divisorias (---, ___, ***)
    text = re.sub(r'^[ \t]*[-*_]{3,}[ \t]*$', '', text, flags=re.MULTILINE)
    
    # 3. Eliminar citas markdown (> )
    text = re.sub(r'^[ \t]*>[ \t]*', '', text, flags=re.MULTILINE)
    
    # 4. Estandarizar viñetas con punto elegante (•)
    text = re.sub(r'^[ \t]*[-*][ \t]+', '• ', text, flags=re.MULTILINE)
    
    # 5. Limpiar bloques de código y backticks
    text = text.replace('```', '')
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # 6. Limpiar asteriscos de markdown (**texto** -> texto y *texto* -> texto)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # 7. Deduplicar viñetas y líneas consecutivas (prevenir loops de generación de modelos locales)
    lines = text.split("\n")
    cleaned_lines = []
    seen_bullets = set()
    prev_line = None
    for line in lines:
        stripped = line.strip()
        if stripped and stripped == prev_line:
            continue
        if stripped.startswith("•"):
            if stripped in seen_bullets:
                continue
            seen_bullets.add(stripped)
        cleaned_lines.append(line)
        if stripped:
            prev_line = stripped
    text = "\n".join(cleaned_lines)

    # 8. Normalizar espaciado vertical (máximo 2 saltos de línea consecutivos)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def add_thought(state: AgentState, step_name: str, action: str, detail: str, status: str = "COMPLETED") -> None:
    now_str = datetime.utcnow().strftime("%H:%M:%S")
    state["agent_thoughts"].append({
        "step_name": step_name,
        "action": action,
        "detail": detail,
        "status": status,
        "timestamp": now_str
    })

# ==========================================
# NODOS DEL GRAFO LANGGRAPH
# ==========================================

def interpret_node(state: AgentState) -> AgentState:
    text = state["citizen_input"]
    text_lower = text.lower()
    add_thought(state, "Recepción", "Analizando solicitud del ciudadano", f"Identificando intención y datos suministrados")
    
    # 0. Filtro de Alcance Institucional (FAQ / Salvaguarda de Propósito)
    # Usar coincidencia por palabras completas para evitar falsos positivos (ej. "descuento" con "cuento")
    for trigger in OUT_OF_SCOPE_TRIGGERS:
        if re.search(r'\b' + re.escape(trigger) + r'\b', text_lower):
            state["intent"] = "FUERA_DE_ALCANCE"
            add_thought(state, "Alcance Institucional", "Consulta fuera de competencia distrital", "La solicitud no corresponde a servicios o trámites de la Alcaldía", status="WARNING")
            return state

    # 1. Detectar si es consulta de estado de radicado
    radicado_match = re.search(r'\b(BQL-\d{4}-\d+)\b', text, re.IGNORECASE)
    if radicado_match or any(kw in text_lower for kw in ["consultar estado", "mi caso", "numero de radicado", "radicado no", "estado de mi"]):
        rad_num = radicado_match.group(1).upper() if radicado_match else None
        state["intent"] = "CONSULTA_ESTADO"
        state["extracted_entities"]["radicado"] = rad_num
        add_thought(state, "Consulta de Trámite", "Número de radicado identificado", f"Radicado: {rad_num or 'Pendiente de número'}")
        return state

    # 2. Detectar si hay disparadores de escalamiento sensible (Gobernanza)
    escalation_reason = check_sensitive_triggers(text)
    if escalation_reason:
        state["requires_human_approval"] = True
        state["escalation_reason"] = escalation_reason
        add_thought(state, "Supervisión", "Salvaguarda institucional activada", "Caso con aspectos sensibles asignado a funcionario humano", status="WARNING")

    # 3. Extracción de entidades relevantes (Direcciones, Barrios, Celulares, Cédulas)
    entities = state["extracted_entities"]
    
    # Dirección (Calle, Cra, Carrera, Cll, Transversal, Diagonal...)
    addr_match = re.search(r'\b(calle|cra|carrera|cll|diagonal|transversal|av|avenida|vía 40)\s+[\d\w\s#-]+(?=,|\.|\s+barrio|\s+en\s+el|$)', text, re.IGNORECASE)
    if addr_match:
        entities["address"] = addr_match.group(0).strip()
        
    # Barrio en Barranquilla
    barrios_comunes = [
        "alto prado", "el prado", "boston", "riomar", "san jose", "san josé", "rebolo",
        "simon bolivar", "simón bolívar", "ciudad jardin", "ciudad jardín", "las nieves",
        "chiquinquira", "chiquinquirá", "la victoria", "el recreo", "bellavista", "los alpes",
        "villa santos", "los andes", "las cayenas", "buenavista", "el silenciio", "la unión", "baranquilla"
    ]
    for b in barrios_comunes:
        if b in text_lower:
            entities["neighborhood"] = b.title()
            break

    # Teléfono (10 dígitos empezando en 3)
    phone_match = re.search(r'\b(3\d{9})\b', text)
    if phone_match:
        entities["citizen_phone"] = phone_match.group(1)

    # Cédula o Documento
    id_match = re.search(r'\b(c[eé]dula|cc|doc(?:umento)?)\s*(?:no\.?|:)?\s*(\d{7,10})\b', text, re.IGNORECASE)
    if id_match:
        entities["citizen_id"] = id_match.group(2)
    else:
        num_match = re.search(r'\b(\d{7,10})\b', text)
        if num_match and not entities.get("citizen_phone"):
            entities["citizen_id"] = num_match.group(1)

    # Poste o luminaria
    pole_match = re.search(r'\b(poste|placa|luminaria)\s*(?:no\.?|#|c[oó]digo)?\s*([a-zA-Z0-9-]+)\b', text, re.IGNORECASE)
    if pole_match:
        entities["pole_number"] = pole_match.group(2)

    # 4. Determinar si es reporte/radicación formal o consulta informativa / FAQ
    # Detectar si es una pregunta orientativa o consulta de información
    question_marks = ('¿' in text or '?' in text)
    info_question_words = [
        "qué", "que", "cómo", "como", "cuáles", "cuales", "cuándo", "cuando",
        "dónde", "donde", "por qué", "por que", "quién", "quien", "cuánto", "cuanto",
        "requisitos", "requisito", "documentos", "documento", "fechas", "plazos",
        "descuento", "descuentos", "horario", "horarios", "canales", "pasos",
        "procedimiento", "paz y salvo", "información", "informacion", "guía", "guia",
        "preguntas frecuentes", "faq", "cómo hago", "como hago", "cómo puedo", "como puedo",
        "qué hacer", "que hacer", "qué se necesita", "que se necesita", "para qué sirve", "para que sirve"
    ]
    is_info_question = question_marks or any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in info_question_words)

    # Disparadores explícitos de radicación de caso o reporte en terreno
    explicit_filing_triggers = [
        "quiero reportar", "vengo a reportar", "reporto que", "denuncio que", "deseo radicar",
        "solicito radicar", "radicar queja", "radicar denuncia", "radicar reclamo",
        "solicito visita", "solicito que vengan", "solicito inspección", "por favor vengan",
        "vengan a arreglar", "arreglen", "reparar de inmediato", "se dañó", "se cayo",
        "se cayó un poste", "poste caído", "poste a punto", "fuga de agua", "se fue la luz"
    ]
    is_explicit_filing = any(trig in text_lower for trig in explicit_filing_triggers)

    # Palabras de incidencia en terreno
    incident_words = [
        "dañado", "daño", "apagada", "falla", "avería", "averia", "escombros", "invasión", "invasion"
    ]
    has_incident_word = any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in incident_words)

    if is_explicit_filing:
        state["intent"] = "RADICACION"
    elif is_info_question:
        state["intent"] = "CONSULTA"
    elif has_incident_word and (entities.get("address") or entities.get("citizen_phone")):
        # Reporte de incidencia con dirección o teléfono suministrado
        state["intent"] = "RADICACION"
    elif any(k in text_lower for k in ["reportar", "denunciar", "radicar"]):
        state["intent"] = "RADICACION"
    else:
        state["intent"] = "CONSULTA"

    add_thought(state, "Recepción", "Datos preliminares estructurados", f"Intención: {state['intent']}")
    return state

def plan_node(state: AgentState) -> AgentState:
    intent = state.get("intent", "CONSULTA")
    add_thought(state, "Plan de Atención", "Estableciendo pasos de atención oficial", f"Organizando flujo para {intent}")
    
    if intent == "FUERA_DE_ALCANCE":
        state["plan"] = ["1. Informar marco de competencia de la Alcaldía de Barranquilla"]
    elif intent == "CONSULTA_ESTADO":
        state["plan"] = [
            "1. Validar radicado distrital",
            "2. Consultar sistema de operaciones",
            "3. Verificar cumplimiento de términos legales (SLA)",
            "4. Informar estado y próximos pasos al ciudadano"
        ]
    elif intent == "RADICACION":
        state["plan"] = [
            "1. Consultar normativa y procedimientos aplicables",
            "2. Clasificar solicitud y asignar dependencia distrital",
            "3. Validar requisitos obligatorios",
            "4. Verificar salvaguardas de gobernanza",
            "5. Generar radicado oficial y comprobante ciudadano",
            "6. Entregar constancia con tiempos de respuesta"
        ]
    else:
        state["plan"] = [
            "1. Buscar fundamentación oficial en la base institucional",
            "2. Confirmar vigencia 2026",
            "3. Redactar orientación ciudadana con citas oficiales"
        ]
        
    return state

def rag_node(state: AgentState) -> AgentState:
    if state["intent"] == "FUERA_DE_ALCANCE":
        return state

    db = SessionLocal()
    try:
        query = state["citizen_input"]
        add_thought(state, "Consulta Normativa", "Verificando base documental distrital", "Consultando reglamentos y guías oficiales vigentes")
        
        rag_res = tool_search_knowledge(query, db, top_k=3)
        citations = rag_res.get("citations", [])
        state["search_results"] = citations
        state["citations"] = citations
        
        if citations:
            best = citations[0]
            add_thought(state, "Evidencia Verificada", f"Documento: {best['title']}", f"Fuente oficial: {best['authority']}")
    finally:
        db.close()
    return state

def classify_node(state: AgentState) -> AgentState:
    if state["intent"] == "FUERA_DE_ALCANCE":
        return state

    db = SessionLocal()
    try:
        text = state["citizen_input"]
        add_thought(state, "Clasificación", "Asignando dependencia distrital responsable", "Evaluando competencias institucionales")
        
        classification = tool_classify_request(text, db)
        state["classification"] = classification
        
        add_thought(
            state,
            "Direccionamiento",
            f"Dependencia: {classification['department_name']}",
            f"Plazo reglamentario de atención: {classification['sla_days']} días hábiles"
        )
    finally:
        db.close()
    return state

def validate_node(state: AgentState) -> AgentState:
    if state["intent"] in ["FUERA_DE_ALCANCE", "CONSULTA", "CONSULTA_ESTADO"]:
        return state

    db = SessionLocal()
    try:
        proc_id = state.get("classification", {}).get("procedure_id")
        if not proc_id:
            proc = db.query(Procedure).first()
            proc_id = proc.id if proc else 1

        add_thought(state, "Validación", "Verificando datos obligatorios", "Comprobando requisitos mínimos del trámite")
        
        val_res = tool_validate_required_fields(proc_id, state["extracted_entities"], db)
        state["validation"] = val_res
        
        if val_res["is_valid"]:
            add_thought(state, "Requisitos", "Validación completa", "Todos los datos requeridos fueron suministrados")
        else:
            missing_names = [f["label"] for f in val_res["missing_fields"]]
            add_thought(state, "Requisitos", "Información complementaria requerida", f"Datos pendientes: {', '.join(missing_names)}", status="WARNING")
    finally:
        db.close()
    return state

def router_node(state: AgentState) -> str:
    intent = state.get("intent", "CONSULTA")
    if intent == "FUERA_DE_ALCANCE":
        return "out_of_scope_node"
    if intent == "CONSULTA_ESTADO":
        return "status_node"
    if state.get("requires_human_approval", False):
        return "escalate_node"
    if intent == "RADICACION":
        if not state.get("validation", {}).get("is_valid", False):
            return "ask_clarification_node"
        return "execute_case_node"
    return "synthesize_answer_node"

def out_of_scope_node(state: AgentState) -> AgentState:
    add_thought(state, "Respuesta", "Orientación sobre el alcance institucional", "Informando competencias de la Alcaldía de Barranquilla")
    raw_text = (
        "Estimado ciudadano, este canal virtual está habilitado exclusivamente para brindar orientación y gestionar "
        "trámites oficiales de la Alcaldía Distrital de Barranquilla.\n\n"
        "Trámites y servicios disponibles en esta ventanilla:\n"
        "• Alumbrado Público: Reportes de bombillas apagadas, postes con fallas y solicitudes del operador K-YENA.\n"
        "• Control Urbano y Espacio Público: Denuncias por invasión de andenes peatonales, talleres en vía y escombros.\n"
        "• Hacienda Distrital: Fechas de descuento de Impuesto Predial 2026, paz y salvo y liquidación.\n"
        "• Sisbén IV: Requisitos para nueva encuesta socioeconómica y actualización del grupo familiar.\n"
        "• Salud Pública: Reporte de criaderos de dengue y medidas de control sanitario.\n"
        "• PQRSD y Seguimiento: Radicación formal con comprobante digital y consulta de estado con número de radicado.\n\n"
        "No tenemos habilitación para responder preguntas sobre programación, recetas, entretenimiento, tareas escolares o asuntos ajenos a la administración distrital de Barranquilla.\n\n"
        "Si tienes alguna consulta sobre un trámite municipal, por favor escríbela a continuación."
    )
    state["final_response"] = clean_response_text(raw_text)
    state["status"] = "SUCCESS"
    return state

def status_node(state: AgentState) -> AgentState:
    db = SessionLocal()
    try:
        radicado = state["extracted_entities"].get("radicado")
        add_thought(state, "Consulta", "Buscando expediente en sistema", f"Radicado: {radicado or 'No especificado'}")
        
        if not radicado:
            state["final_response"] = (
                "Para consultar el estado de tu solicitud, por favor indícanos tu número de radicado distrital "
                "(por ejemplo: BQL-2026-00101)."
            )
            state["status"] = "PENDING_INFO"
            return state

        res = tool_get_case_status(radicado, db)
        state["case_result"] = res
        
        if res["status"] == "NOT_FOUND":
            state["final_response"] = (
                f"No encontramos un caso registrado con el radicado {radicado} en el sistema distrital. "
                "Verifica que el número coincida exactamente con el formato BQL-2026-XXXXX."
            )
            state["status"] = "ERROR"
        else:
            hist_lines = "\n".join([f"• {h['timestamp']} ({h['actor']}): {h['description']}" for h in res.get("history", [])])
            alerta_sla = "Atención prioritaria: trámite próximo al límite de tiempo legal." if res.get("is_at_risk") else "Trámite dentro del tiempo legal establecido."
            
            raw_text = (
                f"Estado Oficial de tu Solicitud: {res['radicado']}\n\n"
                f"• Asunto: {res['title']}\n"
                f"• Solicitante: {res['citizen_name']}\n"
                f"• Categoría: {res['category']}\n"
                f"• Dependencia Responsable: {res['assigned_to']}\n"
                f"• Estado Actual: {res['current_status']}\n"
                f"• Prioridad Asignada: {res['priority']}\n"
                f"• Plazo Límite Estimado: {res['sla_due_date']} ({alerta_sla})\n\n"
                f"Historial de Actuaciones:\n{hist_lines}\n\n"
                f"Información certificada por el Sistema de Atención Ciudadana de la Alcaldía de Barranquilla."
            )
            state["final_response"] = clean_response_text(raw_text)
            state["status"] = "SUCCESS"
            add_thought(state, "Consulta", "Estado recuperado", f"Expediente activo en {res['assigned_to']}")
    finally:
        db.close()
    return state

def ask_clarification_node(state: AgentState) -> AgentState:
    val = state.get("validation", {})
    missing = val.get("missing_fields", [])
    dept_name = state.get("classification", {}).get("department_name", "la Alcaldía Distrital de Barranquilla")
    category = state.get("classification", {}).get("predicted_category", "solicitud")
    
    add_thought(state, "Requisitos", "Solicitando datos complementarios", f"Faltan {len(missing)} campos para formalizar el trámite")
    
    missing_items = "\n".join([f"• {f['label']}: {f['help_text']}" for f in missing])
    
    raw_text = (
        f"Comprendo tu solicitud relacionada con {category}, la cual será atendida por {dept_name}.\n\n"
        f"Para formalizar tu radicación y asignarte de inmediato tu comprobante con número oficial de seguimiento, "
        f"necesitamos que nos suministres los siguientes datos indispensables:\n\n"
        f"{missing_items}\n\n"
        f"Por favor responde con estos datos en tu próximo mensaje para completar tu trámite."
    )
    state["final_response"] = clean_response_text(raw_text)
    state["status"] = "PENDING_INFO"
    return state

def execute_case_node(state: AgentState) -> AgentState:
    db = SessionLocal()
    try:
        entities = state["extracted_entities"]
        classification = state.get("classification", {})
        
        add_thought(state, "Radicación", "Formalizando trámite en sistema", "Generando número único de seguimiento")
        
        payload = {
            "citizen_name": entities.get("citizen_name", "Ciudadano Solicitante"),
            "citizen_id": entities.get("citizen_id", ""),
            "citizen_phone": entities.get("citizen_phone", ""),
            "citizen_email": entities.get("citizen_email", ""),
            "address": entities.get("address", "Barranquilla"),
            "neighborhood": entities.get("neighborhood", "Sector no especificado"),
            "category": classification.get("predicted_category", "General"),
            "title": f"Reporte de {classification.get('predicted_category', 'Gestión')} en {entities.get('neighborhood', 'Barranquilla')}",
            "description": state["citizen_input"],
            "department_id": classification.get("department_id"),
            "procedure_id": classification.get("procedure_id"),
            "department_code": classification.get("department_code"),
            "department_name": classification.get("department_name"),
            "sla_days": classification.get("sla_days", 15),
            "priority": classification.get("priority", "MEDIA"),
            "confidence_score": classification.get("confidence_score", 0.90),
            "requires_human_approval": False,
            "justification": classification.get("justification")
        }
        
        case_res = tool_create_case_draft(payload, db)
        
        # Generar comprobante estructurado
        security_token = hashlib.sha256(f"{case_res['radicado']}-{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12].upper()
        case_res["comprobante"] = {
            "radicado": case_res["radicado"],
            "codigo_verificacion": security_token,
            "fecha_radicacion": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "entidad": "Alcaldía Distrital de Barranquilla",
            "dependencia": case_res["department_name"],
            "plazo_dias_habiles": case_res["sla_days"],
            "fecha_limite_sla": case_res["sla_due_date"],
            "ciudadano": payload["citizen_name"],
            "ubicacion": f"{payload['address']} ({payload['neighborhood']})",
            "proximos_pasos": [
                f"Tu solicitud fue direccionada a {case_res['department_name']}.",
                f"Tiempo reglamentario de atención: {case_res['sla_days']} días hábiles.",
                "No requieres desplazarte a ventanillas físicas; puedes consultar el avance en este portal.",
                "Un funcionario o cuadrilla técnica se comunicará contigo si se requiere una inspección ocular."
            ]
        }
        state["case_result"] = case_res
        
        raw_text = (
            f"Solicitud Radicada Exitosamente\n\n"
            f"Tu requerimiento ha quedado formalmente registrado en el sistema de atención distrital:\n\n"
            f"• Número de Radicado: {case_res['radicado']}\n"
            f"• Código Digital de Verificación: {security_token}\n"
            f"• Categoría: {case_res['category']}\n"
            f"• Dependencia Responsable: {case_res['department_name']}\n"
            f"• Plazo Límite de Respuesta: {case_res['sla_due_date']} ({case_res['sla_days']} días hábiles)\n"
            f"• Estado Inicial: En Trámite\n\n"
            f"Próximos Pasos:\n"
            f"1. La dependencia asignada revisará tu caso y programará la actuación correspondiente.\n"
            f"2. Conserva tu número de radicado ({case_res['radicado']}) para hacer seguimiento en línea en cualquier momento.\n"
            f"3. No es necesario acudir a las ventanillas físicas de la Alcaldía."
        )
        state["final_response"] = clean_response_text(raw_text)
        state["status"] = "SUCCESS"
        add_thought(state, "Radicación", "Radicación completada", f"Número asignado: {case_res['radicado']}")
    finally:
        db.close()
    return state

def escalate_node(state: AgentState) -> AgentState:
    db = SessionLocal()
    try:
        entities = state["extracted_entities"]
        classification = state.get("classification", {})
        reason = state.get("escalation_reason", "Solicitud requiere intervención humana directa.")
        
        add_thought(state, "Revisión Especial", "Asignando caso a funcionario institucional", reason, status="WARNING")
        
        payload = {
            "citizen_name": entities.get("citizen_name", "Ciudadano Solicitante"),
            "citizen_id": entities.get("citizen_id", ""),
            "citizen_phone": entities.get("citizen_phone", ""),
            "address": entities.get("address", "Barranquilla"),
            "neighborhood": entities.get("neighborhood", ""),
            "category": classification.get("predicted_category", "Atención Especial"),
            "title": f"Caso en revisión: {reason[:60]}",
            "description": state["citizen_input"],
            "department_id": classification.get("department_id"),
            "procedure_id": classification.get("procedure_id"),
            "department_code": classification.get("department_code"),
            "department_name": classification.get("department_name"),
            "sla_days": 5,
            "priority": "ALTA",
            "confidence_score": 0.90,
            "requires_human_approval": True,
            "escalation_reason": reason,
            "justification": reason
        }
        
        case_res = tool_create_case_draft(payload, db)
        state["case_result"] = case_res
        
        raw_text = (
            f"Solicitud en Revisión Especial por Funcionario\n\n"
            f"Por la naturaleza administrativa de tu requerimiento, este caso ha sido asignado de manera prioritaria "
            f"a la bandeja de un funcionario especializado de {case_res['department_name']}.\n\n"
            f"• Número de Radicado de Seguimiento: {case_res['radicado']}\n"
            f"• Prioridad Asignada: Alta\n"
            f"• Plazo Máximo de Evaluación: 5 días hábiles\n\n"
            f"Un funcionario se comunicará contigo si se requiere documentación soporte adicional."
        )
        state["final_response"] = clean_response_text(raw_text)
        state["status"] = "ESCALATED"
        add_thought(state, "Revisión Especial", "Caso asignado a funcionario", f"Radicado {case_res['radicado']} en cola humana")
    finally:
        db.close()
    return state

def synthesize_answer_node(state: AgentState) -> AgentState:
    query = state["citizen_input"]
    citations = state.get("citations", [])
    classification = state.get("classification", {})
    
    add_thought(state, "Orientación", "Redactando orientación institucional con calidez y cercanía", "Incorporando fundamento normativo oficial")
    
    if citations:
        top = citations[0]
        query_l = query.lower()
        
        # Seleccionar el fragmento más relevante según el foco de la consulta
        if any(w in query_l for w in ["descuento", "descuentos", "porcentaje", "porcentajes", "pronto pago", "beneficio"]):
            for c in citations:
                if "descuento" in c.get("content", "").lower() or "10%" in c.get("content", ""):
                    top = c
                    break
        elif any(w in query_l for w in ["paz y salvo", "pazysalvo"]):
            for c in citations:
                if "paz y salvo" in c.get("content", "").lower():
                    top = c
                    break
        elif any(w in query_l for w in ["sisben", "sisbén", "encuesta"]):
            for c in citations:
                if "encuesta" in c.get("content", "").lower() or "sisbén" in c.get("content", "").lower():
                    top = c
                    break
        elif any(w in query_l for w in ["luminaria", "alumbrado", "k-yena", "kyena", "poste"]):
            for c in citations:
                if "luminaria" in c.get("content", "").lower() or "alumbrado" in c.get("content", "").lower():
                    top = c
                    break
        elif any(w in query_l for w in ["andén", "anden", "espacio público", "espacio publico", "escombros"]):
            for c in citations:
                if "andén" in c.get("content", "").lower() or "espacio público" in c.get("content", "").lower():
                    top = c
                    break

        # Construir contexto estructurado enriquecido
        context_parts = []
        for i, c in enumerate(citations[:3]):
            kf_str = json.dumps(c.get("key_facts", {}), ensure_ascii=False) if c.get("key_facts") else ""
            req_str = ", ".join(c.get("requirements", [])) if c.get("requirements") else ""
            steps_str = " | ".join(c.get("steps", [])) if c.get("steps") else ""
            channels_str = ", ".join(c.get("channels", [])) if c.get("channels") else ""
            
            part = f"Documento {i+1}: {c['title']} ({c.get('authority', 'Alcaldía de Barranquilla')})\n"
            if kf_str:
                part += f"Datos Clave Oficiales 2026: {kf_str}\n"
            if req_str:
                part += f"Requisitos: {req_str}\n"
            if steps_str:
                part += f"Pasos: {steps_str}\n"
            if channels_str:
                part += f"Canales de Atención: {channels_str}\n"
            part += f"Contenido Oficial: {c['content']}"
            context_parts.append(part)

        context_text = "\n\n".join(context_parts)

        system_prompt = (
            "Eres el Asistente Oficial de Atención Ciudadana de la Alcaldía Distrital de Barranquilla, Colombia.\n"
            "Tu labor es atender al ciudadano con calidez, gran amabilidad, respeto, cercanía y vocación de servicio.\n\n"
            "PAUTAS DE ATENCIÓN OBLIGATORIAS:\n"
            "1. Inicia con un saludo cercano y cordial (ejemplo: '¡Hola! Con gusto te oriento...', '¡Buenas tardes! Es un placer ayudarte...').\n"
            "2. Responde directamente la inquietud del ciudadano con base estricta en los datos del contexto oficial para el año 2026.\n"
            "3. Cita con absoluta exactitud las fechas, porcentajes y plazos indicados (ejemplo: 10% hasta el 31 de marzo de 2026, 5% hasta el 31 de mayo de 2026). NUNCA inventes fechas ni porcentajes distintos.\n"
            "4. Menciona con claridad los requisitos y pasos a seguir.\n"
            "5. Indica la dependencia distrital encargada y los canales oficiales (portal web www.barranquilla.gov.co, Línea 195, Ventanilla Única).\n"
            "6. Cierra con una despedida cálida ofreciendo tu disposición para cualquier otra consulta.\n\n"
            "REGLAS DE FORMATO:\n"
            "- NO uses encabezados con símbolos markdown como ### o ####.\n"
            "- NO uses líneas divisorias ni bloques de código.\n"
            "- NO encierres texto en asteriscos dobles (**). Usa texto limpio.\n"
            "- Usa viñetas con el punto '•' para listas ordenadas de pasos o requisitos."
        )

        user_prompt = f"Consulta del ciudadano: {query}\n\nContexto institucional oficial:\n{context_text}\n\nRespuesta institucional organizada:"
        
        llm_reply = llm_client.generate(prompt=user_prompt, system_prompt=system_prompt)
        
        # Validar si el LLM cubrió los hechos indispensables
        needs_facts_fallback = False
        if any(w in query_l for w in ["descuento", "descuentos", "porcentaje", "porcentajes"]):
            if not any(k in (llm_reply or "").lower() for k in ["10%", "5%", "diez por ciento", "marzo"]):
                needs_facts_fallback = True

        if llm_reply and len(llm_reply.strip()) > 30 and not needs_facts_fallback:
            final_text = clean_response_text(llm_reply)
        else:
            dept = classification.get('department_name', top.get('authority', 'Alcaldía de Barranquilla'))
            kf = top.get('key_facts', {})
            reqs = top.get('requirements', [])
            steps = top.get('steps', [])
            channels = top.get('channels', [])
            
            lines = [
                f"¡Hola! Con mucho gusto te comparto la información oficial de la Alcaldía Distrital de Barranquilla:",
                "",
                top['content'].strip(),
                ""
            ]
            if reqs:
                lines.append("Requisitos y Documentos:")
                for r in reqs:
                    lines.append(f"• {r}")
                lines.append("")
            if steps:
                lines.append("Pasos a Seguir:")
                for s in steps:
                    lines.append(f"• {s}")
                lines.append("")
            
            lines.append(f"Dependencia Competente: {dept}")
            if channels:
                lines.append(f"Canales de Atención: {', '.join(channels)}")
            else:
                lines.append(f"Canal Oficial de Consulta: {top.get('source_url', 'https://www.barranquilla.gov.co')}")
            
            lines.append("\nQuedo a tu entera disposición si necesitas realizar otro trámite o consulta.")
            final_text = clean_response_text("\n".join(lines))
            
        state["final_response"] = final_text
    else:
        state["final_response"] = clean_response_text(
            "¡Hola! Apreciado ciudadano, en este momento no encontramos un procedimiento específico para tu consulta "
            "en nuestra base documental distrital vigente.\n\n"
            "Te invitamos cordialmente a consultar la Ventanilla Única de Atención al Ciudadano de la Alcaldía de Barranquilla "
            "(Paseo Bolívar, Calle 34 # 43-31) o comunicarte con la línea telefónica gratuita distrital 195, donde con gusto te atenderemos."
        )

    state["status"] = "SUCCESS"
    return state

def verify_node(state: AgentState) -> AgentState:
    add_thought(state, "Cierre", "Trámite finalizado", "Atención registrada bajo estándares de servicio al ciudadano")
    state["final_response"] = clean_response_text(state["final_response"])
    if "Alcaldía Distrital de Barranquilla" not in state["final_response"]:
        state["final_response"] += "\n\nAlcaldía Distrital de Barranquilla — Distrito Especial, Industrial y Portuario."
    return state

# ==========================================
# CONSTRUCCIÓN DEL WORKFLOW LANGGRAPH
# ==========================================

def create_citizen_agent_graph():
    builder = StateGraph(AgentState)
    
    # Agregar nodos
    builder.add_node("interpret_node", interpret_node)
    builder.add_node("plan_node", plan_node)
    builder.add_node("rag_node", rag_node)
    builder.add_node("classify_node", classify_node)
    builder.add_node("validate_node", validate_node)
    builder.add_node("status_node", status_node)
    builder.add_node("ask_clarification_node", ask_clarification_node)
    builder.add_node("execute_case_node", execute_case_node)
    builder.add_node("escalate_node", escalate_node)
    builder.add_node("out_of_scope_node", out_of_scope_node)
    builder.add_node("synthesize_answer_node", synthesize_answer_node)
    builder.add_node("verify_node", verify_node)

    # Definir aristas y transiciones
    builder.add_edge(START, "interpret_node")
    builder.add_edge("interpret_node", "plan_node")
    builder.add_edge("plan_node", "rag_node")
    builder.add_edge("rag_node", "classify_node")
    builder.add_edge("classify_node", "validate_node")

    # Enrutamiento condicional
    builder.add_conditional_edges(
        "validate_node",
        router_node,
        {
            "out_of_scope_node": "out_of_scope_node",
            "status_node": "status_node",
            "escalate_node": "escalate_node",
            "ask_clarification_node": "ask_clarification_node",
            "execute_case_node": "execute_case_node",
            "synthesize_answer_node": "synthesize_answer_node"
        }
    )

    # Todos los caminos convergen en verify_node y luego END
    builder.add_edge("out_of_scope_node", "verify_node")
    builder.add_edge("status_node", "verify_node")
    builder.add_edge("ask_clarification_node", "verify_node")
    builder.add_edge("execute_case_node", "verify_node")
    builder.add_edge("escalate_node", "verify_node")
    builder.add_edge("synthesize_answer_node", "verify_node")
    builder.add_edge("verify_node", END)

    return builder.compile()

citizen_agent_graph = create_citizen_agent_graph()
