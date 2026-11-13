# 🚀 Beginner's Quickstart Guide — Structured LLM Prompt Pipeline & JSON Extractor

Welcome to the **Structured LLM Extractor**! This guide is written for new users and developers to help you understand the architecture, run the FastAPI backend & interactive Web UI, execute extractions, and deploy to the cloud.

---

## 📌 What Does This Project Do?

This application solves a critical enterprise challenge: **converting messy, unstructured documents into strictly typed, guaranteed-valid JSON**.

Key capabilities:
1. **Universal Document Ingestion**: Upload **PDF invoices**, **Word (.docx) resumes**, **scanned receipt images (PNG, JPG)**, or raw text.
2. **Autonomous Classifier**: Auto-detects whether the document is an Invoice, Receipt, or Resume without manual tagging.
3. **Constrained Schema Decoding**: Uses Google Gemini's native `response_json_schema` enforced by **Pydantic v2** (`extra="forbid"`). Schema keys are guaranteed never to hallucinate.
4. **Verification Agent**: Audits the extracted data for mathematical correctness (verifies line items sum to the total, checks taxes and tips, and assigns a 0–100% confidence rating).
5. **Interactive Glassmorphism Dashboard**: Modern visual UI with drag-and-drop file upload, live JSON viewer, and card rendering.
6. **FastAPI REST API**: OpenAPI / Swagger endpoints for easy integration with backend systems.

---

## 📋 Prerequisites

Before you start:
- **Python 3.10 to 3.13** installed. Verify: `python --version`
- **Git** installed.
- A **Google Gemini API Key** (free at [Google AI Studio](https://aistudio.google.com/)).
  - *Tip: If you do not have an API key, the system has a built-in **"Demo Mode"** with instant deterministic mocked extractions for offline testing!*

---

## 🛠️ Step-by-Step Local Setup

### Step 1: Open Your Terminal
Navigate to this project's directory:
```bash
# From repository root:
cd "Structured LLM Prompt Pipeline & JSON Extractor"
```

### Step 2: Create a Virtual Environment
```bash
# On Windows:
python -m venv .venv
.venv\Scripts\activate

# On macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Your Environment (.env)
Copy the `.env.example` file:
```bash
# On Windows:
copy .env.example .env

# On macOS / Linux:
cp .env.example .env
```
Open `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

---

## 🖥️ How to Run the Application

### 1. Launch the FastAPI Server & Interactive Web UI
Run the server with Uvicorn:
```bash
uvicorn main:app --reload --port 8000
```
Then open your browser to:
- **Interactive Web Dashboard**: `http://localhost:8000/`
- **Interactive Swagger REST Docs**: `http://localhost:8000/docs`
- **Alternative ReDoc Docs**: `http://localhost:8000/redoc`

#### Using the Web Dashboard:
1. Select an Extraction Schema (`Invoice`, `Receipt`, `Resume`, or `Auto-Detect`).
2. Toggle between **"Live AI Mode"** (uses your Gemini API key) or **"Demo Mode"** (deterministic offline).
3. Drag and drop any of the included sample files (e.g. `sample_invoice.pdf`, `sample_receipt.txt`, `sample_resume.docx`).
4. Click **"Extract Structured Data"**.
5. View the parsed Visual Cards, inspect the raw JSON, and view the Verification Math Audit!

---

### 2. Using the Command Line Interface (CLI)
You can also run extractions directly in your terminal:
```bash
# Extract an invoice:
python -m src.extractor.cli extract sample_invoice.pdf --type invoice

# Auto-classify and extract a receipt:
python -m src.extractor.cli extract sample_receipt.txt --auto-classify

# Inspect supported schemas:
python -m src.extractor.cli schemas
```

---

## 🧪 How to Run Automated Tests

Run the full pytest suite (35 unit and integration tests):
```bash
pytest tests/ -v
```
All tests use deterministic mocks, executing in ~1.5s with a 100% pass rate without consuming API credits.

---

## ☁️ How to Deploy to Render (Free Cloud Web Service)

This application can be deployed as a live REST API and web dashboard on **[Render.com](https://render.com)** for free:

1. **Push to GitHub**: Push your monorepo to your GitHub account.
2. **Open Render Dashboard**: Visit [dashboard.render.com](https://dashboard.render.com) and click **"New +"** -> **"Web Service"**.
3. **Connect Repository**: Select your GitHub repository.
4. **Configure Settings**:
   - **Name**: `structured-llm-extractor`
   - **Region**: Closest to you (e.g., Oregon, Frankfurt)
   - **Branch**: `main`
   - **Root Directory**: `Structured LLM Prompt Pipeline & JSON Extractor` *(Crucial for monorepo!)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. **Environment Variables**:
   - Add variable: `GEMINI_API_KEY` = your Gemini API key
6. **Deploy**: Click **"Create Web Service"**. Render will deploy the API and give you a live `https://<service-name>.onrender.com` URL!

---

## 🐳 Optional: Run with Docker

```bash
# Build Docker image
docker build -t structured-llm-extractor .

# Run container
docker run -d -p 8000:8000 -e GEMINI_API_KEY="your_key" --name extractor structured-llm-extractor
```

---

## ❓ Troubleshooting & FAQs

- **Q: Receiving a 422 Validation Error?**
  *This occurs when a document does not match the chosen schema or has missing mandatory fields. Try using `--auto-classify` or check the Swagger documentation at `/docs`.*
- **Q: Can I run this completely offline without paying for Gemini?**
  *Yes! In the Web UI, toggle on "Demo Mode", or set `ENVIRONMENT=development` in `.env` to test mocked outputs without calling the API.*
