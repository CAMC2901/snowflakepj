from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db, CuratedDocument, DocumentChunk, IngestionLog
from backend.app.rag.vector_store import vector_store

router = APIRouter(prefix="/knowledge", tags=["Conocimiento RAG"])

class SearchKnowledgeRequest(BaseModel):
    query: str
    top_k: int = 4
    category_filter: Optional[str] = None

@router.get("/documents")
def list_curated_documents(db: Session = Depends(get_db)):
    docs = db.query(CuratedDocument).all()
    output = []
    for d in docs:
        chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == d.id).count()
        output.append({
            "id": d.id,
            "doc_code": d.doc_code,
            "title": d.title,
            "category": d.category,
            "authority": d.authority,
            "validity_date": d.validity_date,
            "source_url": d.source_url,
            "checksum": d.checksum,
            "summary": d.summary,
            "chunks_count": chunks_count,
            "created_at": d.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return {"total": len(output), "documents": output}

@router.post("/search")
def direct_search_knowledge(req: SearchKnowledgeRequest, db: Session = Depends(get_db)):
    results = vector_store.search(
        query=req.query,
        db=db,
        top_k=req.top_k,
        category_filter=req.category_filter
    )
    return {"query": req.query, "total_found": len(results), "results": results}
