import re
from typing import List, Dict, Any

class DocumentChunker:
    """Divide documentos en fragmentos semánticos preservando artículos y metadatos."""
    
    @staticmethod
    def chunk_document(
        parsed_doc: Dict[str, Any],
        doc_metadata: Dict[str, Any],
        chunk_size: int = 400,
        chunk_overlap: int = 50
    ) -> List[Dict[str, Any]]:
        full_text = parsed_doc.get("full_text", "")
        
        # Intentar división por encabezados jerárquicos (## Artículo / Sección / 1. ...)
        sections = re.split(r'\n(?=#{1,3}\s|\d+\.\s+[A-ZÁÉÍÓÚÑ])', full_text)
        chunks = []
        chunk_idx = 0
        
        for section in sections:
            section = section.strip()
            if not section or len(section) < 30:
                continue
                
            words = section.split()
            if len(words) <= chunk_size:
                # Extraer posible referencia de artículo o sección
                first_line = section.split("\n")[0]
                art_ref = first_line.replace("#", "").strip()[:80]
                
                chunks.append({
                    "chunk_index": chunk_idx,
                    "content": section,
                    "article_reference": art_ref,
                    "token_count": len(words),
                    "page_number": 1,
                    **doc_metadata
                })
                chunk_idx += 1
            else:
                # Dividir secciones largas en sub-chunks con solapamiento
                step = chunk_size - chunk_overlap
                for i in range(0, len(words), step):
                    sub_words = words[i:i + chunk_size]
                    sub_text = " ".join(sub_words)
                    first_line = section.split("\n")[0].replace("#", "").strip()[:80]
                    
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "content": sub_text,
                        "article_reference": f"{first_line} (Parte {i//step + 1})",
                        "token_count": len(sub_words),
                        "page_number": 1,
                        **doc_metadata
                    })
                    chunk_idx += 1
                    
        return chunks
