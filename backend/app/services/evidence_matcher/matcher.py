import re
import math
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.requirement import Requirement
from app.models.bidder import Bidder
from app.models.bidder_document import BidderDocument, BidderDocumentPage
from app.models.evidence_match import EvidenceMatch, MatchStatus, MatchingMethod

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "until", "while",
    "of", "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "upon", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don",
    "should", "now", "must", "be", "have", "has", "had", "should", "bidder", "shall", "provide"
}

class EvidenceMatcherService:
    """
    Evidence Matching Engine (Phase 5)
    Identifies relevant bidder document pages for a given tender requirement.
    Preserves requirement -> evidence -> bidder -> document -> page traceability.
    """

    @staticmethod
    def preprocess_requirement(requirement: Requirement) -> Dict[str, Any]:
        text = requirement.text or ""
        text_lower = text.lower()
        
        # Tokenize and normalize words
        words = re.findall(r'\b[a-zA-Z0-9\-\.\:]+\b', text_lower)
        keywords = [w for w in words if w not in STOPWORDS and len(w) > 1]
        
        # Extract technical terms, acronyms, standards (e.g. ISO 9001, GST, CMMI)
        standards = re.findall(r'\b(?:iso|cmmi|gst|gstin|pan|msme|epf|esi|bis|ca|oem)[- ]?[a-zA-Z0-9]*\b', text_lower)
        
        # Extract numeric constraints and years (e.g. 5 years, 50 lakhs, 2018-2025)
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        year_terms = re.findall(r'\b(?:\d+\s*(?:years?|yrs?)|years?\s*of\s*experience)\b', text_lower)
        
        # Key multi-word phrases (bi-grams and tri-grams)
        clean_tokens = [w for w in words if w not in STOPWORDS]
        phrases = []
        for i in range(len(clean_tokens) - 1):
            phrases.append(f"{clean_tokens[i]} {clean_tokens[i+1]}")
            if i < len(clean_tokens) - 2:
                phrases.append(f"{clean_tokens[i]} {clean_tokens[i+1]} {clean_tokens[i+2]}")

        return {
            "req_code": requirement.req_code,
            "category": requirement.category,
            "original_text": text,
            "keywords": list(set(keywords)),
            "standards": list(set(standards)),
            "numbers": list(set(numbers)),
            "year_terms": list(set(year_terms)),
            "phrases": list(set(phrases)),
            "constraint_type": requirement.constraint_type,
            "threshold": requirement.threshold
        }

    @staticmethod
    def extract_evidence_snippet(page_text: str, matched_terms: List[str], max_length: int = 400) -> str:
        """
        Extract concise sentence/paragraph snippet preserving original page text.
        """
        if not page_text or not page_text.strip():
            return ""

        sentences = re.split(r'(?<=[.!?\n])\s+', page_text.strip())
        scored_sentences = []
        
        for i, sentence in enumerate(sentences):
            sent_lower = sentence.lower()
            score = 0
            for term in matched_terms:
                if term.lower() in sent_lower:
                    score += 2 if len(term.split()) > 1 else 1
            if score > 0:
                scored_sentences.append((score, i, sentence))

        if not scored_sentences:
            # Fallback to first paragraph/sentences
            snippet = page_text.strip()[:max_length]
            return snippet if len(page_text.strip()) <= max_length else snippet + "..."

        # Pick highest scoring sentence and include adjacent context if within budget
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        best_idx = scored_sentences[0][1]

        start_idx = max(0, best_idx - 1)
        end_idx = min(len(sentences), best_idx + 2)

        snippet_parts = [sentences[j].strip() for j in range(start_idx, end_idx) if sentences[j].strip()]
        snippet = " ".join(snippet_parts)

        if len(snippet) > max_length:
            snippet = snippet[:max_length] + "..."

        return snippet

    @classmethod
    def calculate_page_match_score(
        cls, req_info: Dict[str, Any], page_text: str, doc_category: Optional[str] = None
    ) -> Tuple[float, List[str], str]:
        """
        Calculates match score between requirement info and page text.
        Returns (score, matched_keywords, reason_explanation).
        """
        if not page_text or not page_text.strip():
            return 0.0, [], "Page text is empty."

        page_lower = page_text.lower()
        matched_keywords = []
        score = 0.0

        # 1. Standards / Certifications / Reg numbers (e.g. ISO 9001, GST) - Highest priority
        matched_standards = []
        for std in req_info["standards"]:
            std_clean = std.replace(" ", "").replace("-", "")
            page_clean = page_lower.replace(" ", "").replace("-", "")
            if std in page_lower or std_clean in page_clean:
                matched_standards.append(std)

        if matched_standards:
            score += 0.50
            matched_keywords.extend([s for s in matched_standards if s not in matched_keywords])

        # 2. Exact phrase matching
        matched_phrases = []
        for phrase in req_info["phrases"]:
            if phrase in page_lower:
                matched_phrases.append(phrase)
        
        if matched_phrases:
            score += min(0.40, len(matched_phrases) * 0.18)
            matched_keywords.extend([p for p in matched_phrases if p not in matched_keywords])

        # 3. Individual keyword matching
        matched_words = []
        for kw in req_info["keywords"]:
            kw_regex = r'\b' + re.escape(kw).replace(r'\-', r'[\-\s]?') + r'\b'
            if re.search(kw_regex, page_lower):
                matched_words.append(kw)

        if req_info["keywords"]:
            keyword_ratio = len(matched_words) / len(req_info["keywords"])
            score += keyword_ratio * 0.40
            matched_keywords.extend([w for w in matched_words if w not in matched_keywords])

        # 4. Numeric, Duration & Monetary alignment
        numeric_matched = False
        if req_info["numbers"]:
            for num in req_info["numbers"]:
                if re.search(r'\b' + re.escape(num) + r'\b', page_text):
                    numeric_matched = True
                    break

        # Check turnover/monetary mention e.g. 12.5 crore
        turnover_presence = re.search(r'(?:₹|rs\.?|inr)?\s*\d+(?:\.\d+)?\s*(?:crore|lakh|lakhs|million|billion)\b', page_lower)
        if turnover_presence and ("turnover" in page_lower or "financial" in page_lower or req_info["category"] == "FINANCIAL"):
            score += 0.20
            numeric_matched = True

        date_range = re.findall(r'\b(19\d\d|20\d\d)\s*(?:to|-|until)\s*(19\d\d|20\d\d)\b', page_lower)
        if date_range:
            for start_yr, end_yr in date_range:
                duration = int(end_yr) - int(start_yr)
                if req_info["threshold"] and duration >= req_info["threshold"]:
                    score += 0.25
                    matched_keywords.append(f"experience duration {start_yr}-{end_yr} ({duration} yrs)")
                    numeric_matched = True

        if numeric_matched and not date_range and not turnover_presence:
            score += 0.10

        # 5. Document category alignment bonus
        if doc_category and req_info["category"]:
            doc_cat_u = doc_category.upper()
            req_cat_u = req_info["category"].upper()
            if doc_cat_u == req_cat_u or (req_cat_u == "ELIGIBILITY" and doc_cat_u in ["CERTIFICATION", "REGISTRATION", "EXPERIENCE"]):
                score += 0.10


        final_score = round(min(1.0, score), 2)

        reasons = []
        if matched_standards:
            reasons.append(f"required standard/code ({', '.join(matched_standards)}) found")
        if matched_phrases:
            reasons.append(f"key phrases matched ({', '.join(matched_phrases[:3])})")
        elif matched_words:
            reasons.append(f"matched keywords ({', '.join(matched_words[:4])})")
        if numeric_matched:
            reasons.append("numeric constraint / date range verified")

        if final_score >= 0.80:
            reason_str = f"Strong evidence match (confidence {final_score:.2f}) because " + " and ".join(reasons) + "."
        elif final_score >= 0.60:
            reason_str = f"Moderate evidence match (confidence {final_score:.2f}) because " + " and ".join(reasons) + "."
        elif final_score >= 0.40:
            reason_str = f"Weak candidate evidence (confidence {final_score:.2f}) with partial keyword overlap."
        else:
            reason_str = f"Low relevance (confidence {final_score:.2f}); insufficient evidence keywords found."

        return final_score, matched_keywords, reason_str


    @classmethod
    def match_requirement_for_bidder(
        cls,
        db: Session,
        tender_id: int,
        bidder_id: int,
        requirement_id: int,
        top_k: int = 5
    ) -> List[EvidenceMatch]:
        """
        Executes evidence matching for a single requirement against a bidder's document pages.
        Validates cross-tender security.
        Persists and returns EvidenceMatch records.
        """
        requirement = db.query(Requirement).filter(
            Requirement.id == requirement_id,
            Requirement.tender_id == tender_id
        ).first()

        if not requirement:
            raise ValueError(f"Requirement {requirement_id} not found under tender {tender_id}")

        bidder = db.query(Bidder).filter(
            Bidder.id == bidder_id,
            Bidder.tender_id == tender_id
        ).first()

        if not bidder:
            raise ValueError(f"Bidder {bidder_id} not found under tender {tender_id}")

        # Clear existing evidence matches for this requirement and bidder (prevents duplicates on rerun)
        db.query(EvidenceMatch).filter(
            EvidenceMatch.bidder_id == bidder_id,
            EvidenceMatch.requirement_id == requirement_id
        ).delete()
        db.commit()

        # Retrieve bidder document pages
        documents = db.query(BidderDocument).filter(
            BidderDocument.bidder_id == bidder_id,
            BidderDocument.tender_id == tender_id
        ).all()

        doc_ids = [d.id for d in documents]
        doc_map = {d.id: d for d in documents}

        if not doc_ids:
            # Create a NOT_FOUND record if bidder has no documents
            no_doc_match = EvidenceMatch(
                tender_id=tender_id,
                requirement_id=requirement_id,
                bidder_id=bidder_id,
                document_id=None,
                page_id=None,
                evidence_text="No bidder documents uploaded or processed for this tender.",
                match_status=MatchStatus.NOT_FOUND.value,
                confidence_score=0.0,
                matching_method=MatchingMethod.KEYWORD.value,
                matched_keywords=[],
                reason="No processed bidder documents available for evidence matching."
            )
            db.add(no_doc_match)
            db.commit()
            db.refresh(no_doc_match)
            return [no_doc_match]

        pages = db.query(BidderDocumentPage).filter(
            BidderDocumentPage.document_id.in_(doc_ids)
        ).all()

        req_info = cls.preprocess_requirement(requirement)
        candidate_matches = []

        for p in pages:
            doc = doc_map.get(p.document_id)
            doc_cat = doc.category if doc else None

            score, matched_kws, reason = cls.calculate_page_match_score(
                req_info=req_info,
                page_text=p.extracted_text,
                doc_category=doc_cat
            )

            # Determine status based on confidence thresholds
            if score >= 0.80:
                status = MatchStatus.MATCHED.value
            elif score >= 0.60:
                status = MatchStatus.PARTIAL.value
            elif score >= 0.40:
                status = MatchStatus.LOW_CONFIDENCE.value
            else:
                status = MatchStatus.NOT_FOUND.value

            if score >= 0.40: # Only treat as candidate evidence if score >= 0.40
                snippet = cls.extract_evidence_snippet(p.extracted_text, matched_kws)
                candidate_matches.append({
                    "document_id": p.document_id,
                    "page_id": p.id,
                    "evidence_text": snippet,
                    "match_status": status,
                    "confidence_score": score,
                    "matching_method": MatchingMethod.KEYWORD.value,
                    "matched_keywords": matched_kws,
                    "reason": reason
                })

        # Sort candidate matches by confidence_score descending
        candidate_matches.sort(key=lambda x: x["confidence_score"], reverse=True)

        stored_matches = []

        if not candidate_matches:
            # Create explicit NOT_FOUND record
            not_found_match = EvidenceMatch(
                tender_id=tender_id,
                requirement_id=requirement_id,
                bidder_id=bidder_id,
                document_id=None,
                page_id=None,
                evidence_text="No relevant evidence found across bidder documents.",
                match_status=MatchStatus.NOT_FOUND.value,
                confidence_score=0.0,
                matching_method=MatchingMethod.KEYWORD.value,
                matched_keywords=[],
                reason="No bidder document pages met the relevance threshold for this requirement."
            )
            db.add(not_found_match)
            db.commit()
            db.refresh(not_found_match)
            stored_matches.append(not_found_match)
        else:
            # Pick top_k evidence matches
            top_candidates = candidate_matches[:top_k]
            for c in top_candidates:
                match_rec = EvidenceMatch(
                    tender_id=tender_id,
                    requirement_id=requirement_id,
                    bidder_id=bidder_id,
                    document_id=c["document_id"],
                    page_id=c["page_id"],
                    evidence_text=c["evidence_text"],
                    match_status=c["match_status"],
                    confidence_score=c["confidence_score"],
                    matching_method=c["matching_method"],
                    matched_keywords=c["matched_keywords"],
                    reason=c["reason"]
                )
                db.add(match_rec)
                stored_matches.append(match_rec)
            
            db.commit()
            for m in stored_matches:
                db.refresh(m)

        return stored_matches

    @classmethod
    def match_all_requirements_for_bidder(
        cls,
        db: Session,
        tender_id: int,
        bidder_id: int
    ) -> List[EvidenceMatch]:
        """
        Batch runs evidence matching for all requirements of a tender for a given bidder.
        Rerun safe: removes existing evidence matches for this (tender_id, bidder_id) first.
        """
        requirements = db.query(Requirement).filter(
            Requirement.tender_id == tender_id
        ).all()

        if not requirements:
            return []

        all_results = []
        for req in requirements:
            matches = cls.match_requirement_for_bidder(
                db=db,
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id
            )
            all_results.extend(matches)

        return all_results
