"""
Unit tests for Advanced RAG Innovation Features:
- MultiQueryExpander
- ConversationalContextualizer
- GroundingConfidenceEvaluator
- DocumentIntelligenceService
"""

import pytest
from langchain_core.documents import Document
from src.advanced_rag import (
    MultiQueryExpander,
    ConversationalContextualizer,
    GroundingConfidenceEvaluator,
    DocumentIntelligenceService,
)


def test_multi_query_expansion():
    query = "What is the flexible remote work policy?"
    expanded = MultiQueryExpander.expand_query(query)
    assert len(expanded) >= 2
    assert query in expanded
    # Check that synonyms or terms were added
    all_text = " ".join(expanded).lower()
    assert "remote" in all_text or "telecommute" in all_text or "hybrid" in all_text


def test_conversational_contextualizer():
    # Turn 1: User asked about stipend
    history = [
        {"role": "user", "content": "How much is the home office equipment stipend?"},
        {"role": "assistant", "content": "Acme provides a one-time stipend of $1,200 USD."},
    ]
    # Turn 2: Follow-up with ambiguous pronoun "it"
    follow_up = "Can I use it for an ergonomic chair?"
    contextualized = ConversationalContextualizer.contextualize(follow_up, history)

    assert "ergonomic chair" in contextualized
    # Should include anchor terms from previous question
    assert "stipend" in contextualized or "office" in contextualized or "equipment" in contextualized


def test_grounding_evaluator_valid_answer():
    docs = [
        Document(
            page_content="Full-time employees receive a one-time home office equipment stipend of $1,200 USD.",
            metadata={"file_name": "handbook.pdf", "page": 1},
        )
    ]
    answer = "Employees receive a one-time stipend of $1,200 USD [Document: handbook.pdf, Page: 1]."
    metrics = GroundingConfidenceEvaluator.evaluate(
        answer=answer, retrieved_docs=docs, highest_vector_confidence=0.85
    )

    assert metrics["grounding_score"] >= 60.0
    assert "Low" in metrics["hallucination_risk"] or "Very Low" in metrics["hallucination_risk"]
    assert metrics["citation_count"] == 1
    assert metrics["overlap_ratio"] > 50.0


def test_grounding_evaluator_refusal():
    docs = [Document(page_content="Some irrelevant text", metadata={"file_name": "doc.pdf", "page": 1})]
    refusal_answer = "I am sorry, but the provided documents do not contain sufficient information to answer this question."
    metrics = GroundingConfidenceEvaluator.evaluate(
        answer=refusal_answer, retrieved_docs=docs, highest_vector_confidence=0.10
    )

    # Correct refusal is awarded 100% grounding confidence with zero hallucination risk
    assert metrics["grounding_score"] == 100.0
    assert "Zero" in metrics["hallucination_risk"]


def test_document_intelligence_service():
    sample_docs = [
        Document(
            page_content="1. Remote Work Policy\nAcme offers a $1,200 USD stipend and 24 days of vacation per year.",
            metadata={"file_name": "handbook.pdf", "page": 1},
        )
    ]
    summary = DocumentIntelligenceService.generate_executive_summary(sample_docs)

    assert summary["doc_count"] == 1
    assert summary["total_pages"] == 1
    assert "$1,200" in " ".join(summary["financial_figures"])
    assert any("24 days" in tp.lower() for tp in summary["time_periods"])
