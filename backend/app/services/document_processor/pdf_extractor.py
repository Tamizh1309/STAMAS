import pymupdf  # PyMuPDF
import os
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("stamas.pdf_extractor")

class PDFExtractorService:
    @staticmethod
    def normalize_text(text: str) -> str:
        if not text:
            return ""
        # Remove null characters
        text = text.replace("\x00", "")
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Normalize repeated whitespace but preserve newlines
        # Convert multiple spaces/tabs into a single space
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    @staticmethod
    def calculate_quality(text: str) -> str:
        # Simple deterministic quality classification
        char_count = len(text)
        if char_count > 500:
            return "HIGH"
        elif char_count > 100:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def extract_pdf_data(file_path: str) -> Dict[str, Any]:
        """
        Extract page text, tables, and total page count from a PDF document.
        Returns a dictionary with metadata, full text, and per-page text details.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at path: {file_path}")

        doc = pymupdf.open(file_path)
        page_count = len(doc)
        pages = []
        full_text_list = []
        
        has_text_layer = False
        has_low_text_layer = False

        for page_idx in range(page_count):
            page = doc.load_page(page_idx)
            text = page.get_text("text") or ""
            
            cleaned_text = PDFExtractorService.normalize_text(text)
            
            quality = PDFExtractorService.calculate_quality(cleaned_text)
            
            if len(cleaned_text) > 100:
                has_text_layer = True
            elif len(page.get_images()) > 0:
                has_low_text_layer = True
            
            # Extract basic tabular layout structures if present
            tables = []
            try:
                tabs = page.find_tables()
                if tabs and tabs.tables:
                    for t in tabs.tables:
                        table_df = t.extract()
                        if table_df:
                            tables.append(table_df)
            except Exception as e:
                logger.debug(f"Table extraction skip on page {page_idx + 1}: {e}")

            method = "TEXT_LAYER" if len(cleaned_text) > 50 else "UNAVAILABLE"

            pages.append({
                "page_number": page_idx + 1,
                "text_content": cleaned_text,
                "tables_data": tables,
                "extraction_quality": quality,
                "extraction_method": method
            })
            
            if cleaned_text:
                full_text_list.append(f"--- PAGE {page_idx + 1} ---\n" + cleaned_text)

        doc.close()
        full_text = "\n\n".join(full_text_list)
        
        doc_extraction_method = "UNAVAILABLE"
        if has_text_layer and has_low_text_layer:
            doc_extraction_method = "MIXED"
        elif has_text_layer:
            doc_extraction_method = "TEXT_LAYER"

        return {
            "page_count": page_count,
            "total_characters": len(full_text),
            "full_text": full_text,
            "pages": pages,
            "extraction_method": doc_extraction_method
        }
