"""Política explícita de priorización; no reemplaza las salvaguardas del grafo."""

from copy import deepcopy


# Estimaciones iniciales de esfuerzo humano equivalente, no latencias medidas.
# Frecuencia: eventos que activan la tarea, no estadísticas de uso.
TASK_CATALOG = (
    {"id": "interpret", "name": "Interpretar la solicitud", "time_minutes": 2, "frequency": "Cada mensaje", "risk": 1, "value": 2, "reviewer": "Supervisor de atención ciudadana", "intents": ["CONSULTA", "RADICACION", "CONSULTA_ESTADO", "FUERA_DE_ALCANCE"]},
    {"id": "scope", "name": "Verificar competencia institucional", "time_minutes": 1, "frequency": "Cada mensaje", "risk": 1, "value": 3, "reviewer": "Supervisor de atención ciudadana", "intents": ["CONSULTA", "RADICACION", "CONSULTA_ESTADO", "FUERA_DE_ALCANCE"]},
    {"id": "knowledge", "name": "Recuperar normativa y fuentes", "time_minutes": 4, "frequency": "Consultas y radicaciones", "risk": 1, "value": 3, "reviewer": "Responsable de la biblioteca normativa", "intents": ["CONSULTA", "RADICACION"]},
    {"id": "classify", "name": "Clasificar y asignar dependencia", "time_minutes": 4, "frequency": "Solicitudes de orientación y radicación", "risk": 2, "value": 3, "reviewer": "Funcionario de la dependencia asignada", "intents": ["CONSULTA", "RADICACION"]},
    {"id": "validate", "name": "Validar requisitos obligatorios", "time_minutes": 3, "frequency": "Cada radicación", "risk": 1, "value": 3, "reviewer": "Funcionario de ventanilla única", "intents": ["RADICACION"]},
    {"id": "clarify", "name": "Solicitar datos faltantes", "time_minutes": 2, "frequency": "Radicaciones incompletas", "risk": 1, "value": 2, "reviewer": "Funcionario de ventanilla única", "intents": ["RADICACION"]},
    {"id": "register", "name": "Registrar solicitud y comprobante", "time_minutes": 8, "frequency": "Radicaciones completas", "risk": 2, "value": 3, "reviewer": "Funcionario de la dependencia asignada", "intents": ["RADICACION"]},
    {"id": "status", "name": "Consultar expediente y plazos", "time_minutes": 3, "frequency": "Consultas de radicado", "risk": 2, "value": 3, "reviewer": "Funcionario responsable del expediente", "intents": ["CONSULTA_ESTADO"]},
    {"id": "escalate", "name": "Detectar y escalar asuntos sensibles", "time_minutes": 10, "frequency": "Cada mensaje; derivación ante alertas", "risk": 3, "value": 3, "reviewer": "Funcionario especializado de la dependencia competente", "intents": ["CONSULTA", "RADICACION", "CONSULTA_ESTADO"]},
    {"id": "answer", "name": "Redactar y verificar la respuesta", "time_minutes": 5, "frequency": "Cada respuesta", "risk": 2, "value": 3, "reviewer": "Supervisor de atención ciudadana", "intents": ["CONSULTA", "RADICACION", "CONSULTA_ESTADO", "FUERA_DE_ALCANCE"]},
)


def build_task_policy(intent=None, requires_human_approval=False):
    """Ordena por valor descendente, riesgo y esfuerzo ascendentes; desempata por ID.

    Las tres elecciones son prioridades de supervisión/mejora, no una lista
    exclusiva de ejecución. Todas las etapas obligatorias siguen ejecutándose.
    """
    tasks = deepcopy(list(TASK_CATALOG))
    for task in tasks:
        high_effort = task["time_minutes"] > 5
        high_impact = task["value"] >= 2
        task["matrix_quadrant"] = (
            "PROYECTO_ESTRATEGICO" if high_effort and high_impact else
            "GANANCIA_RAPIDA" if high_impact else
            "RECONSIDERAR" if high_effort else "TAREA_MENOR"
        )
        task["applicable"] = intent is None or intent in task["intents"]
        task["review_status"] = "PENDING_REVIEW"
        task["human_decision_required"] = task["risk"] == 3

    eligible = [task for task in tasks if task["applicable"] and task["risk"] < 3]
    selected = sorted(eligible, key=lambda task: (
        -task["value"], task["risk"], task["time_minutes"], task["id"]
    ))[:3]
    selected_ids = [task["id"] for task in selected]
    for task in tasks:
        task["selected"] = task["id"] in selected_ids

    summary = "Prioridades de la IA: " + "; ".join(
        f"{task['name']} (valor {task['value']}, riesgo {task['risk']}); revisa: {task['reviewer']}"
        for task in selected
    ) + ". Las validaciones y salvaguardas se mantienen obligatorias."
    if requires_human_approval:
        summary += " Esta solicitud requiere intervención humana prioritaria, independientemente del ranking."
    return {
        "version": "1.0",
        "scale": {"risk": "1 bajo, 2 medio, 3 alto", "value": "1 bajo, 2 medio, 3 alto"},
        "estimates_notice": "Tiempos estimados de trabajo humano equivalente; frecuencias por evento, no mediciones reales.",
        "matrix_rules": {"high_effort": "Más de 5 minutos", "high_impact": "Valor mayor o igual a 2"},
        "selection_rule": "Valor descendente, riesgo ascendente, tiempo ascendente e ID; solo tareas aplicables con riesgo menor a 3.",
        "mandatory_steps_preserved": True,
        "requires_human_approval": requires_human_approval,
        "tasks": tasks,
        "selected_task_ids": selected_ids,
        "presentation": {"target_seconds": 120, "text": summary},
    }
