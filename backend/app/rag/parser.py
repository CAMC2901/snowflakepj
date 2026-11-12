import hashlib
from pathlib import Path
from typing import Dict, Any, List
import pymupdf

def calculate_checksum(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

class DocumentParser:
    """Extrae texto estructurado y metadatos de archivos PDF y Markdown."""
    
    @staticmethod
    def parse_pdf(pdf_path: Path) -> Dict[str, Any]:
        doc = pymupdf.open(str(pdf_path))
        full_text = []
        pages_data = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            cleaned_text = DocumentParser._clean_text(text)
            pages_data.append({
                "page": page_num + 1,
                "text": cleaned_text
            })
            full_text.append(cleaned_text)
            
        doc.close()
        
        checksum = calculate_checksum(pdf_path)
        return {
            "filename": pdf_path.name,
            "format": "PDF",
            "file_size": pdf_path.stat().st_size,
            "checksum": checksum,
            "full_text": "\n\n".join(full_text),
            "pages": pages_data,
            "page_count": len(pages_data)
        }

    @staticmethod
    def parse_markdown(md_path: Path) -> Dict[str, Any]:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        cleaned_text = DocumentParser._clean_text(content)
        checksum = calculate_checksum(md_path)
        return {
            "filename": md_path.name,
            "format": "MARKDOWN",
            "file_size": md_path.stat().st_size,
            "checksum": checksum,
            "full_text": cleaned_text,
            "pages": [{"page": 1, "text": cleaned_text}],
            "page_count": 1
        }

    @staticmethod
    def _clean_text(text: str) -> str:
        # Normalizar espacios y saltos de línea repetidos preservando artículos y tablas
        lines = [line.strip() for line in text.split("\n")]
        cleaned = "\n".join([line for line in lines if line])
        return cleaned
