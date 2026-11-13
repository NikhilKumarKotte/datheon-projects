# 🚀 Beginner's Quickstart Guide — OmniStream AI Chatbot

Welcome to **OmniStream AI**! This guide is written for new users and developers to help you understand, set up, run, and deploy this full-stack AI chatbot quickly and easily.

---

## 📌 What Does This Project Do?

**OmniStream AI** is a production-ready conversational chatbot with advanced capabilities:
1. **Real-time Token Streaming**: Word-by-word streaming responses just like ChatGPT or Claude.
2. **Autonomous Tool Routing**: Can execute **Live Web Search** (via DuckDuckGo), compute math with a sandboxed **Python Calculator**, and retrieve knowledge from uploaded files via **Vector RAG**.
3. **Chain-of-Thought (CoT)**: Displays an expandable `🧠 Agent Reasoning` box showing what the AI is thinking and which tools it chose.
4. **Multi-Session Memory & Cloud Database**: Keeps track of your conversation threads. Automatically uses local SQLite (`data/chat_history.db`) or connects to cloud PostgreSQL (Supabase / Neon).
5. **Dynamic Theme Engine**: Switch between 5 styles in real-time (Midnight Slate, Nordic Frost, Cyberpunk Neon, Emerald Obsidian, Sunset Amber).
6. **Delight Features**: Text-to-speech audio narration (`🔊`), copy message to clipboard, and feedback ratings (`👍`/`👎`).

---

## 📋 Prerequisites

Before you start:
- **Python 3.10 to 3.13** installed. Check with: `python --version`
- **Git** installed.
- *(Recommended)* A **Google Gemini API Key** (free from [Google AI Studio](https://aistudio.google.com/)) or an OpenAI / Groq API key.
  - *Tip: If you don't have an API key right now, you can select the built-in **"Demo Mode"** in the sidebar to test all UI features instantly!*

---

## 🛠️ Step-by-Step Local Setup

### Step 1: Open Your Terminal
Navigate to this project directory:
```bash
# From the repository root:
cd "Interactive Full-Stack AI Chatbot with Streamlit"
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

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the `.env.example` file to `.env`:
```bash
# On Windows:
copy .env.example .env

# On macOS / Linux:
cp .env.example .env
```
Open `.env` in any code or text editor and insert your API key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
# Optional:
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```
*(You can also paste your API key directly into the app sidebar at runtime!)*

---

## 🖥️ How to Run the Application

Launch the Streamlit web app:
```bash
streamlit run app.py
```
Your browser will open automatically at:
```
http://localhost:8501
```

### Exploring the Chatbot:
1. **Choose Model**: In the sidebar, pick **Google Gemini**, **OpenAI**, **Groq**, or **Demo Mode**.
2. **Switch Themes**: Test out different color themes from the Theme dropdown.
3. **Use Autonomous Tools**:
   - Ask for live news: *"What are the latest updates on space exploration?"* (Triggers DuckDuckGo web search).
   - Ask for calculations: *"What is the compound interest on $15,000 at 7.5% over 10 years?"* (Triggers Python math engine).
   - Ingest documents: Upload a PDF/TXT in the sidebar and ask questions about it!
4. **Manage Chats**: Start new chats, rename them, or switch between conversation threads in the sidebar.

---

## 🧪 How to Run Automated Tests

To test the database persistence, RAG indexing, agent tool routing, and reasoning traces:
```bash
python -m unittest tests/test_components.py
```
All component unit tests will execute and confirm system integrity.

---

## ☁️ How to Deploy to Streamlit Community Cloud (Free)

1. Ensure this project is pushed to your **GitHub** repository.
2. Navigate to **[share.streamlit.io](https://share.streamlit.io)** and log in with GitHub.
3. Click **"Create app"**.
4. Set the following settings:
   - **Repository**: Your GitHub repository
   - **Branch**: `main`
   - **Main file path**: `Interactive Full-Stack AI Chatbot with Streamlit/app.py`
5. Click **"Advanced settings..."** -> **Secrets** and add:
   ```toml
   GOOGLE_API_KEY = "your_google_api_key"
   ```
6. Click **Deploy!**. Streamlit Cloud will build and launch your chatbot with a shareable public URL.

---

## 🐳 Optional: Run with Docker

If you prefer Docker:
```bash
# Build the Docker image
docker build -t omnistream-ai .

# Run the container
docker run -d -p 8501:8501 --env-file .env --name omnistream-ai omnistream-ai
```
Visit `http://localhost:8501`.

---

## ❓ Troubleshooting & FAQs

- **Q: How does chat memory persist?**
  *By default, messages are saved in a local SQLite database at `data/chat_history.db`. If you configure `DATABASE_URL` in `.env`, it automatically uses your remote PostgreSQL database.*
- **Q: Getting rate limited?**
  *Switch to a different provider in the sidebar (e.g. Gemini 1.5 Flash or Groq) or select Demo Mode for zero-quota testing.*
- **Q: How to reset conversation history?**
  *Click the trash icon in the sidebar to delete individual threads, or delete the `data/chat_history.db` file to wipe all local history.*
