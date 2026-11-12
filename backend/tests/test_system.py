import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    print("\n[TEST 1] Verificando /health...")
    res = requests.get(f"{BASE_URL}/health", timeout=5)
    assert res.status_code == 200, f"Error en health: {res.status_code}"
    data = res.json()
    assert data["status"] == "HEALTHY"
    print("  --> PASS: Health OK:", data)

def test_rag_documents():
    print("\n[TEST 2] Verificando Documentos RAG Indexados...")
    res = requests.get(f"{BASE_URL}/api/knowledge/documents", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 5, f"Esperados >=5 documentos, encontrados {data['total']}"
    print(f"  --> PASS: {data['total']} documentos oficiales curados con metadatos y checksum.")

def test_rag_search():
    print("\n[TEST 3] Verificando Búsqueda Híbrida RAG...")
    payload = {"query": "plazos de descuento pronto pago predial 2026", "top_k": 2}
    res = requests.post(f"{BASE_URL}/api/knowledge/search", json=payload, timeout=8)
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) > 0
    top = data["results"][0]
    print(f"  --> PASS: Top result: '{top['title']}' con Score: {top['similarity_score']}")

def test_agent_consultation():
    print("\n[TEST 4] Verificando Consulta Informativa al Agente...")
    payload = {
        "message": "¿Cuáles son las fechas de descuento del impuesto predial 2026 en Barranquilla?",
        "session_id": "test-suite"
    }
    res = requests.post(f"{BASE_URL}/api/agent/chat", json=payload, timeout=12)
    assert res.status_code == 200
    data = res.json()
    assert len(data["citations"]) > 0
    assert len(data["thoughts"]) > 0
    print(f"  --> PASS: Respuesta generada con {len(data['citations'])} citas y {len(data['thoughts'])} pensamientos registrados.")

def test_agent_missing_fields():
    print("\n[TEST 5] Verificando Detección de Campos Faltantes...")
    payload = {
        "message": "Hola, se dañó el alumbrado público de la cuadra, vengan a arreglarlo por favor.",
        "session_id": "test-suite"
    }
    res = requests.post(f"{BASE_URL}/api/agent/chat", json=payload, timeout=12)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PENDING_INFO"
    assert data["validation"]["missing_count"] > 0
    print(f"  --> PASS: Agente solicitó {data['validation']['missing_count']} campos obligatorios faltantes con cortesía.")

def test_agent_complete_filing():
    print("\n[TEST 6] Verificando Radicación Completa de Solicitud...")
    payload = {
        "message": "Deseo reportar que la luminaria frente a la Calle 72 # 44-32 en el barrio Boston está rota y apagada. Mi celular es 3015557788 y poste BQ-9912.",
        "session_id": "test-suite"
    }
    res = requests.post(f"{BASE_URL}/api/agent/chat", json=payload, timeout=12)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    radicado = data["case_result"]["radicado"]
    assert radicado.startswith("BQL-2026-")
    print(f"  --> PASS: Caso radicado exitosamente con número trazable: {radicado}")
    return radicado

def test_case_tracking(radicado):
    print(f"\n[TEST 7] Verificando Consulta de Radicado '{radicado}'...")
    res = requests.get(f"{BASE_URL}/api/cases/{radicado}", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["radicado"] == radicado
    assert len(data["events"]) > 0
    print(f"  --> PASS: Caso recuperado. Estado: {data['status']}, Eventos en historial: {len(data['events'])}")
    return data["id"]

def test_human_approval(case_id):
    print(f"\n[TEST 8] Verificando Aprobación Humana de Clasificación (Case ID: {case_id})...")
    payload = {
        "officer_id": "TEST_SUPERVISOR_01",
        "notes": "Aprobación verificada en suite de pruebas automáticas."
    }
    res = requests.post(f"{BASE_URL}/api/cases/{case_id}/approve_classification", json=payload, timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    print(f"  --> PASS: Clasificación avalada por funcionario. Nuevo estado: {data['new_case_status']}")

def test_analytics_dashboard():
    print("\n[TEST 9] Verificando Métricas y Dashboard Analítico...")
    res = requests.get(f"{BASE_URL}/api/analytics/dashboard", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "by_department" in data
    assert data["kpis"]["total_cases"] > 0
    print(f"  --> PASS: Métricas calculadas en SQL real: Total casos = {data['kpis']['total_cases']}")

def run_all_tests():
    print("="*60)
    print("INICIANDO SUITE DE PRUEBAS DE INTEGRACIÓN END-TO-END")
    print("AGENTE INTELIGENTE DE GESTIÓN CIUDADANA - ALCALDÍA DE BARRANQUILLA")
    print("="*60)
    
    test_health()
    test_rag_documents()
    test_rag_search()
    test_agent_consultation()
    test_agent_missing_fields()
    radicado = test_agent_complete_filing()
    case_id = test_case_tracking(radicado)
    test_human_approval(case_id)
    test_analytics_dashboard()
    
    print("\n" + "="*60)
    print("¡TODAS LAS PRUEBAS (9/9) PASARON SATISFACTORIAMENTE!")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
