# app.py
import os, time, re
from typing import Optional
from flask import Flask, render_template, request, jsonify
from db import execute, DB_PATH

# --- Gemini (optional) -------------------------------------------------
ai_model = None
if os.getenv("AI_MODEL_TYPE", "GEMINI").upper() == "GEMINI":
    try:
        from gemini_model import GeminiModel
        ai_model = GeminiModel()
        print("Gemini model loaded")
    except Exception as e:
        print("⚠️ Gemini init failed, fallback to naive parse:", e)

# --- Flask app ---------------------------------------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

# --- Query Builder ---
def build_query(keyword: str | None, limit: int, offset: int) -> tuple[str, tuple]:
    if keyword:
        sql = "SELECT * FROM news WHERE text LIKE ? ORDER BY rowid DESC LIMIT ? OFFSET ?"
        return sql, (f"%{keyword}%", limit, offset)
    # if not keyword, return all news
    sql = "SELECT * FROM news ORDER BY rowid DESC LIMIT ? OFFSET ?"
    return sql, (limit, offset)

# --- fallback parse ---
def naive_parse(query: str) -> dict:
    q_low = query.lower()
    words = re.findall(r"\b[a-z]{4,}\b", q_low)
    kw = words[-1].rstrip('s') if words else None
    return {"keyword": kw}

@app.route("/news")
def news():
    page     = int(request.args.get("page", 1))
    limit    = int(request.args.get("limit", 20))
    category = request.args.get("category")
    keyword  = request.args.get("keyword")
    offset   = (page - 1) * limit

    sql, p = build_query(category, keyword, limit, offset)
    rows   = execute(sql, p)

    count_sql, cp = build_query(category, keyword, 1, 0)
    total  = execute(count_sql.replace("SELECT *", "SELECT COUNT(*) AS c"), cp)[0]["c"]

    return jsonify({"page": page, "limit": limit,
                    "total_pages": (total+limit-1)//limit,
                    "total": total, "data": rows})

@app.route("/search")
def search():
    q = request.args.get("q")
    if not q: return jsonify({"error":"q param required"}), 400
    return news()

# --- /query endpoint ---
@app.route("/query", methods=["POST"])
def query():
    data = request.get_json(force=True)
    user_q = data.get("query", "").strip()
    if not user_q:
        return jsonify({"error": "query field required"}), 400

    parsed = ai_model.parse(user_q) if ai_model else {}
    if not parsed.get("keyword"):
        parsed = naive_parse(user_q)

    kw = parsed.get("keyword")

    sql, p = build_query(kw, 10, 0)
    rows   = execute(sql, p)

    return jsonify({
        "query": user_q,
        "parsed": parsed,
        "results": rows
    })

@app.route("/system_status")
def status():
    return jsonify({"db_exists": DB_PATH.exists(), "time": time.time()})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
