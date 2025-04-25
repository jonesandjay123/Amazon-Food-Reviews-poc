# app.py  ── 支援 ❶Azure-OpenAI-RAG (預設) ❷Gemini (可選)
import os, time, re
from dotenv import load_dotenv
load_dotenv()

from rag_model import RAGModel
rag_model = RAGModel()                     # ← RAG 一律可用

from flask import Flask, render_template, request, jsonify
from db import execute, DB_PATH

# ---------- 依環境變數決定要不要載 AI-Parse ---------- #
AI_MODEL_TYPE = os.getenv("AI_MODEL_TYPE", "OPENAI").upper()
ai_model = None

if AI_MODEL_TYPE == "GEMINI":
    try:
        from gemini_model import GeminiModel      # 只有 parse 用
        ai_model = GeminiModel()
        print("✅ Gemini model loaded for SQL parse")
    except Exception as e:
        print("⚠️  Gemini init failed, fallback to naive parse:", e)
else:                             # OPENAI / CHATGPT
    try:
        from chatgpt_model import ChatGPTModel    # 只有 parse 用
        ai_model = ChatGPTModel(temperature=0.0)  # 低溫方便規則化輸出
        print("✅ ChatGPT model loaded for SQL parse")
    except Exception as e:
        print("⚠️  ChatGPT init failed, fallback to naive parse:", e)

# ---------- Flask app ---------- #
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

# --- Query Builder (SQL) ---
def build_query(keyword: str | None, limit: int, offset: int) -> tuple[str, tuple]:
    if keyword:
        sql = "SELECT * FROM news WHERE text LIKE ? ORDER BY rowid DESC LIMIT ? OFFSET ?"
        return sql, (f"%{keyword}%", limit, offset)
    sql = "SELECT * FROM news ORDER BY rowid DESC LIMIT ? OFFSET ?"
    return sql, (limit, offset)

# --- 極簡 fallback parse ---
def naive_parse(query: str) -> dict:
    words = re.findall(r"\b[a-z]{4,}\b", query.lower())
    kw = words[-1].rstrip('s') if words else None
    return {"keyword": kw}

# ---------- RAG 端點 ----------
@app.route("/rag_query", methods=["POST"])
def rag_query():
    data = request.get_json(force=True)
    user_q = data.get("query", "").strip()
    if not user_q:
        return jsonify({"error": "query field required"}), 400

    result = rag_model.ask(user_q)
    return jsonify(result)

# ---------- 傳統 SQL 端點 ----------
@app.route("/query", methods=["POST"])
def query():
    data = request.get_json(force=True)
    user_q = data.get("query", "").strip()
    if not user_q:
        return jsonify({"error": "query field required"}), 400

    # 先嘗試 AI parse（若 model 存在且有 parse 方法）
    try:
        parsed = ai_model.parse(user_q) if (ai_model and hasattr(ai_model, "parse")) else {}
    except Exception as e:
        print("⚠️  AI parse failed, fallback to naive:", e)
        parsed = {}

    if not parsed.get("keyword"):
        parsed = naive_parse(user_q)

    kw = parsed.get("keyword")
    sql, params = build_query(kw, 10, 0)
    rows = execute(sql, params)

    return jsonify({
        "query": user_q,
        "parsed": parsed,
        "results": rows
    })

@app.route("/system_status")
def status():
    return jsonify({"db_exists": DB_PATH.exists(), "time": time.time()})

if __name__ == "__main__":
    # 預設 5000；如需改 port 用環境變數或這裡直接改
    app.run(debug=True, port=5000)
