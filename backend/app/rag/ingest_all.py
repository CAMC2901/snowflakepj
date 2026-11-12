from pathlib import Path
from backend.app.core.database import SessionLocal, init_db
from backend.app.rag.vector_store import vector_store

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "documents"

METADATA_REGISTRY = {
    "01_guia_tramites_alumbrado_barranquilla.pdf": {
        "doc_code": "DOC-ALUMBRADO-01",
        "title": "Guía Oficial de Atención y Reportes de Alumbrado Público Barranquilla",
        "category": "Alumbrado Público",
        "authority": "Alcaldía Distrital de Barranquilla / K-YENA S.A.S.",
        "source_url": "https://www.barranquilla.gov.co/alumbrado-publico",
        "validity_date": "2026 Vigente"
    },
    "02_reglamento_espacio_publico_control_urbano.pdf": {
        "doc_code": "DOC-ESPACIO-02",
        "title": "Reglamento y Procedimiento de Control del Espacio Público y Urbanismo",
        "category": "Espacio Público",
        "authority": "Secretaría Distrital de Control Urbano y Espacio Público",
        "source_url": "https://www.barranquilla.gov.co/controlurbano",
        "validity_date": "2026 Vigente"
    },
    "03_estatuto_tributario_predial_barranquilla.pdf": {
        "doc_code": "DOC-HACIENDA-03",
        "title": "Estatuto Tributario Distrital: Impuesto Predial Unificado e Impuestos Locales",
        "category": "Hacienda Distrital",
        "authority": "Secretaría Distrital de Hacienda - Alcaldía de Barranquilla",
        "source_url": "https://www.barranquilla.gov.co/hacienda",
        "validity_date": "2026 Vigente"
    },
    "04_procedimiento_sisben_iv_gestion_social.pdf": {
        "doc_code": "DOC-SISBEN-04",
        "title": "Guía Operativa del Sistema Sisbén IV - Distrito de Barranquilla",
        "category": "Gestión Social",
        "authority": "Secretaría Distrital de Gestión Social - Oficina Sisbén",
        "source_url": "https://www.barranquilla.gov.co/gestionsocial/sisben",
        "validity_date": "2026 Vigente"
    },
    "05_manual_pqrsd_atencion_ciudadana_alcaldia.pdf": {
        "doc_code": "DOC-PQRSD-05",
        "title": "Manual de Atención Ciudadana y Trámite de PQRSD - Alcaldía de Barranquilla",
        "category": "Atención Ciudadana",
        "authority": "Secretaría General - Alcaldía de Barranquilla",
        "source_url": "https://www.barranquilla.gov.co/atencion-al-ciudadano/pqrsd",
        "validity_date": "2026 Vigente"
    },
    "06_salud_publica_prevencion_dengue_inspeccion.pdf": {
        "doc_code": "DOC-SALUD-06",
        "title": "Protocolo de Salud Ambiental, Vigilancia Epidemiológica y Control de Dengue",
        "category": "Salud Pública",
        "authority": "Secretaría Distrital de Salud - Alcaldía de Barranquilla",
        "source_url": "https://www.barranquilla.gov.co/salud",
        "validity_date": "2026 Vigente"
    },
    "07_preguntas_frecuentes_y_alcance_institucional.pdf": {
        "doc_code": "DOC-FAQ-07",
        "title": "Preguntas Frecuentes (FAQ) y Guía de Alcance Institucional",
        "category": "Atención Ciudadana",
        "authority": "Alcaldía Distrital de Barranquilla - Secretaría General",
        "source_url": "https://www.barranquilla.gov.co/atencion-al-ciudadano/faq",
        "validity_date": "2026 Vigente"
    }
}

def run_ingestion():
    init_db()
    db = SessionLocal()
    try:
        print("--> Iniciando Ingesta y Vectorización de Documentos Oficiales...")
        total_chunks = 0
        for filename, meta in METADATA_REGISTRY.items():
            pdf_path = DOCS_DIR / filename
            if not pdf_path.exists():
                print(f"Archivo no encontrado: {filename}")
                continue
                
            chunks_indexed = vector_store.index_document_file(pdf_path, meta, db)
            total_chunks += chunks_indexed
            print(f" [OK] Indexado '{filename}': {chunks_indexed} fragmentos generados con embeddings 768-dim.")
            
        print(f"--> Ingesta finalizada. Total fragmentos en el sistema RAG: {total_chunks}")
    finally:
        db.close()

if __name__ == "__main__":
    run_ingestion()
