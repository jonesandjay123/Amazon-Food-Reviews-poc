# app.py
import os, time
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

def build_query(category: Optional[str], keyword: Optional[str],
                limit: int, offset: int) -> tuple[str, tuple]:
    sql = "SELECT * FROM news WHERE 1=1"
    params: list = []
    if category:
        sql += " AND category = ?"; params.append(category)
    if keyword:
        kw = f"%{keyword}%"
        sql += " AND text LIKE ?"
        params.append(kw)
    sql += " ORDER BY rowid DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    return sql, tuple(params)

def naive_parse(query: str) -> dict:
    cats = ["business","entertainment","politics","sport","tech"]
    q_low = query.lower()
    cat  = next((c for c in cats if c in q_low), None)
    words = [w for w in q_low.split() if w not in cats and len(w) > 4]
    kw = words[0] if words else None
    return {"category": cat, "keyword": kw}

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

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json(force=True)
    user_q = data.get("query")
    if not user_q:
        return jsonify({"error": "query field required"}), 400

    parsed = ai_model.parse(user_q) if ai_model else naive_parse(user_q)
    cat = parsed.get("category")
    kw  = parsed.get("keyword")

    # first query
    sql, p = build_query(cat, kw, 10, 0)
    rows   = execute(sql, p)

    # if no result, try again with only category
    if not rows and kw:
        sql, p = build_query(cat, None, 10, 0)
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
