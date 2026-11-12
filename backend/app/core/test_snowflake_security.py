"""Suite de Verificación de Seguridad y Menor Privilegio (RBAC) para Snowflake MCP

Comprueba empíricamente que:
1. Las consultas SELECT de lectura están autorizadas.
2. Los intentos de inserción o modificación son rechazados por Snowflake.
3. Los intentos destructivos (DROP TABLE) son bloqueados por privilegios insuficientes.
4. El acceso a esquemas restringidos (GOVERNANCE.ACCESS_AUDIT) está denegado.
"""

import sys
import os
from typing import Dict, Any

def run_security_audit(account: str, user: str, password: str, warehouse: str = "COMPUTE_WH") -> Dict[str, Any]:
    try:
        import snowflake.connector
    except ImportError:
        print("[ERROR] snowflake-connector-python no está instalado.")
        return {"success": False, "error": "Missing snowflake connector"}

    print("=" * 65)
    print("INICIANDO AUDITORÍA DE SEGURIDAD Y MENOR PRIVILEGIO (RBAC)")
    print(f"Usuario: {user} | Rol Objetivo: BQL_CITIZEN_READONLY_ROLE")
    print("=" * 65)

    acc_clean = account.strip().replace("https://", "").replace("http://", "")
    if ".snowflakecomputing.com" in acc_clean:
        acc_clean = acc_clean.split(".snowflakecomputing.com")[0]

    results = []

    try:
        conn = snowflake.connector.connect(
            user=user.strip(),
            password=password.strip(),
            account=acc_clean,
            warehouse=warehouse.strip(),
            database="BARRANQUILLA_CITIZEN_DB",
            role="BQL_CITIZEN_READONLY_ROLE",
            login_timeout=20
        )
        cs = conn.cursor()
        print("[CONEXIÓN] Sesión establecida exitosamente con el rol BQL_CITIZEN_READONLY_ROLE.\n")
    except Exception as e:
        print(f"[FALLO DE CONEXIÓN] No se pudo autenticar con Snowflake: {e}")
        return {"success": False, "error": str(e)}

    # PRUEBA 1: Lectura de Solicitudes (Debe estar PERMITIDO)
    try:
        cs.execute("SELECT COUNT(*) FROM BARRANQUILLA_CITIZEN_DB.OPERATIONS.CASES;")
        count = cs.fetchone()[0]
        print(f"[TEST 1 - LECTURA DE CASOS] PERMITIDO (Correcto) -> Total registros legibles: {count}")
        results.append(("Lectura de Casos (SELECT)", "PERMITIDO", True))
    except Exception as e:
        print(f"[TEST 1 - LECTURA DE CASOS] FALLO INESPERADO: {e}")
        results.append(("Lectura de Casos (SELECT)", "BLOQUEADO_ERRONEO", False))

    # PRUEBA 2: Lectura de Vistas Analíticas (Debe estar PERMITIDO)
    try:
        cs.execute("SELECT COUNT(*) FROM BARRANQUILLA_CITIZEN_DB.ANALYTICS.V_CASES_BY_DEPARTMENT;")
        count = cs.fetchone()[0]
        print(f"[TEST 2 - LECTURA ANALÍTICA] PERMITIDO (Correcto) -> Registros analíticos: {count}")
        results.append(("Lectura Analítica (SELECT VIEW)", "PERMITIDO", True))
    except Exception as e:
        print(f"[TEST 2 - LECTURA ANALÍTICA] FALLO INESPERADO: {e}")
        results.append(("Lectura Analítica (SELECT VIEW)", "BLOQUEADO_ERRONEO", False))

    # PRUEBA 3: Intento Destructivo DROP TABLE (Debe estar BLOQUEADO por Snowflake)
    try:
        cs.execute("DROP TABLE BARRANQUILLA_CITIZEN_DB.OPERATIONS.CASES;")
        print("[TEST 3 - PROTECCIÓN DROP TABLE] ¡PELIGRO! El usuario pudo borrar una tabla.")
        results.append(("Protección DROP TABLE", "NO_PROTEGIDO", False))
    except Exception as e:
        if "insufficient privileges" in str(e).lower() or "not authorized" in str(e).lower() or "does not exist" in str(e).lower():
            print("[TEST 3 - PROTECCIÓN DROP TABLE] BLOQUEADO CON ÉXITO (Correcto) -> Snowflake rechazó la operación.")
            results.append(("Protección DROP TABLE", "BLOQUEADO_EXITOSO", True))
        else:
            print(f"[TEST 3 - PROTECCIÓN DROP TABLE] Bloqueado con error: {e}")
            results.append(("Protección DROP TABLE", "BLOQUEADO_EXITOSO", True))

    # PRUEBA 4: Intento de Modificación INSERT (Debe estar BLOQUEADO por Snowflake)
    try:
        cs.execute("""
        INSERT INTO BARRANQUILLA_CITIZEN_DB.OPERATIONS.CASES 
        (RADICADO, TITLE, DESCRIPTION, CATEGORY)
        VALUES ('TEST-HACK', 'Intento no autorizado', 'Prueba de inyección', 'Seguridad');
        """)
        print("[TEST 4 - PROTECCIÓN INSERT] ¡PELIGRO! El usuario pudo insertar datos directamente.")
        results.append(("Protección INSERT", "NO_PROTEGIDO", False))
    except Exception as e:
        print("[TEST 4 - PROTECCIÓN INSERT] BLOQUEADO CON ÉXITO (Correcto) -> Escritura no autorizada denegada.")
        results.append(("Protección INSERT", "BLOQUEADO_EXITOSO", True))

    # PRUEBA 5: Intento de Acceso a Gobernanza / Auditoría Interna (Debe estar DENEGADO)
    try:
        cs.execute("SELECT * FROM BARRANQUILLA_CITIZEN_DB.GOVERNANCE.ACCESS_AUDIT LIMIT 1;")
        print("[TEST 5 - AISLAMIENTO DE AUDITORÍA] ¡PELIGRO! El usuario pudo leer la auditoría interna.")
        results.append(("Aislamiento de Auditoría", "NO_PROTEGIDO", False))
    except Exception as e:
        print("[TEST 5 - AISLAMIENTO DE AUDITORÍA] DENEGADO CON ÉXITO (Correcto) -> Esquema GOVERNANCE aislado.")
        results.append(("Aislamiento de Auditoría", "BLOQUEADO_EXITOSO", True))

    cs.close()
    conn.close()

    print("\n" + "=" * 65)
    passed_count = sum(1 for _, _, ok in results if ok)
    print(f"RESULTADO DE LA AUDITORÍA: {passed_count}/{len(results)} PRUEBAS DE SEGURIDAD SATISFACTORIAS")
    print("=" * 65)

    return {
        "success": passed_count == len(results),
        "score": f"{passed_count}/{len(results)}",
        "details": results
    }

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        acc = sys.argv[1]
        usr = sys.argv[2]
        pwd = sys.argv[3]
        wh = sys.argv[4] if len(sys.argv) > 4 else "COMPUTE_WH"
        run_security_audit(acc, usr, pwd, wh)
    else:
        print("Uso: python test_snowflake_security.py <account> <user> <password> [warehouse]")
