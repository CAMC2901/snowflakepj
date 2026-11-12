from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.rag.structured_vector_db import structured_vector_db
from backend.app.rag.vector_store import vector_store

def tool_search_knowledge(
    query: str,
    db: Session,
    top_k: int = 4,
    category_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Herramienta search_knowledge: Busca en la base de datos vectorial estructurada
    de la Alcaldía Distrital de Barranquilla (vigencia fiscal 2026).
    """
    try:
        # 1. Búsqueda vectorial estructurada prioritaria
        structured_matches = structured_vector_db.search(query=query, top_k=top_k, category=category_filter)
        
        citations = []
        if structured_matches:
            for i, item in enumerate(structured_matches):
                citations.append({
                    "citation_index": i + 1,
                    "citation_tag": f"[{item['doc_code']}-REF{i+1}]",
                    "title": item["title"],
                    "category": item["category"],
                    "authority": item["authority"],
                    "article_reference": item.get("article_reference", f"Resolución Distrital 2026 - {item['topic']}"),
                    "source_url": item["source_url"],
                    "validity_date": str(item.get("validity_year", 2026)),
                    "checksum": f"SHA256-{item['id']}",
                    "similarity_score": item["similarity_score"],
                    "content": item["content"],
                    "key_facts": item.get("key_facts", {}),
                    "requirements": item.get("requirements", []),
                    "steps": item.get("steps", []),
                    "channels": item.get("channels", [])
                })
        else:
            # 2. Respaldo en vector store clásico si no hubiese matches
            results = vector_store.search(query=query, db=db, top_k=top_k, category_filter=category_filter)
            for i, item in enumerate(results):
                citations.append({
                    "citation_index": i + 1,
                    "citation_tag": f"[{item['doc_code']}-REF{i+1}]",
                    "title": item["title"],
                    "category": item["category"],
                    "authority": item["authority"],
                    "article_reference": item["article_reference"],
                    "source_url": item["source_url"],
                    "validity_date": item["validity_date"],
                    "checksum": item["checksum"],
                    "similarity_score": item["similarity_score"],
                    "content": item["content"],
                    "key_facts": {},
                    "requirements": [],
                    "steps": [],
                    "channels": []
                })
            
        return {
            "status": "SUCCESS",
            "query": query,
            "total_found": len(citations),
            "citations": citations,
            "has_evidence": len(citations) > 0 and citations[0]["similarity_score"] >= 0.20
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "query": query,
            "error": str(e),
            "citations": [],
            "has_evidence": False
        }
