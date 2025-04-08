# LangQueryGen

LangQueryGen is a modular AI-powered backend that transforms natural language questions into SQL queries using **Retrieval-Augmented Generation (RAG)** with **LangChain**, **Ollama** (local LLM like Mistral 7B), and **Flask**. The system also includes semantic validation of user input and a Node.js layer for interaction or interface.

---

## 🚀 Features

- 🔍 **Natural Language to SQL** with LangChain and a local model (via Ollama)
- 🧠 **RAG pipeline** with FAISS and HuggingFace embeddings
- ✅ **Input validation agent** for filtering sensitive questions
- 🛠️ **Modular Flask API** structure
- 🧩 **Node.js Integration** for frontend or orchestration
- 🔒 **Fully local and secure** – no external API calls

---

## 📁 Project Structure

```
flask-server/
├── app.py                 # Flask entry point
├── routes/                # API routes (Blueprint)
├── services/              # LangChain agents and logic
├── models/                # Pydantic request/response models
├── utils/                 # Auxiliary functions (e.g., query fixer)
├── venv/                  # Python virtual environment
├── package-lock.json      # Node.js dependencies
└── ...
```

---

## 🧑‍💻 How to Run (Backend)

### 1. Clone the repo and create the virtual environment

```bash
git clone https://github.com/raphael-santosz/LangQueryGen.git
cd LangQueryGen/flask-server
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

---

## 🧑‍💻 How to Run (Frontend)

```bash
cd client
npm install
npm run dev
```

---

## 📦 Requirements

- Python 3.10+
- Node.js 18+
- Ollama installed locally
- SQL Server or compatible DB
- Optional: FAISS, LangChain, HuggingFace embeddings

---

## ⚙️ Technologies

- 🐍 Flask + Pydantic
- 🧠 LangChain + Ollama + HuggingFace
- 🧮 SQLAlchemy
- 🌐 Node.js (for UI or extended API)
- 🧠 Mistral 7B / LLaMA3

---

## 🛡️ Security

The validation agent checks whether the user input relates to sensitive topics like **salary** or **payment**, returning `"Bloqueado"` if found.  
All LLM interactions are **local and secure**, ensuring full data privacy.

---

## ✨ Authors

Developed by **Raphael Augusto Santos**  and **Rafael Azzolini**
[GitHub](https://github.com/raphael-santosz)
