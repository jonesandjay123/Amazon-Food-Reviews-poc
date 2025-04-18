from flask import Blueprint, jsonify, request
from db import execute_query

# 創建藍圖
api = Blueprint('api', __name__)

@api.route("/news", methods=["GET"])
def get_news():
    """取得新聞列表，支援分頁和類別過濾"""
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    category = request.args.get("category")
    keyword = request.args.get("keyword")
    
    # 計算分頁 offset
    offset = (page - 1) * limit
    
    # 建構查詢
    sql_query = "SELECT * FROM news WHERE 1=1"
    params = []
    
    # 添加分類過濾
    if category:
        sql_query += " AND category = ?"
        params.append(category)
    
    # 添加關鍵字過濾
    if keyword:
        sql_query += " AND (title LIKE ? OR text LIKE ?)"
        keyword_param = f"%{keyword}%"
        params.append(keyword_param)
        params.append(keyword_param)
    
    # 計算總記錄數
    count_query = sql_query.replace("SELECT *", "SELECT COUNT(*) as count")
    count_result = execute_query(count_query, tuple(params) if params else None)
    total_count = count_result[0]["count"] if count_result else 0
    
    # 添加分頁限制
    sql_query += " LIMIT ? OFFSET ?"
    params.append(limit)
    params.append(offset)
    
    # 執行查詢
    results = execute_query(sql_query, tuple(params) if params else None)
    
    # 計算總頁數
    total_pages = (total_count + limit - 1) // limit
    
    return jsonify({
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_count": total_count,
        "data": results
    })

@api.route("/news/<int:news_id>", methods=["GET"])
def get_news_detail(news_id):
    """根據 ID 取得新聞詳情"""
    result = execute_query("SELECT * FROM news WHERE id = ?", (news_id,))
    
    if result:
        return jsonify(result[0])
    else:
        return jsonify({"error": "找不到指定的新聞"}), 404

@api.route("/search", methods=["GET"])
def search_news():
    """搜尋新聞（基本文字搜尋）"""
    q = request.args.get("q")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    
    if not q:
        return jsonify({"error": "搜尋關鍵字不能為空"}), 400
    
    offset = (page - 1) * limit
    
    # 建構查詢（標題和內文中搜尋）
    sql_query = "SELECT * FROM news WHERE title LIKE ? OR text LIKE ?"
    params = (f"%{q}%", f"%{q}%")
    
    # 計算總記錄數
    count_query = sql_query.replace("SELECT *", "SELECT COUNT(*) as count")
    count_result = execute_query(count_query, params)
    total_count = count_result[0]["count"] if count_result else 0
    
    # 添加分頁限制
    sql_query += " LIMIT ? OFFSET ?"
    params = params + (limit, offset)
    
    # 執行查詢
    results = execute_query(sql_query, params)
    
    # 計算總頁數
    total_pages = (total_count + limit - 1) // limit
    
    return jsonify({
        "query": q,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_count": total_count,
        "data": results
    })

@api.route("/query", methods=["POST"])
def query_news():
    """自然語言查詢新聞（使用 Gemini API）"""
    data = request.get_json()
    
    if not data or "query" not in data:
        return jsonify({"error": "查詢不能為空"}), 400
    
    user_query = data["query"]
    
    # 這裡可以連接 Gemini API 解析查詢
    # 簡化版，直接解析常見的類別和關鍵字
    
    # 簡單解析邏輯
    parsed_data = parse_natural_language_query(user_query)
    
    # 建構查詢
    sql_query = "SELECT * FROM news WHERE 1=1"
    params = []
    
    if parsed_data.get("category"):
        sql_query += " AND category = ?"
        params.append(parsed_data["category"])
    
    if parsed_data.get("keyword"):
        sql_query += " AND (title LIKE ? OR text LIKE ?)"
        keyword_param = f"%{parsed_data['keyword']}%"
        params.append(keyword_param)
        params.append(keyword_param)
    
    # 添加限制
    sql_query += " LIMIT 10"
    
    # 執行查詢
    results = execute_query(sql_query, tuple(params) if params else None)
    
    return jsonify({
        "query": user_query,
        "parsed": parsed_data,
        "results": results
    })

@api.route("/system_status", methods=["GET"])
def system_status():
    """取得系統狀態"""
    from db import check_database
    
    db_status = check_database()
    
    return jsonify({
        "status": "ok" if db_status else "error",
        "database": "connected" if db_status else "error",
        "timestamp": request.environ.get('REQUEST_TIME', 0)
    })

@api.route("/debug", methods=["GET"])
def debug():
    """除錯資訊"""
    from db import cache
    
    return jsonify({
        "cache_size": len(cache["query_cache"]),
        "last_load_time": cache["last_load_time"],
        "timestamp": request.environ.get('REQUEST_TIME', 0)
    })

def parse_natural_language_query(query):
    """解析自然語言查詢，提取類別和關鍵字"""
    result = {"keyword": None, "category": None}
    
    # 轉小寫進行比對
    query_lower = query.lower()
    
    # 檢查類別 (5 個類別：business、entertainment、politics、sport、tech)
    categories = ["business", "entertainment", "politics", "sport", "tech"]
    for category in categories:
        if category in query_lower:
            result["category"] = category
            break
    
    # 提取關鍵字 (簡化版)
    # 可以根據常見的關鍵詞模式提取
    keywords = ["about", "related to", "concerning", "on"]
    for keyword in keywords:
        if keyword in query_lower:
            parts = query_lower.split(keyword, 1)
            if len(parts) > 1 and parts[1].strip():
                # 取最後一個關鍵詞後的文字作為搜尋詞
                result["keyword"] = parts[1].strip()
                # 移除任何尾隨標點符號
                result["keyword"] = result["keyword"].rstrip(".,;:?!")
                break
    
    # 如果上述方法未找到關鍵字，使用一些啟發式規則
    if not result["keyword"]:
        # 排除類別詞和常見動詞後，取最長的詞作為關鍵字
        exclude_words = categories + ["list", "show", "find", "get", "latest", "news"]
        words = [w for w in query_lower.split() if w not in exclude_words and len(w) > 3]
        if words:
            result["keyword"] = max(words, key=len)
    
    return result 