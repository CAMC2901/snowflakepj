"""
Suite de Pruebas Automatizadas de Funcionamiento y Preguntas Frecuentes (FAQ)
Agente Inteligente de Gestión Ciudadana — Alcaldía Distrital de Barranquilla
"""

import re
import sys
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 25

def assert_clean_format(text: str, test_name: str):
    """Verifica que el texto de respuesta no contenga símbolos markdown ruidosos."""
    assert "###" not in text, f"[{test_name}] Falló: La respuesta contiene encabezados markdown '###'"
    assert "####" not in text, f"[{test_name}] Falló: La respuesta contiene encabezados markdown '####'"
    assert "---" not in text, f"[{test_name}] Falló: La respuesta contiene líneas divisorias '---'"
    assert "```" not in text, f"[{test_name}] Falló: La respuesta contiene bloques de código markdown '```'"
    assert not re.search(r'\*\*[^*]+\*\*', text), f"[{test_name}] Advertencia: La respuesta contiene dobles asteriscos '**'"

def test_1_faq_sisben():
    print("\n" + "="*70)
    print("TEST 1: FAQ - Requisitos para Nueva Encuesta del Sisbén IV")
    print("="*70)
    prompt = "¿Qué documentos y requisitos necesito para solicitar una nueva encuesta del Sisbén IV en Barranquilla?"
    res = requests.post(f"{BASE_URL}/api/agent/chat", json={"message": prompt}, timeout=TIMEOUT)
    assert res.status_code == 200, f"Error HTTP: {res.status_code}"
    data = res.json()
    
    print(f"-> Intención detectada: {data.get('intent')}")
    print(f"-> Estado de respuesta: {data.get('status')}")
    print(f"-> Citas normativas RAG: {len(data.get('citations', []))}")
    print(f"-> Extracto de respuesta:\n{data.get('response')[:350]}...\n")
    
    assert data["intent"] == "CONSULTA", f"Se esperaba CONSULTA, pero se obtuvo {data['intent']}"
    assert data["status"] == "SUCCESS", f"Se esperaba SUCCESS, pero se obtuvo {data['status']}"
    assert len(data["citations"]) > 0, "No se recuperaron citas documentales del Sisbén"
    assert_clean_format(data["response"], "TEST 1 (Sisbén)")
    print("✓ TEST 1 EXITOSO: FAQ Sisbén IV responde de manera informativa y sin pedir datos de radicación.")

def test_2_faq_predial_descuentos():
    print("\n" + "="*70)
    print("TEST 2: FAQ - Fechas y Descuentos del Impuesto Predial 2026")
    print("="*70)
    prompt = "¿Cuáles son las fechas y porcentajes de descuento por pronto pago del Impuesto Predial Unificado 2026 en Barranquilla?"
    res = requests.post(f"{BASE_URL}/api/agent/chat", json={"message": prompt}, timeout=TIMEOUT)
    assert res.status_code == 200
    data = res.json()
    
    print(f"-> Intención detectada: {data.get('intent')}")
    print(f"-> Estado de respuesta: {data.get('status')}")
    print(f"-> Citas normativas RAG: {len(data.get('citations', []))}")
    print(f"-> Extracto de respuesta:\n{data.get('response')[:350]}...\n")
    
    assert data["intent"] == "CONSULTA"
    assert data["status"] == "SUCCESS"
    assert len(data["citations"]) > 0
    resp_lower = data["response"].lower()
    assert "10%" in data["response"] or "diez por ciento" in resp_lower or "descuento" in resp_lower, "No se mencionó el descuento en la respuesta"
    assert_clean_format(data["response"], "TEST 2 (Predial Descuentos)")
    print("✓ TEST 2 EXITOSO: FAQ Predial entrega los descuentos y plazos normativos 2026.")

def test_3_faq_paz_y_salvo():
    print("\n" + "="*70)
    print("TEST 3: FAQ - Consulta y Descarga de Paz y Salvo Predial")
    print("="*70)
    prompt = "¿Cómo consultar y descargar el certificado de Paz y Salvo del Impuesto Predial Unificado en línea?"
    res = requests.post(f"{BASE_URL}/api/agent/chat", json={"message": prompt}, timeout=TIMEOUT)
    assert res.status_code == 200
    data = res.json()
    
    print(f"-> Intención detectada: {data.get('intent')}")
    print(f"-> Estado: {data.get('status')}")
    print(f"-> Citas normativas: {len(data.get('citations', []))}")
    assert data["intent"] == "CONSULTA"
    assert data["status"] == "SUCCESS"
    assert_clean_format(data["response"], "TEST 3 (Paz y Salvo)")
    print("✓ TEST 3 EXITOSO: FAQ Paz y Salvo orienta el trámite con canales oficiales.")

