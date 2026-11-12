import os
from pathlib import Path
import fitz # PyMuPDF

DOCS_DIR = Path(__file__).resolve().parent / "documents"

def generate_pdf_from_text(title: str, text: str, output_path: Path):
    doc = fitz.open()
    
    # Split text into paragraphs
    paragraphs = text.split("\n\n")
    current_page = doc.new_page()
    
    # Title
    rect_title = fitz.Rect(50, 40, 550, 75)
    current_page.insert_textbox(rect_title, title, fontsize=13, fontname="helv", color=(0.06, 0.16, 0.26))
    
    y = 85.0
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Estimate height
        lines = para.split("\n")
        para_height = len(lines) * 14 + 10
        if y + para_height > 780:
            current_page = doc.new_page()
            y = 50.0
            
        rect_para = fitz.Rect(50, y, 550, min(y + para_height + 20, 790))
        current_page.insert_textbox(rect_para, para, fontsize=9, fontname="helv", color=(0.14, 0.22, 0.27))
        y += para_height + 8
        
    pages_count = len(doc)
    doc.save(str(output_path))
    doc.close()
    print(f"PDF generado correctamente: {output_path.name} ({pages_count} páginas)")

def main():
    md_files = list(DOCS_DIR.glob("*.md"))
    for md_file in md_files:
        pdf_name = md_file.stem + ".pdf"
        pdf_path = DOCS_DIR / pdf_name
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.split("\n")
        title = lines[0].replace("#", "").strip() if lines else md_file.stem
        body = "\n".join(lines[1:])
        generate_pdf_from_text(title, body, pdf_path)

if __name__ == "__main__":
    main()
