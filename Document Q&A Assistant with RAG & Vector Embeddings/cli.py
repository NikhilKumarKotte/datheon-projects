import sys
import os
from typing import Optional, List, Dict, Any

# Enable UTF-8 for Windows command prompt and PowerShell
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from src.config import default_config, SAMPLE_DOCS_DIR
from src.document_loader import DocumentLoaderService
from src.text_splitter import TextChunkerService
from src.vector_store import VectorStoreManager
from src.rag_pipeline import RAGPipeline
from src.advanced_rag import DocumentIntelligenceService

console = Console(highlight=False)


def display_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║       📄 Document Q&A Assistant with RAG & Citations          ║
    ║   Powered by LangChain • ChromaDB • FAISS • Embeddings        ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(f"[bold cyan]{banner}[/bold cyan]")


def handle_ingest(path_str: str, store_type: str, chunk_size: int, chunk_overlap: int):
    """Ingests a document or folder into the vector store."""
    target_path = Path(path_str).resolve()
    console.print(f"\n[bold yellow]🔍 Ingesting from:[/bold yellow] [green]{target_path}[/green]")

    if target_path.is_file():
        docs = DocumentLoaderService.load_file(target_path)
    elif target_path.is_dir():
        docs = DocumentLoaderService.load_directory(target_path)
    else:
        console.print(f"[bold red]❌ Error: Path does not exist: {target_path}[/bold red]")
        sys.exit(1)

    console.print(f"[bold green]✓ Loaded {len(docs)} document pages/sections.[/bold green]")

    chunker = TextChunkerService(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunker.split_documents(docs)
    stats = chunker.get_chunk_statistics(chunks)

    console.print(
        f"[bold green]✓ Generated {stats['total_chunks']} chunks[/bold green] "
        f"(avg: {stats['avg_chars']} chars, range: {stats['min_chars']}-{stats['max_chars']})"
    )

    manager = VectorStoreManager()
    manager.create_or_add_documents(chunks, store_type=store_type)
    console.print(
        f"[bold green]🎉 Successfully indexed and persisted to {store_type.upper()} store![/bold green]\n"
    )


def handle_ask(question: str, store_type: str, top_k: int):
    """Answers a single user query."""
    manager = VectorStoreManager()
    stats = manager.get_stats(store_type=store_type)
    if not stats["is_indexed"]:
        console.print(
            f"[bold red]❌ The {store_type.upper()} vector store is empty! "
            f"Please run 'ingest' first.[/bold red]"
        )
        return

    pipeline = RAGPipeline(vector_store_manager=manager)
    console.print(f"\n[bold yellow]❓ Question:[/bold yellow] {question}")

    with console.status("[bold blue]🔎 Retrieving context and synthesizing answer...[/bold blue]"):
        result = pipeline.answer_question(query=question, store_type=store_type, top_k=top_k)

    # Display Answer
    console.print(
        Panel(
            result["answer"],
            title="[bold green]💡 Grounded Answer[/bold green]",
            border_style="green",
        )
    )

    # Display Grounding Metrics
    g_metrics = result.get("grounding_metrics")
    if g_metrics:
        console.print(
            f"[bold]🛡️ Grounding Score:[/bold] [green]{g_metrics['grounding_score']}%[/green]  |  "
            f"[bold]Hallucination Risk:[/bold] [{g_metrics['risk_color']}]{g_metrics['hallucination_risk']}[/{g_metrics['risk_color']}]  |  "
            f"[bold]Lexical Match:[/bold] {g_metrics['overlap_ratio']}%"
        )
        console.print()

    # Display Citations Table
    if result["citations"]:
        table = Table(title="📚 Verified Source Citations", border_style="cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Document", style="bold cyan")
        table.add_column("Page", justify="center", style="yellow")
        table.add_column("Confidence", justify="center", style="green")
        table.add_column("Excerpt Snippet", style="white")

        for idx, cite in enumerate(result["citations"], 1):
            snippet = cite["excerpt"].replace("\n", " ")
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            table.add_row(
                str(idx),
                cite["file_name"],
                str(cite["page"]),
                f"{cite['confidence']*100:.1f}%",
                snippet,
            )

        console.print(table)
    else:
        console.print("[dim]No sources cited.[/dim]")


def handle_interactive_chat(store_type: str, top_k: int):
    """Runs an interactive conversational REPL loop with memory."""
    display_banner()
    manager = VectorStoreManager()
    stats = manager.get_stats(store_type=store_type)
    if not stats["is_indexed"]:
        console.print(
            f"[yellow]⚠️ Notice: {store_type.upper()} index appears empty. "
            f"Checking for sample documents in sample_docs/...[/yellow]"
        )
        if SAMPLE_DOCS_DIR.exists():
            console.print("[cyan]Auto-ingesting sample documents for instant demo...[/cyan]")
            handle_ingest(str(SAMPLE_DOCS_DIR), store_type, 600, 100)

    pipeline = RAGPipeline(vector_store_manager=manager)
    chat_history = []

    console.print(
        f"\n[bold cyan]💬 Entering Interactive Q&A Mode ({store_type.upper()}).[/bold cyan]\n"
        "[dim]Type your question and press Enter. Type 'exit' or 'quit' to leave.[/dim]\n"
    )

    while True:
        try:
            question = console.input("[bold yellow]Ask a question > [/bold yellow]").strip()
            if not question:
                continue
            if question.lower() in {"exit", "quit", "q"}:
                console.print("[bold green]Goodbye! Have a great day.[/bold green]")
                break

            result = pipeline.answer_question(
                query=question,
                store_type=store_type,
                top_k=top_k,
                chat_history=chat_history,
            )

            # Record turn
            chat_history.append({"role": "user", "content": question})
            chat_history.append({"role": "assistant", "content": result["answer"]})

            console.print(
                Panel(
                    result["answer"],
                    title="[bold green]💡 Grounded Answer[/bold green]",
                    border_style="green",
                )
            )

            # Print brief citation list
            if result["citations"]:
                console.print("[bold cyan]Source Citations:[/bold cyan]")
                for idx, c in enumerate(result["citations"], 1):
                    console.print(
                        f"  [{idx}] [bold]{c['file_name']}[/bold] (Page {c['page']}) — "
                        f"[green]{c['confidence']*100:.1f}% confidence[/green]"
                    )
            console.print()

        except KeyboardInterrupt:
            console.print("\n[bold green]Session ended. Goodbye![/bold green]")
            break


def handle_summarize(path_str: Optional[str] = None):
    """Generates an executive document intelligence summary."""
    target_path = Path(path_str).resolve() if path_str else SAMPLE_DOCS_DIR
    if target_path.is_file():
        docs = DocumentLoaderService.load_file(target_path)
    elif target_path.is_dir():
        docs = DocumentLoaderService.load_directory(target_path)
    else:
        console.print(f"[bold red]❌ Error: Path does not exist: {target_path}[/bold red]")
        return

    summary = DocumentIntelligenceService.generate_executive_summary(docs)
    console.print(f"\n[bold cyan]⚡ {summary['title']}[/bold cyan]")
    console.print(f"[dim]Total Pages: {summary['total_pages']} | Words: {summary['total_words']:,}[/dim]\n")

    if summary["topics"]:
        console.print("[bold yellow]📌 Key Document Sections:[/bold yellow]")
        for t in summary["topics"]:
            console.print(f"  • {t}")
        console.print()

    if summary["financial_figures"]:
        console.print("[bold green]💰 Financial Stipends & Allowances Detected:[/bold green]")
        for f in summary["financial_figures"]:
            console.print(f"  • {f}")
        console.print()

    if summary["time_periods"]:
        console.print("[bold blue]⏳ Key Durations & Schedules:[/bold blue]")
        for p in summary["time_periods"]:
            console.print(f"  • {p}")
        console.print()


def handle_stats():
    """Prints vector store status and vector counts."""
    manager = VectorStoreManager()
    table = Table(title="📊 Vector Store Status Diagnostics", border_style="blue")
    table.add_column("Store Type", style="bold cyan")
    table.add_column("Indexed", justify="center")
    table.add_column("Vector Count", justify="center", style="green")
    table.add_column("Storage Path", style="dim")

    for stype in ["chroma", "faiss"]:
        st = manager.get_stats(store_type=stype)
        status_icon = "✅ Yes" if st["is_indexed"] else "❌ No"
        table.add_row(stype.upper(), status_icon, str(st["vector_count"]), st["path"])

    console.print(table)


def handle_reset(store_type: str):
    """Resets the chosen vector store."""
    manager = VectorStoreManager()
    if store_type == "all":
        manager.clear_store("chroma")
        manager.clear_store("faiss")
        console.print("[bold green]✓ Successfully cleared both ChromaDB and FAISS stores.[/bold green]")
    else:
        manager.clear_store(store_type)
        console.print(f"[bold green]✓ Successfully cleared {store_type.upper()} store.[/bold green]")


def main():
    parser = argparse.ArgumentParser(
        description="Document Q&A Assistant CLI (RAG & Vector Embeddings)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents or folder into vector store")
    ingest_parser.add_argument("path", type=str, help="Path to PDF/TXT file or directory")
    ingest_parser.add_argument(
        "--store", choices=["chroma", "faiss"], default="chroma", help="Vector store type (default: chroma)"
    )
    ingest_parser.add_argument("--chunk-size", type=int, default=600, help="Chunk size in characters")
    ingest_parser.add_argument("--chunk-overlap", type=int, default=100, help="Chunk overlap in characters")

    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a single question against the indexed documents")
    ask_parser.add_argument("question", type=str, help="The question to ask")
    ask_parser.add_argument(
        "--store", choices=["chroma", "faiss"], default="chroma", help="Vector store type"
    )
    ask_parser.add_argument("--top-k", type=int, default=4, help="Number of context chunks to retrieve")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start an interactive chat session")
    chat_parser.add_argument(
        "--store", choices=["chroma", "faiss"], default="chroma", help="Vector store type"
    )
    chat_parser.add_argument("--top-k", type=int, default=4, help="Top-K context chunks")

    # Summarize command
    sum_parser = subparsers.add_parser("summarize", help="Generate document intelligence executive summary")
    sum_parser.add_argument("path", nargs="?", default=None, help="Optional document or folder path")

    # Stats command
    subparsers.add_parser("stats", help="Display vector store diagnostics")

    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Clear vector store index")
    reset_parser.add_argument(
        "--store", choices=["chroma", "faiss", "all"], default="chroma", help="Store to reset"
    )

    args = parser.parse_args()

    if args.command == "ingest":
        handle_ingest(args.path, args.store, args.chunk_size, args.chunk_overlap)
    elif args.command == "ask":
        handle_ask(args.question, args.store, args.top_k)
    elif args.command == "chat":
        handle_interactive_chat(args.store, args.top_k)
    elif args.command == "summarize":
        handle_summarize(args.path)
    elif args.command == "stats":
        handle_stats()
    elif args.command == "reset":
        handle_reset(args.store)
    else:
        display_banner()
        parser.print_help()


if __name__ == "__main__":
    main()
