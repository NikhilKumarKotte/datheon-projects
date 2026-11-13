"""
Advanced AI Leverage & Innovation Module for Document Q&A.
Features:
1. Multi-Query Expansion & Semantic Rephrasing
2. Conversational Contextualizer (Multi-turn RAG Memory)
3. Factual Grounding Confidence Index (Hallucination Risk Meter)
4. Document Intelligence & Executive Summary Generator
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiQueryExpander:
    """Generates semantically diverse search queries from a single user question

    to overcome vocabulary mismatch and improve retrieval recall.
    """

    SYNONYM_MAP = {
        "remote": ["telecommute", "work from home", "hybrid", "wfh", "distributed"],
        "vacation": ["pto", "paid time off", "annual leave", "holidays", "leave accrual"],
        "stipend": ["allowance", "reimbursement", "budget", "expenses", "subsidy", "fund"],
        "insurance": ["healthcare", "medical", "dental", "vision", "health benefits"],
        "security": ["encryption", "mfa", "passwords", "breach", "confidentiality"],
        "ai": ["artificial intelligence", "llm", "generative ai", "models", "data science"],
        "equipment": ["hardware", "laptop", "monitor", "ergonomic chair", "desk"],
    }

    @classmethod
    def expand_query(cls, query: str) -> List[str]:
        """Generates multiple search perspectives for a user query.

        Args:
            query: Original user question.

        Returns:
            List of 2-4 varied search query strings.
        """
        queries = [query.strip()]
        lower_q = query.lower()

        # Identify keywords and generate tailored variations
        expansions = []
        for term, synonyms in cls.SYNONYM_MAP.items():
            if term in lower_q:
                for syn in synonyms[:2]:
                    # Replace keyword with synonym
                    subbed = re.sub(rf"\b{term}\b", syn, lower_q, flags=re.IGNORECASE)
                    if subbed not in queries and subbed not in expansions:
                        expansions.append(subbed)

        # Add generalized keyword query
        words = [w for w in re.findall(r"\w+", lower_q) if len(w) > 3]
        if words:
            expansions.append(" ".join(words))

        queries.extend(expansions[:3])
        return queries


class ConversationalContextualizer:
    """Reformulates follow-up conversational queries into standalone questions

    using chat history context, preventing multi-turn retrieval failure.
    """

    PRONOUNS = {"it", "this", "that", "they", "them", "these", "those", "he", "she"}

    @classmethod
    def contextualize(cls, current_query: str, chat_history: List[Dict[str, str]]) -> str:
        """Contextualizes an ambiguous follow-up question based on prior turns.

        Args:
            current_query: The latest user prompt.
            chat_history: Prior chat turns [{'role': 'user'|'assistant', 'content': ...}].

        Returns:
            Self-contained search query.
        """
        if not chat_history:
            return current_query

        words = set(re.findall(r"\w+", current_query.lower()))
        has_pronoun = bool(words & cls.PRONOUNS)
        is_short = len(current_query.split()) <= 6

        if not (has_pronoun or is_short):
            return current_query

        # Retrieve last user question and extract dominant noun phrases
        last_user_query = ""
        for turn in reversed(chat_history):
            if turn.get("role") == "user":
                last_user_query = turn.get("content", "")
                break

        if not last_user_query:
            return current_query

        # Extract meaningful anchor tokens from previous question
        stop_tokens = {"what", "is", "the", "are", "how", "many", "does", "can", "i", "about"}
        prev_keywords = [
            w for w in re.findall(r"\w+", last_user_query.lower()) if w not in stop_tokens and len(w) > 3
        ]

        if prev_keywords:
            anchor = " ".join(prev_keywords[:3])
            contextualized = f"{current_query} (regarding {anchor})"
            logger.info(f"Contextualized query: '{current_query}' -> '{contextualized}'")
            return contextualized

        return current_query


class GroundingConfidenceEvaluator:
    """Calculates factual grounding metrics and hallucination risk indices

    by analyzing token overlap, vector proximity, and citation density.
    """

    @classmethod
    def evaluate(
        cls,
        answer: str,
        retrieved_docs: List[Document],
        highest_vector_confidence: float,
    ) -> Dict[str, Any]:
        """Computes factual grounding metrics.

        Args:
            answer: Generated or synthesized answer.
            retrieved_docs: Top context documents retrieved.
            highest_vector_confidence: Highest similarity score from vector store.

        Returns:
            Dictionary with grounding score (0-100), risk level, and rationale.
        """
        if not retrieved_docs or not answer.strip():
            return {
                "grounding_score": 0.0,
                "hallucination_risk": "High",
                "risk_color": "#EF4444",
                "overlap_ratio": 0.0,
                "vector_confidence": 0.0,
                "citation_count": 0,
            }

        # Check refusal / out of scope pattern
        refusal_phrases = [
            "do not contain sufficient information",
            "not present in the indexed documents",
            "no documents have been indexed",
        ]
        if any(rp in answer.lower() for rp in refusal_phrases):
            return {
                "grounding_score": 100.0,
                "hallucination_risk": "Zero (Correct Refusal)",
                "risk_color": "#10B981",
                "overlap_ratio": 1.0,
                "vector_confidence": highest_vector_confidence,
                "citation_count": 0,
            }

        # Extract answer terms
        answer_terms = set(re.findall(r"\b[a-zA-Z]{4,}\b", answer.lower()))
        stop_words = {
            "this", "that", "with", "from", "have", "been", "were", "what", "which",
            "their", "there", "about", "would", "could", "should", "document", "page",
        }
        filtered_answer_terms = answer_terms - stop_words

        if not filtered_answer_terms:
            return {
                "grounding_score": 75.0,
                "hallucination_risk": "Low",
                "risk_color": "#10B981",
                "overlap_ratio": 0.75,
                "vector_confidence": highest_vector_confidence,
                "citation_count": 1,
            }

        # Extract context terms
        all_context_text = " ".join([d.page_content.lower() for d in retrieved_docs])
        context_terms = set(re.findall(r"\b[a-zA-Z]{4,}\b", all_context_text))

        # Calculate lexical support
        matched_terms = filtered_answer_terms & context_terms
        overlap_ratio = len(matched_terms) / len(filtered_answer_terms)

        # Count citation tags
        citation_count = len(re.findall(r"\[Document:.*?Page:.*?\]", answer))

        # Composite Grounding Score:
        # 50% Lexical Token Overlap + 40% Vector Proximity + 10% Citation Density
        citation_bonus = min(0.10, citation_count * 0.05)
        raw_score = (overlap_ratio * 0.50) + (highest_vector_confidence * 0.40) + citation_bonus
        final_score = round(min(1.0, max(0.0, raw_score)) * 100, 1)

        if final_score >= 70.0:
            risk = "Very Low (Strongly Grounded)"
            color = "#10B981"  # Emerald
        elif final_score >= 50.0:
            risk = "Low (Adequately Grounded)"
            color = "#3B82F6"  # Blue
        elif final_score >= 35.0:
            risk = "Moderate"
            color = "#F59E0B"  # Amber
        else:
            risk = "High (Potential Hallucination)"
            color = "#EF4444"  # Red

        return {
            "grounding_score": final_score,
            "hallucination_risk": risk,
            "risk_color": color,
            "overlap_ratio": round(overlap_ratio * 100, 1),
            "vector_confidence": round(highest_vector_confidence * 100, 1),
            "citation_count": citation_count,
        }


class DocumentIntelligenceService:
    """Extracts executive summaries, key topics, and critical numerical metrics

    from indexed documents.
    """

    @classmethod
    def generate_executive_summary(cls, documents: List[Document]) -> Dict[str, Any]:
        """Produces a structured executive briefing of loaded documents.

        Args:
            documents: List of Document pages/sections.

        Returns:
            Dictionary with title, key takeaways, entities, and numerical highlights.
        """
        if not documents:
            return {
                "title": "No Documents Loaded",
                "summary": "Please upload or load sample documents to generate an executive intelligence summary.",
                "highlights": [],
                "numbers": [],
                "doc_count": 0,
                "total_pages": 0,
            }

        full_text = " ".join([d.page_content for d in documents])
        file_names = list({d.metadata.get("file_name", "Document") for d in documents})

        # Extract monetary amounts and key figures
        money_matches = list(set(re.findall(r"\$[\d,]+(?:\.\d+)?(?:\s?(?:USD|EUR|GBP))?", full_text)))
        days_matches = list(set(re.findall(r"\b\d+\s?(?:days|weeks|months|hours|business days)\b", full_text, flags=re.I)))

        # Extract major section headers or topics
        headings = list(set(re.findall(r"(?:^|\n)(?:[0-9]+\.\s+([^\n]+)|##\s+([^\n]+))", full_text)))
        clean_headings = []
        for h1, h2 in headings:
            h = (h1 or h2).strip()
            if 4 < len(h) < 60 and h not in clean_headings:
                clean_headings.append(h)

        total_words = len(full_text.split())

        return {
            "title": f"Executive Intelligence: {', '.join(file_names[:2])}",
            "doc_count": len(file_names),
            "total_pages": len(documents),
            "total_words": total_words,
            "topics": clean_headings[:6],
            "financial_figures": money_matches[:5],
            "time_periods": days_matches[:5],
            "preview_snippet": full_text[:400].strip() + "...",
        }
