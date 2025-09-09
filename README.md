# 🛒 AI-Powered Shopping Agent

A simple **Python-based shopping assistant** that fetches products from an API and helps users filter and search items using natural language queries.  
It uses the **OpenAI API** to provide friendly, AI-generated answers along with accurate filtered results.

---

## 🚀 Features
- 📦 Fetch product data from API  
- 💰 Filter by **price** and **keyword**  
- 🧑‍💻 Natural language queries (e.g. *"Show me chairs under $200"*)  
- 🤖 Accurate product filtering + **AI-powered summary**  

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-username/Ai_Powered_Shopping_Agent.git
cd Ai_Powered_Shopping_Agent
````

### 2. Create a virtual environment (using [uv](https://docs.astral.sh/uv/))

```bash
uv venv .venv
uv pip install -r requirements.txt
```

### 3. Add your OpenAI API key

Create a `.env` file in the project root:

```ini
OPENAI_API_KEY=sk-xxxxxx
```

### 4. Run the agent

```bash
uv run python main.py
```

---

## 📝 Example Queries

* `Show me products under $300`
* `Find me a chair`
* `Suggest a lamp below $200`

---

## 📌 Notes

* Make sure your `.env` file is **not committed** to GitHub.
* For reference, an `.env.example` file is included.

```