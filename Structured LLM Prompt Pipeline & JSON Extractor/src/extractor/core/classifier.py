"""
Autonomous Document Classifier for Model Chaining.
Automatically identifies document type (invoice, resume, receipt) from text or visual hints.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger("extractor.classifier")


class DocumentClassifier:
    """Classifies document type autonomously before routing to specialized extraction schemas."""

    # Fast heuristic keyword indicators
    RESUME_INDICATORS = [
        r"\beducation\b", r"\bexperience\b", r"\bskills\b", r"\bcurriculum vitae\b",
        r"\bresume\b", r"\bprojects\b", r"\bwork history\b", r"\buniversity\b",
        r"\bbachelor\b", r"\bmaster\b", r"\bph\.?d\b", r"\bgithub\b", r"\blinkedin\b"
    ]
    INVOICE_INDICATORS = [
        r"\binvoice\b", r"\binvoice no\b", r"\binv-\d+", r"\bbill to\b",
        r"\bdue date\b", r"\bunit price\b", r"\bline total\b", r"\bgrand total\b",
        r"\bsupplier\b", r"\bvendor\b", r"\bpayment terms\b"
    ]
    RECEIPT_INDICATORS = [
        r"\breceipt\b", r"\bcashier\b", r"\bregister\b", r"\bcard number\b",
        r"\btrans #\b", r"\btip\b", r"\bsubtotal\b", r"\bchange due\b",
        r"\bstore #\b", r"\btax #\b", r"\bauth code\b", r"\bvisa\b", r"\bmastercard\b"
    ]

    @classmethod
    def classify(cls, text: str, filename: Optional[str] = None) -> str:
        """
        Classify document content into 'invoice', 'resume', or 'receipt'.
        Combines filename semantics with textual feature analysis.
        """
        fn = (filename or "").lower()

        # Filename heuristics
        if any(w in fn for w in ["resume", "cv", "bio"]):
            return "resume"
        if any(w in fn for w in ["receipt", "slip", "bill", "ticket"]):
            return "receipt"
        if any(w in fn for w in ["invoice", "inv"]):
            return "invoice"

        clean_text = text.lower()

        # Scoring heuristics based on domain density
        resume_score = sum(1 for p in cls.RESUME_INDICATORS if re.search(p, clean_text))
        invoice_score = sum(1 for p in cls.INVOICE_INDICATORS if re.search(p, clean_text))
        receipt_score = sum(1 for p in cls.RECEIPT_INDICATORS if re.search(p, clean_text))

        scores = {
            "resume": resume_score,
            "invoice": invoice_score,
            "receipt": receipt_score,
        }

        best_type, highest_score = max(scores.items(), key=lambda x: x[1])

        # If confident, return best match; default to invoice if ambiguous
        if highest_score > 0:
            logger.info("Auto-classified document as '%s' (score: %d)", best_type, highest_score)
            return best_type

        return "invoice"