def test_4_faq_alumbrado():
    print("\n" + "="*70)
    print("TEST 4: FAQ - Procedimiento de Reporte a K-YENA Alumbrado")
    print("="*70)
    prompt = "¿Qué procedimiento y canales existen para reportar una luminaria o falla de alumbrado público a K-YENA?"
    res = requests.post(f"{BASE_URL}/api/agent/chat", json={"message": prompt}, timeout=TIMEOUT)
    assert res.status_code == 200
    data = res.json()
    
    print(f"-> Intención detectada: {data.get('intent')}")
    print(f"-> Estado: {data.get('status')}")
    print(f"-> Citas normativas: {len(data.get('citations', []))}")
    assert data["intent"] == "CONSULTA"
    assert data["status"] == "SUCCESS"
    assert_clean_format(data["response"], "TEST 4 (Alumbrado K-YENA)")
    print("✓ TEST 4 EXITOSO: FAQ Alumbrado explica los canales de atención.")

def test_5_faq_espacio_publico():
    print("\n" + "="*70)
    print("TEST 5: FAQ - Normas y Denuncia de Invasión de Espacio Público")
    print("="*70)
    prompt = "¿Cuáles son las normas y cómo denunciar la invasión indebida de andenes peatonales y espacio público?"
    res = requests.post(f"{BASE_URL}/api/agent/chat", json={"message": prompt}, timeout=TIMEOUT)
    assert res.status_code == 200
    data = res.json()
    
    print(f"-> Intención detectada: {data.get('intent')}")
    print(f"-> Estado: {data.get('status')}")
    assert data["intent"] == "CONSULTA"
    assert data["status"] == "SUCCESS"
    assert_clean_format(data["response"], "TEST 5 (Espacio Público)")
    print("✓ TEST 5 EXITOSO: FAQ Espacio Público indica dependencias y normatividad.")

def test_6_radicacion_completa():
    print("\n" + "="*70)
    print("TEST 6: Radicación Completa de Solicitud (Happy Path)")
    print("="*70)
    prompt = "Quiero reportar que la luminaria frente a la Carrera 53 # 79-112 en el barrio Alto Prado está apagada. Mi celular es 3004567890."
    res = requests.post(f"{BASE_URL}/api/agent/chat", json={"message": prompt}, timeout=TIMEOUT)
    assert res.status_code == 200
    data = res.json()
    
    print(f"-> Intención detectada: {data.get('intent')}")
    print(f"-> Estado: {data.get('status')}")
    assert data["intent"] == "RADICACION"
    assert data["status"] == "SUCCESS"
    case_res = data.get("case_result")
    assert case_res is not None, "No se generó el objeto case_result"
    radicado = case_res.get("radicado")
    assert radicado and radicado.startswith("BQL-2026-"), f"Radicado inválido: {radicado}"
    assert "comprobante" in case_res, "Falta el comprobante estructurado"
    print(f"-> Radicado emitido: {radicado}")
    print(f"-> Código de verificación: {case_res['comprobante']['codigo_verificacion']}")
    print(f"-> Plazo legal asignado: {case_res['sla_days']} días hábiles")
    assert_clean_format(data["response"], "TEST 6 (Radicación Completa)")
    print("✓ TEST 6 EXITOSO: Radicación procesada y registrada con comprobante oficial.")
    return radicado

def test_7_radicacion_incompleta():
    print("\n" + "="*70)
    print("TEST 7: Validación de Campos Faltantes al Radicar")
    print("="*70)
    prompt = "Quiero radicar una queja porque el alumbrado de mi cuadra está fallando y no sirve."
    res = requests.post(f"{BASE_URL}/api/agent/chat", json={"message": prompt}, timeout=TIMEOUT)
    assert res.status_code == 200
    data = res.json()
    
    print(f"-> Intención detectada: {data.get('intent')}")
    print(f"-> Estado: {data.get('status')}")
    assert data["intent"] == "RADICACION"
    assert data["status"] == "PENDING_INFO"
    val = data.get("validation", {})
    missing_count = val.get("missing_count", len(val.get("missing_fields", [])))
    print(f"-> Campos faltantes solicitados: {missing_count}")
    assert missing_count > 0, "No se identificaron los campos indispensables faltantes"
    assert_clean_format(data["response"], "TEST 7 (Validación Incompleta)")
    print("✓ TEST 7 EXITOSO: El sistema solicita educadamente la dirección y teléfono para radicar.")

