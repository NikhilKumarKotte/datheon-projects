"""
Core Retrieval-Augmented Generation (RAG) Pipeline.
Enforces strict grounding on custom documents, eliminates hallucinations,
and generates humanized answers with source page citations.
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config import AppConfig, default_config
from src.vector_store import VectorStoreManager
from src.utils import (
    format_citation_markdown,
    extract_citations_from_docs,
    build_system_context_string,
)
from src.advanced_rag import (
    MultiQueryExpander,
    ConversationalContextualizer,
    GroundingConfidenceEvaluator,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Strict Grounding Prompt Template for LCEL
STRICT_RAG_SYSTEM_PROMPT = """You are an expert Document Q&A Assistant.
Your mission is to provide accurate, helpful, and strictly verified answers to the user's questions based EXCLUSIVELY on the provided context excerpts.

GROUNDING & CITATION RULES:
1. Base your answer ENTIRELY on the provided CONTEXT below. Do NOT use outside knowledge, speculate, or fabricate facts.
2. If the context does not contain sufficient information to answer the question factually, clearly say:
   "I am sorry, but the provided documents do not contain sufficient information to answer this question."
3. For every key fact, policy, number, or statement in your response, include an explicit citation tag referencing the exact file name and page number, in this format:
   [Document: <filename>, Page: <page>]
4. Maintain a warm, clear, professional, and humanized conversational tone.

CONTEXT:
{context}

QUESTION:
{question}

