import re
from typing import List, Dict, Any

def chunk_page_text(
    document_id: int,
    page_id: int,
    page_number: int,
    document_name: str,
    tender_id: int,
    bidder_id: int,
    page_text: str,
    category: str = "GENERAL",
    max_chunk_chars: int = 500,
    overlap_chars: int = 100
) -> List[Dict[str, Any]]:
    """
    Safely chunks page-level text into smaller segments while preserving metadata
    and preventing line/sentence truncation where possible.
    """
    if not page_text or not page_text.strip():
        return []

    # Clean text slightly while maintaining structure
    clean_text = page_text.strip()

    # Split primarily on paragraphs / double newlines
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', clean_text) if p.strip()]

    raw_chunks: List[str] = []

    for para in paragraphs:
        if len(para) <= max_chunk_chars:
            raw_chunks.append(para)
        else:
            # Split large paragraph into sentences or lines
            sentences = re.split(r'(?<=[.!?])\s+|\n+', para)
            current_chunk = ""
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                if len(current_chunk) + len(sent) + 1 <= max_chunk_chars:
                    current_chunk = f"{current_chunk} {sent}".strip()
                else:
                    if current_chunk:
                        raw_chunks.append(current_chunk)
                    current_chunk = sent
            if current_chunk:
                raw_chunks.append(current_chunk)

    # Now assign indices and attach metadata
    final_chunks: List[Dict[str, Any]] = []

    for idx, text_block in enumerate(raw_chunks):
        if not text_block.strip():
            continue
        chunk_metadata = {
            "document_id": document_id,
            "page_id": page_id,
            "page_number": page_number,
            "document_name": document_name,
            "tender_id": tender_id,
            "bidder_id": bidder_id,
            "category": category,
            "chunk_index": idx
        }
        final_chunks.append({
            "chunk_index": idx,
            "text": text_block.strip(),
            "metadata": chunk_metadata
        })

    return final_chunks