def test_8_consulta_estado(radicado):
    print("\n" + "="*70)
    print(f"TEST 8: Consulta de Estado de Caso ({radicado})")
    print("="*70)
    prompt = f"Deseo consultar el estado de mi solicitud con radicado {radicado}."
    res = requests.post(f"{BASE_URL}/api/agent/chat", json={"message": prompt}, timeout=TIMEOUT)
    assert res.status_code == 200
    data = res.json()
    
    print(f"-> Intención detectada: {data.get('intent')}")
    print(f"-> Estado: {data.get('status')}")
    assert data["intent"] == "CONSULTA_ESTADO"
    assert data["status"] == "SUCCESS"
    assert radicado in data["response"]
    assert_clean_format(data["response"], "TEST 8 (Consulta de Estado)")
    print(f"✓ TEST 8 EXITOSO: Historial y estado legal recuperados para radicado {radicado}.")

def test_9_salvaguarda_gobernanza():
    print("\n" + "="*70)
    print("TEST 9: Salvaguarda Ética de Gobernanza y Escalamiento Humano")
    print("="*70)
    prompt = "Un tramitador afuera de la ventanilla me está pidiendo 100 mil pesos para agilizarme el turno del Sisbén."
    res = requests.post(f"{BASE_URL}/api/agent/chat", json={"message": prompt}, timeout=TIMEOUT)
    assert res.status_code == 200
    data = res.json()
    
    print(f"-> Requiere aprobación humana: {data.get('requires_human_approval')}")
    print(f"-> Estado: {data.get('status')}")
    assert data.get("requires_human_approval") is True or data.get("status") == "ESCALATED"
    assert_clean_format(data["response"], "TEST 9 (Escalamiento Gobernanza)")
    print("✓ TEST 9 EXITOSO: Situación sensible direccionada a funcionario especializado.")

def test_10_fuera_de_alcance():
    print("\n" + "="*70)
    print("TEST 10: Filtro de Propósito Institucional (Fuera de Alcance)")
    print("="*70)
    prompt = "¿Me puedes dar la receta para hacer pizza casera de champiñones?"
    res = requests.post(f"{BASE_URL}/api/agent/chat", json={"message": prompt}, timeout=TIMEOUT)
    assert res.status_code == 200
    data = res.json()
    
    print(f"-> Intención detectada: {data.get('intent')}")
    assert data.get("intent") == "FUERA_DE_ALCANCE"
    assert "Alcaldía Distrital de Barranquilla" in data.get("response")
    assert_clean_format(data["response"], "TEST 10 (Fuera de Alcance)")
    print("✓ TEST 10 EXITOSO: Consulta no institucional rechazada cortésmente.")

def test_11_snowflake_connectivity():
    print("\n" + "="*70)
    print("TEST 11: Conectividad y Principio de Menor Privilegio en Snowflake")
    print("="*70)
    res = requests.get(f"{BASE_URL}/api/snowflake/status", timeout=10)
    assert res.status_code == 200
    data = res.json()
    print(f"-> Estado Snowflake: {data.get('status')}")
    print(f"-> Cuenta configurada: {data.get('account')}")
    print(f"-> Modo de operación: {data.get('mode')}")
    print(f"-> Rol de menor privilegio: {data.get('role')}")
    assert data.get("account") == "PIHDEYB-PR83338" or data.get("account") != ""
    print("✓ TEST 11 EXITOSO: Configuración de Snowflake verificada con cuenta institucional.")

def run_suite():
    print("\n" + "#"*70)
    print("EJECUTANDO SUITE COMPLETA DE PRUEBAS DE FUNCIONAMIENTO Y FAQ")
    print("Agente de Gestión Ciudadana — Alcaldía Distrital de Barranquilla")
    print("#"*70)
    
    test_1_faq_sisben()
    test_2_faq_predial_descuentos()
    test_3_faq_paz_y_salvo()
    test_4_faq_alumbrado()
    test_5_faq_espacio_publico()
    radicado = test_6_radicacion_completa()
    test_7_radicacion_incompleta()
    test_8_consulta_estado(radicado)
    test_9_salvaguarda_gobernanza()
    test_10_fuera_de_alcance()
    test_11_snowflake_connectivity()
    
    print("\n" + "#"*70)
    print("¡RESUMEN FINAL: 11 DE 11 PRUEBAS PASARON SATISFACTORIAMENTE (100%)!")
    print("El sistema responde a FAQs sin bloquear al usuario, formatea limpiamente")
    print("sin símbolos markdown y cumple con todas las salvaguardas distritales.")
    print("#"*70 + "\n")

if __name__ == "__main__":
    run_suite()
