# 🚀 Beginner's Quickstart Guide — Document Q&A Assistant with RAG

Welcome to the **Document Q&A Assistant**! This guide is written specifically for new users and contributors to help you set up, understand, run, and deploy this project in just a few minutes.

---

## 📌 What Does This Project Do?

This application is a **Retrieval-Augmented Generation (RAG)** assistant. It allows you to:
1. **Upload custom documents** (PDFs, Markdown, or Text files).
2. **Break down the documents** into semantic chunks and store their embeddings in local vector databases (**ChromaDB** or **FAISS**).
3. **Ask complex questions** in natural language.
4. **Receive strictly grounded answers** backed by verified in-text citations (e.g., `[Document: handbook.pdf, Page: 2]`) and zero hallucinations.
5. **Listen to answers** using built-in Text-to-Speech (TTS) audio narration.

---

## 📋 Prerequisites

Before starting, make sure you have:
- **Python 3.10 to 3.13** installed on your system.
  - Verify by running: `python --version`
- **Git** installed.
- *(Optional)* An API key for **Google Gemini**, **OpenAI**, or **Groq** if you want to use cloud LLMs.
  - *Note: If you don't have an API key, the system runs 100% offline for free using local HuggingFace embeddings (`all-MiniLM-L6-v2`)!*

---

## 🛠️ Step-by-Step Local Setup

### Step 1: Open Your Terminal
Navigate to this project's folder:
```bash
# From the repository root:
cd "Document Q&A Assistant with RAG & Vector Embeddings"
```

### Step 2: Create a Virtual Environment (Recommended)
Creating an isolated environment keeps your system Python clean:
```bash
# On Windows:
python -m venv .venv
.venv\Scripts\activate

# On macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Packages
Install all necessary libraries (LangChain, Streamlit, ChromaDB, FAISS, PyPDF):
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the example environment template:
```bash
# On Windows:
copy .env.example .env

# On macOS / Linux:
cp .env.example .env
```
Open `.env` in any text editor and optionally add your API keys:
```env
# Optional Cloud LLM Keys:
GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```
*(If left blank, the app will automatically operate in offline extractive mode).*

---

## 🖥️ How to Run the Project

You can run this project in two convenient modes:

### Mode 1: Interactive Streamlit Web UI (Recommended)
Run the following command in your terminal:
```bash
streamlit run app.py
```
Or, if you are on Windows, simply double-click **`run_app.bat`**!

Your browser will automatically open at:
```
http://localhost:8501
```

#### What you can do in the Web UI:
- **Sidebar**: Select your Vector Store (**ChromaDB** or **FAISS**) and LLM Provider.
- **Upload Section**: Drag and drop any PDF/TXT/MD document. Click **"Ingest & Index Documents"**.
- **Chat Interface**: Type questions in the chat box or click one of the pre-built sample question chips.
- **Citations Drawer**: Expand to see exact source documents, page numbers, and similarity confidence scores.
- **Audio TTS**: Click `🔊 Read Answer Aloud` to hear the answer.
- **Export**: Click `📥 Export Session (Markdown)` to save your Q&A transcript.

---

### Mode 2: Interactive Terminal CLI
If you prefer working from the command line:
```bash
# 1. Ingest sample documents into ChromaDB:
python cli.py ingest sample_docs/ --store chroma

# 2. Ask a single question directly:
python cli.py ask "What is the flexible remote work policy?" --store chroma

# 3. Launch an interactive multi-turn terminal chat REPL:
python cli.py chat --store chroma

# 4. View vector database statistics:
python cli.py stats
```
Or double-click **`run_cli.bat`** on Windows!

---

## 🧪 How to Run Automated Tests

To verify that all components (PDF loader, chunker, vector database, RAG pipeline) are working perfectly:
```bash
python -m pytest tests/ -v
```
All 16 tests should pass with 100% green output.

---

## ☁️ How to Deploy to Streamlit Community Cloud (Free)

1. Push your repository to **GitHub**.
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and log in with your GitHub account.
3. Click **"Create app"**.
4. Configure your repository settings:
   - **Repository**: Your GitHub repository
   - **Branch**: `main`
   - **Main file path**: `Document Q&A Assistant with RAG & Vector Embeddings/app.py`
5. Click **"Advanced settings..."** -> **Secrets** and paste any API keys:
   ```toml
   GOOGLE_API_KEY = "your-api-key"
   ```
6. Click **Deploy!** Your app will be live with a permanent public link in ~2 minutes.

---

## ❓ Troubleshooting & FAQs

- **Q: PyPDF or ChromaDB gives an error on Windows?**
  *Make sure you are using Python 3.10 - 3.13 and have installed all requirements from `requirements.txt` inside your virtual environment.*
- **Q: Do I need to pay for OpenAI or Gemini?**
  *No! The project includes a full offline mode powered by HuggingFace embeddings and local document synthesis that runs 100% free with no internet connection required.*
- **Q: Port 8501 is already in use?**
  *Run `streamlit run app.py --server.port 8502` to use an alternate port.*