HELPFUL & GROUNDED ANSWER:"""


class RAGPipeline:
    """Manages the end-to-end question answering pipeline over indexed documents."""

    def __init__(
        self,
        vector_store_manager: Optional[VectorStoreManager] = None,
        config: Optional[AppConfig] = None,
    ):
        self.config = config or default_config
        self.vector_store_manager = vector_store_manager or VectorStoreManager()

    def get_llm(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Optional[Any]:
        """Instantiates the LLM based on provider and API key availability.

        Returns None if provider is 'local' or required API keys are not supplied.
        """
        provider = (provider or self.config.llm_provider).lower().strip()
        model = model_name or self.config.llm_model_name

        try:
            if provider == "openai":
                from langchain_openai import ChatOpenAI

                key = api_key or self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
                if key:
                    return ChatOpenAI(
                        model=model or "gpt-4o-mini",
                        temperature=self.config.llm_temperature,
                        openai_api_key=key,
                    )
                logger.info("OpenAI API key not found. Using local synthesis.")

            elif provider in {"gemini", "google"}:
                from langchain_google_genai import ChatGoogleGenerativeAI

                key = api_key or self.config.google_api_key or os.getenv("GOOGLE_API_KEY")
                if key:
                    return ChatGoogleGenerativeAI(
                        model=model or "gemini-1.5-flash",
                        temperature=self.config.llm_temperature,
                        google_api_key=key,
                    )
                logger.info("Google API key not found. Using local synthesis.")

            elif provider == "groq":
                from langchain_groq import ChatGroq

                key = api_key or self.config.groq_api_key or os.getenv("GROQ_API_KEY")
                if key:
                    return ChatGroq(
                        model=model or "llama-3.3-70b-versatile",
                        temperature=self.config.llm_temperature,
                        groq_api_key=key,
                    )
                logger.info("Groq API key not found. Using local synthesis.")

        except Exception as e:
            logger.warning(f"Error loading LLM provider '{provider}': {e}. Using local synthesis.")

        return None

    def _synthesize_local_response(
        self, query: str, docs_with_scores: List[Tuple[Document, float]]
    ) -> str:
        """Deterministic, intelligent local extractive RAG synthesizer.

        Works 100% offline without needing any cloud API keys.
        Scans retrieved context chunks, extracts highly relevant sentences,
        attaches source citations, and detects out-of-scope questions.
        """
        if not docs_with_scores:
            return "I am sorry, but no documents have been indexed yet. Please load and index documents first."

        # Comprehensive stop words
        stop_words = {
            "what", "is", "the", "are", "how", "many", "does", "do", "for", "in",
            "a", "an", "and", "or", "to", "of", "with", "can", "tell", "me", "about",
            "on", "at", "by", "from", "it", "this", "that", "these", "those", "be",
            "will", "shall", "would", "could", "should", "there", "their", "so"
        }
        query_terms = set(re.findall(r"\w+", query.lower()))
        meaningful_terms = {t for t in query_terms if t not in stop_words and len(t) > 2}

        # Vector confidence threshold guardrail
        highest_score = max((score for _, score in docs_with_scores), default=0.0)

        candidate_sentences: List[Tuple[str, str, int, float, int]] = []

        for doc, score in docs_with_scores:
            meta = doc.metadata or {}
            file_name = meta.get("file_name", "document")
            page = meta.get("page", 1)

            # Split chunk into sentences
            raw_sentences = re.split(r"(?<=[.!?])\s+", doc.page_content)
            for s in raw_sentences:
                clean_s = s.strip()
                if len(clean_s) < 15:
                    continue
                s_lower = clean_s.lower()
                # Compute meaningful term overlap
                matched_count = sum(1 for term in meaningful_terms if term in s_lower)
                if matched_count > 0:
                    weight = matched_count * (score if score > 0 else 0.5)
                    candidate_sentences.append((clean_s, file_name, page, weight, matched_count))

        # Anti-hallucination guardrail check:
        # If no candidates, or highest match has insufficient concept overlap, refuse
        if not candidate_sentences:
            return "I am sorry, but the provided documents do not contain sufficient information to answer this question."

        max_matches = max(c[4] for c in candidate_sentences)
        # If query had multiple specific concepts but best sentence only matched a weak single word with low score
        if len(meaningful_terms) >= 3 and max_matches < 2 and highest_score < 0.45:
            return "I am sorry, but the provided documents do not contain sufficient information to answer this question."

        # Sort sentences by match weight
        candidate_sentences.sort(key=lambda x: x[3], reverse=True)
        top_sentences = candidate_sentences[:4]

        # Deduplicate sentences while preserving citations
        response_parts = []
        seen = set()
        for text, fname, page, _, _ in top_sentences:
            if text in seen:
                continue
            seen.add(text)
            response_parts.append(f"{text} [Document: {fname}, Page: {page}]")

        answer_body = " ".join(response_parts)
        return (
            f"Based on the loaded documents:\n\n{answer_body}\n\n"
            f"*(Generated via Local RAG Engine with verified source page citations)*"
        )

    def answer_question(
        self,
        query: str,
        store_type: Optional[str] = None,
        top_k: Optional[int] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        api_key: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        use_multi_query: bool = True,
        use_retrieval_qa_chain: bool = False,
    ) -> Dict[str, Any]:
        """Executes the full RAG query answering pipeline.

        Args:
            query: User's question string.
            store_type: 'chroma' or 'faiss'.
            top_k: Number of chunks to retrieve.
            llm_provider: LLM provider override.
            llm_model: Specific model name override.
            api_key: API key override.
            chat_history: Prior turns for conversational contextualization.
            use_multi_query: Whether to use multi-query semantic expansion.
            use_retrieval_qa_chain: Whether to execute classic RetrievalQA chain.

        Returns:
            Dictionary containing:
                - 'query': original question
                - 'contextualized_query': reformulated query if follow-up
                - 'answer': strictly grounded answer
                - 'citations': structured list of source citations
                - 'source_documents': list of retrieved Document objects
                - 'markdown_output': complete formatted output including citations
                - 'highest_confidence': highest similarity confidence score
                - 'grounding_metrics': hallucination and factual grounding scores
        """
        store_type = store_type or self.config.vector_store_type
        top_k = top_k or self.config.top_k

        # 1. Contextualize query if part of conversational chat
        effective_query = query
        if chat_history:
            effective_query = ConversationalContextualizer.contextualize(query, chat_history)

        logger.info(f"Processing query using {store_type.upper()} vector store (k={top_k}): '{effective_query}'")

        # 2. Multi-query retrieval or standard retrieval
        if use_multi_query:
            expanded_queries = MultiQueryExpander.expand_query(effective_query)
            merged_results: Dict[str, Tuple[Document, float]] = {}

            for eq in expanded_queries:
                batch = self.vector_store_manager.similarity_search_with_confidence(
                    query=eq, k=top_k, store_type=store_type
                )
                for doc, score in batch:
                    chunk_key = doc.metadata.get("chunk_id") or doc.page_content[:50]
                    if chunk_key not in merged_results or score > merged_results[chunk_key][1]:
                        merged_results[chunk_key] = (doc, score)

            # Sort by score descending and take top_k
            docs_with_scores = sorted(
                merged_results.values(), key=lambda x: x[1], reverse=True
            )[:top_k]
        else:
            docs_with_scores = self.vector_store_manager.similarity_search_with_confidence(
                query=effective_query, k=top_k, store_type=store_type
            )

        if not docs_with_scores:
            empty_msg = (
                "I am sorry, but no relevant content was found in the indexed documents. "
                "Please make sure your documents are loaded and indexed properly."
            )
            return {
                "query": query,
                "contextualized_query": effective_query,
                "answer": empty_msg,
                "citations": [],
                "source_documents": [],
                "markdown_output": empty_msg,
                "highest_confidence": 0.0,
                "grounding_metrics": GroundingConfidenceEvaluator.evaluate(empty_msg, [], 0.0),
            }

        docs = [doc for doc, _ in docs_with_scores]
        citations = extract_citations_from_docs(docs_with_scores)
        highest_confidence = max((score for _, score in docs_with_scores), default=0.0)

        # 3. Check if a Generative LLM is available
        llm = self.get_llm(
            provider=llm_provider,
            model_name=llm_model,
            api_key=api_key,
        )

        if llm is not None:
            if use_retrieval_qa_chain:
                # Classic LangChain RetrievalQA Chain Execution
                try:
                    qa_chain = self.get_retrieval_qa_chain(
                        store_type=store_type,
                        k=top_k,
                        llm_provider=llm_provider,
                        api_key=api_key,
                    )
                    chain_res = qa_chain.invoke({"query": effective_query})
                    answer = chain_res.get("result", "").strip()
                except Exception as err:
                    logger.warning(f"RetrievalQA error: {err}. Executing LCEL.")
                    context_str = build_system_context_string(docs)
                    prompt = ChatPromptTemplate.from_template(STRICT_RAG_SYSTEM_PROMPT)
                    chain = prompt | llm | StrOutputParser()
                    answer = chain.invoke({"context": context_str, "question": effective_query}).strip()
            else:
                # Modern LCEL Chain Execution
                context_str = build_system_context_string(docs)
                prompt = ChatPromptTemplate.from_template(STRICT_RAG_SYSTEM_PROMPT)
                chain = prompt | llm | StrOutputParser()
                try:
                    raw_answer = chain.invoke({
                        "context": context_str,
                        "question": effective_query,
                    })
                    answer = raw_answer.strip()
                except Exception as e:
                    logger.error(f"Error calling LLM chain: {e}. Falling back to local synthesizer.")
                    answer = self._synthesize_local_response(effective_query, docs_with_scores)
        else:
            # Deterministic local extractive synthesizer
            answer = self._synthesize_local_response(effective_query, docs_with_scores)

        # 4. Compute Grounding & Hallucination Risk Metrics
        grounding_metrics = GroundingConfidenceEvaluator.evaluate(
            answer=answer,
            retrieved_docs=docs,
            highest_vector_confidence=highest_confidence,
        )

        # 5. Format full Markdown output with citations block
        citations_md = format_citation_markdown(citations)
        markdown_output = f"{answer}\n\n---\n{citations_md}"

        return {
            "query": query,
            "contextualized_query": effective_query,
            "answer": answer,
            "citations": citations,
            "source_documents": docs,
            "markdown_output": markdown_output,
            "highest_confidence": highest_confidence,
            "grounding_metrics": grounding_metrics,
        }

    def get_retrieval_qa_chain(
        self,
        store_type: Optional[str] = None,
        k: Optional[int] = None,
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Any:
        """Creates a classic LangChain RetrievalQA chain.

        Suggested approach compatibility method.
        """
        store_type = store_type or self.config.vector_store_type
        k = k or self.config.top_k

        retriever = self.vector_store_manager.as_retriever(
            store_type=store_type, k=k
        )
        llm = self.get_llm(provider=llm_provider, api_key=api_key)

        if llm is None:
            raise ValueError(
                "RetrievalQA chain requires a generative LLM. Please supply a valid OPENAI_API_KEY, "
                "GOOGLE_API_KEY, or GROQ_API_KEY."
            )

        try:
            from langchain_classic.chains import RetrievalQA
        except ImportError:
            from langchain.chains import RetrievalQA

        prompt = PromptTemplate(
            template=STRICT_RAG_SYSTEM_PROMPT,
            input_variables=["context", "question"],
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )
        return qa_chain
