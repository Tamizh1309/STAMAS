import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("stamas.requirement_extractor")

class RequirementExtractorService:
    @staticmethod
    def extract_requirements_from_pages(pages: List[Dict[str, Any]], document_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract structured tender requirements from parsed tender document pages.
        Retains source page number, verbatim evidence text, category, mandatory status,
        and extracted numeric constraints without hallucinating data.
        """
        requirements = []
        req_counter = 1

        # Patterns for classification & constraint detection
        financial_keywords = [
            "turnover", "crore", "lakh", "financial capacity", "balance sheet", 
            "audited", "ca certificate", "emd", "earnest money", "bank guarantee", "financial"
        ]
        technical_keywords = [
            "past performance", "executed", "similar contracts", "similar projects", 
            "experience", "oem", "maf", "manufacturer authorization", "technical capacity", 
            "iso 9001", "iso 27001", "server", "cyber security"
        ]
        eligibility_keywords = [
            "indian registered", "companies act", "llp act", "joint venture", 
            "consortium", "registered entity", "eligibility criteria"
        ]
        document_keywords = [
            "gst certificate", "certificate of incorporation", "undertaking", 
            "stamp paper", "non-blacklisting", "mandatory document", "checklist"
        ]

        mandatory_indicators = ["must", "shall", "required", "mandatory", "compulsory", "failure to submit"]

        for page in pages:
            page_num = page.get("page_number", 1)
            text_content = page.get("text_content", "")
            if not text_content:
                continue

            # Split content into paragraphs or logical requirement lines
            lines = [l.strip() for l in text_content.split("\n") if l.strip()]

            for line in lines:
                line_lower = line.lower()

                # Skip header/footer noise and section titles
                if len(line) < 15 or "government e-marketplace" in line_lower or "tender specification" in line_lower or "compliance document" in line_lower:
                    continue
                
                # Skip pure section titles like "SECTION II: ..." or "3. FINANCIAL CAPACITY & TURNOVER"
                if line_lower.startswith("section ") or (re.match(r'^\d+\.\s+[A-Z\s&]+$', line) and not any(w in line_lower for w in ["must", "shall", "required", "iso", "gst"])):
                    continue

                # Check if line contains a requirement signal
                is_financial = any(kw in line_lower for kw in financial_keywords)
                is_technical = any(kw in line_lower for kw in technical_keywords)
                is_eligibility = any(kw in line_lower for kw in eligibility_keywords)
                is_document = any(kw in line_lower for kw in document_keywords)

                if not (is_financial or is_technical or is_eligibility or is_document or line.startswith("-") or re.match(r'^\d+\.\s+', line)):
                    continue

                # Categorization logic
                if is_financial:
                    category = "FINANCIAL"
                elif is_technical:
                    category = "TECHNICAL"
                elif is_eligibility:
                    category = "ELIGIBILITY"
                elif is_document:
                    category = "DOCUMENT"
                else:
                    category = "OTHER"

                # Mandatory check
                is_mandatory = any(m_word in line_lower for m_word in mandatory_indicators) or line_lower.startswith("-") or "must" in line_lower

                # Numeric threshold extraction
                threshold = None
                unit = None
                currency = None
                constraint_type = "TEXT_MATCH"

                # Extract Turnover / Financial Amounts (e.g. INR 5.00 Crore / Rs. 10 Lakhs)
                turnover_match = re.search(r'(inr|rs\.?)\s*([\d\.]+)\s*(crore|lakh|lakhs)', line, re.IGNORECASE)
                if turnover_match:
                    curr_str, val_str, unit_str = turnover_match.groups()
                    try:
                        num_val = float(val_str)
                        currency = "INR"
                        unit = unit_str.upper()
                        if "crore" in unit_str.lower():
                            threshold = num_val * 10000000
                        elif "lakh" in unit_str.lower():
                            threshold = num_val * 100000
                        constraint_type = "NUMERIC_THRESHOLD"
                    except ValueError:
                        pass
                
                # Extract Experience / Past Performance Counts (e.g., at least 3 similar projects)
                exp_match = re.search(r'(\d+)\s*similar\s*(projects|contracts)', line, re.IGNORECASE)
                if exp_match:
                    try:
                        threshold = float(exp_match.group(1))
                        unit = "PROJECTS"
                        constraint_type = "EXPERIENCE"
                    except ValueError:
                        pass

                # ISO or MAF Certification Check
                if "iso" in line_lower or "maf" in line_lower or "oem" in line_lower:
                    constraint_type = "CERTIFICATION"
                elif category == "DOCUMENT":
                    constraint_type = "DOCUMENT_PRESENCE"

                # Confidence calculation
                confidence = 0.95 if (threshold or constraint_type in ["CERTIFICATION", "DOCUMENT_PRESENCE"]) else 0.85
                status = "EXTRACTED"
                
                # Flag low confidence or ambiguous lines for REVIEW
                if "may" in line_lower or "optional" in line_lower or confidence < 0.8:
                    status = "REVIEW"

                # Clean requirement text
                clean_req_text = line.lstrip("-1234567890. ").strip()
                if not clean_req_text:
                    clean_req_text = line.strip()

                req_code = f"REQ-{req_counter:03d}"
                req_counter += 1

                requirements.append({
                    "req_code": req_code,
                    "category": category,
                    "text": clean_req_text,
                    "mandatory": is_mandatory,
                    "constraint_type": constraint_type,
                    "threshold": threshold,
                    "unit": unit,
                    "currency": currency,
                    "source_document": document_name or "Tender_Document.pdf",
                    "source_page": page_num,
                    "evidence_text": line.strip(),
                    "confidence": confidence,
                    "status": status
                })

        return requirements
