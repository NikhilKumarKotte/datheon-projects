# 🚀 Beginner's Quickstart Guide — Multi-Tool Autonomous AI Agent

Welcome to the **Multi-Tool Autonomous AI Agent**! This guide is designed for new users and evaluators to understand the ReAct reasoning loop, run the agent locally via Web UI or Terminal CLI, and deploy it to the cloud.

---

## 📌 What Does This Project Do?

This system implements an **autonomous AI agent** based on the industry-standard **ReAct (Reasoning + Acting)** framework:
$$\text{Thought} \longrightarrow \text{Action} \longrightarrow \text{Observation} \longrightarrow \text{Final Answer}$$

Unlike a simple chatbot that merely predicts the next token, this agent:
1. **Decomposes complex, multi-part research questions** into logical sub-tasks.
2. **Autonomously selects and calls external tools**:
   - 🌐 **Real-Time Web Search**: Queries DuckDuckGo / Tavily to retrieve current live information.
   - 🧮 **Python Math Calculator**: Safely evaluates arithmetic, percentages, growth rates, and scientific formulas via AST/SymPy.
   - 📁 **Sandboxed File Reader**: Safely inspects local files (reports, JSON, text) inside a secure directory boundary (`sample_data/`).
3. **Observes intermediate outputs**, self-corrects if needed, and synthesizes a structured final report with transparent step-by-step reasoning.

---

## 📋 Prerequisites

Before getting started:
- **Python 3.10 to 3.13** installed. Verify: `python --version`
- **Git** installed.
- A **Google Gemini API Key** (get one free at [Google AI Studio](https://aistudio.google.com/)).

---

## 🛠️ Step-by-Step Local Setup

### Step 1: Open Your Terminal
Navigate to this project's directory:
```bash
# From the repository root:
cd "Multi-Tool Autonomous AI Agent"
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
Copy the example template to create your `.env` file:
```bash
# On Windows:
copy .env.example .env

# On macOS / Linux:
cp .env.example .env
```
Open `.env` and set your Gemini API key:
```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

---

## 🖥️ How to Run the Agent

You can interact with the autonomous agent through two interfaces:

### Option 1: Streamlit Web Dashboard (Recommended)
Launch the interactive web UI:
```bash
streamlit run web_app.py
```
Open your browser at:
```
http://localhost:8501
```

#### Highlights of the Web UI:
- **Interactive Query Input**: Type any compound research query, or click one of the pre-set test scenarios (e.g. *"Analyze Tokyo Branch revenue in sample_data/q3_report.txt and calculate its percentage"*).
- **Live Tool Trace**: Watch the agent think, pick tools, and display observations in real-time.
- **Evaluation Rubric Inspector**: View the system's architecture breakdown across functionality, reasoning, and security.
- **Export**: Download findings as formatted Markdown or text.

---

### Option 2: Rich Terminal CLI
If you want to run queries from your command line:
```bash
# 1. Run a single query directly:
python -m agent.cli.console -q "What was Acme Corp's Tokyo branch revenue in sample_data/q3_report.txt and what percentage of total revenue was it?"

# 2. Start an interactive REPL session:
python -m agent.cli.console
```

---

## 🧪 How to Run Automated Tests

Run the complete pytest test suite:
```bash
pytest -v
```
All **19 tests** cover tool sandboxing, path safety, AST calculator correctness, error recovery, and the full agent executor loop.

---

## ☁️ How to Deploy to Streamlit Community Cloud (Free)

1. Push your repository to **GitHub**.
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and log in with GitHub.
3. Click **"Create app"**.
4. Configure the deployment settings:
   - **Repository**: Your GitHub repository
   - **Branch**: `main`
   - **Main file path**: `Multi-Tool Autonomous AI Agent/web_app.py`
5. In **"Advanced settings..."** -> **Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key_here"
   ```
6. Click **Deploy!**. The cloud container will spin up and provide your public web application link.

---

## 🐳 Optional: Run with Docker

```bash
# Build the Docker image
docker build -t datheon-agent:1.0 .

# Run the Streamlit Web Interface
docker run -it --rm -p 8501:8501 --env-file .env datheon-agent:1.0 --web
```

---

## ❓ Troubleshooting & FAQs

- **Q: What is the sandbox security error?**
  *The agent is deliberately constrained by security policies to only access files located within `sample_data/`. Attempting to read `C:\Windows` or system directories triggers an automatic security block.*
- **Q: Web search is returning empty or rate-limited?**
  *DuckDuckGo has built-in fallback mechanisms. If needed, you can optionally configure `TAVILY_API_KEY` in `.env` for high-volume enterprise web search.*
