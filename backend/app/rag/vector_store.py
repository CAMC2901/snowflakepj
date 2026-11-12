import json
import math
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal, CuratedDocument, DocumentChunk, RawDocument, IngestionLog
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.parser import DocumentParser
from backend.app.rag.chunker import DocumentChunker
from pathlib import Path

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class VectorStore:
    """Índice de conocimiento híbrido (Vectorial Semántico + Palabras Clave BM25) para la Alcaldía."""
    
    def __init__(self):
        pass

    def index_document_file(self, file_path: Path, metadata: Dict[str, Any], db: Session) -> int:
        filename = file_path.name
        
        # 1. Parsear archivo
        if file_path.suffix.lower() == ".pdf":
            parsed = DocumentParser.parse_pdf(file_path)
        else:
            parsed = DocumentParser.parse_markdown(file_path)
            
        # 2. Registrar en RAW
        raw_doc = RawDocument(
            title=metadata.get("title", filename),
            url=metadata.get("source_url", ""),
            entity="Alcaldía Distrital de Barranquilla",
            format=parsed["format"],
            checksum=parsed["checksum"],
            file_size=parsed["file_size"],
            raw_content=parsed["full_text"][:5000],
            status="INDEXED"
        )
        db.add(raw_doc)
        db.commit()

        # 3. Registrar o actualizar en CURATED
        doc_code = metadata.get("doc_code", f"DOC-{file_path.stem[:15].upper()}")
        existing_doc = db.query(CuratedDocument).filter(CuratedDocument.doc_code == doc_code).first()
        if existing_doc:
            db.delete(existing_doc)
            db.commit()

        curated = CuratedDocument(
            doc_code=doc_code,
            title=metadata.get("title", filename),
            category=metadata.get("category", "General"),
            authority=metadata.get("authority", "Alcaldía Distrital de Barranquilla"),
            validity_date=metadata.get("validity_date", "2026 Vigente"),
            source_url=metadata.get("source_url", ""),
            checksum=parsed["checksum"],
            summary=parsed["full_text"][:300] + "..."
        )
        db.add(curated)
        db.commit()
        db.refresh(curated)

        # 4. Chunking
        chunks_data = DocumentChunker.chunk_document(parsed, metadata)
        
        # 5. Generar embeddings y persistir
        chunks_count = 0
        for ch in chunks_data:
            emb = embedding_service.get_embedding(ch["content"])
            chunk_record = DocumentChunk(
                document_id=curated.id,
                chunk_index=ch["chunk_index"],
                content=ch["content"],
                article_reference=ch.get("article_reference", ""),
                page_number=ch.get("page_number", 1),
                token_count=ch.get("token_count", 0),
                embedding_json=json.dumps(emb)
            )
            db.add(chunk_record)
            chunks_count += 1
            
        # 6. Ingestion Log
        log = IngestionLog(
            filename=filename,
            action="INDEX_HYBRID",
            chunks_count=chunks_count,
            status="SUCCESS",
            duration_ms=120
        )
        db.add(log)
        db.commit()
        return chunks_count

    def search(
        self,
        query: str,
        db: Session,
        top_k: int = 4,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query_emb = embedding_service.get_embedding(query)
        stopwords = {
            "cuáles", "cuales", "cuál", "cual", "cómo", "como", "dónde", "donde", "cuándo", "cuando",
            "qué", "que", "por", "para", "con", "del", "las", "los", "una", "uno", "unos", "unas",
            "este", "esta", "estos", "estas", "son", "sus", "ser", "hay", "sobre", "entre"
        }
        raw_terms = set(re.findall(r'\b\w{3,}\b', query.lower()))
        query_terms = raw_terms - stopwords
        if not query_terms:
            query_terms = raw_terms
        
        # Consultar fragmentos de la base de datos
        query_db = db.query(DocumentChunk, CuratedDocument).join(
            CuratedDocument, DocumentChunk.document_id == CuratedDocument.id
        )
        
        if category_filter:
            query_db = query_db.filter(CuratedDocument.category == category_filter)
            
        results = query_db.all()
        scored_chunks = []
        
        for chunk, doc in results:
            emb = json.loads(chunk.embedding_json) if chunk.embedding_json else []
            sem_score = cosine_similarity(query_emb, emb) if emb else 0.0
            
            # Puntuación por coincidencia de términos clave (BM25 simplificado)
            chunk_text_lower = chunk.content.lower()
            keyword_matches = sum(1 for term in query_terms if term in chunk_text_lower)
            lex_score = min(keyword_matches / max(len(query_terms), 1), 1.0)
            
            # Score híbrido: 60% semántico + 40% léxico
            hybrid_score = (0.6 * sem_score) + (0.4 * lex_score)
            
            scored_chunks.append({
                "chunk_id": chunk.id,
                "doc_code": doc.doc_code,
                "title": doc.title,
                "category": doc.category,
                "authority": doc.authority,
                "article_reference": chunk.article_reference,
                "content": chunk.content,
                "source_url": doc.source_url,
                "validity_date": doc.validity_date,
                "checksum": doc.checksum,
                "page_number": chunk.page_number,
                "similarity_score": round(hybrid_score, 4),
                "semantic_score": round(sem_score, 4),
                "lexical_score": round(lex_score, 4)
            })
            
        # Ordenar por mayor score híbrido
        scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_chunks[:top_k]

vector_store = VectorStore()
