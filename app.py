import os
import json
import time
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from google import genai  # 新版 SDK 匯入方式
from google.genai import types  # 用於傳入 GenerateContentConfig
from flasgger import Swagger, swag_from

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# 設定 Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,  # 所有端點
            "model_filter": lambda tag: True,  # 所有模型
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs/"
}

swagger_template = {
    "info": {
        "title": "Amazon Fine Food Reviews API",
        "description": "使用Amazon Fine Food Reviews數據實現的RESTful API，支持各種食品評論查詢功能",
        "version": "1.0.0",
        "contact": {
            "name": "API 支持",
            "email": "support@example.com"
        }
    },
    "tags": [
        {
            "name": "評論列表",
            "description": "獲取評論列表和詳細信息"
        },
        {
            "name": "產品和用戶",
            "description": "獲取特定產品或用戶的評論"
        },
        {
            "name": "搜索",
            "description": "搜索評論和自然語言查詢"
        },
        {
            "name": "系統",
            "description": "調試和系統信息"
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# 設定 Gemini API 憑證
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 建立 Google GenAI 的 API 客戶端
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.0-flash"

# 設定資料庫路徑
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "database.sqlite")

# 確保資料目錄存在
os.makedirs(DATA_DIR, exist_ok=True)

# 查詢結果緩存
cache = {
    "query_cache": {},  # 查詢結果緩存
    "last_load_time": 0  # 上次加載數據的時間戳
}

# 連接到 SQLite 資料庫
def get_db_connection():
    """創建並返回一個SQLite資料庫連接"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"找不到資料庫文件: {DB_PATH}。請先運行download_data.sh下載數據。")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 讓結果以字典形式返回
    return conn

def execute_query(query, params=None, cache_key=None):
    """執行SQLite查詢，支持緩存結果"""
    # 如果提供了緩存鍵且查詢結果已緩存，則直接返回緩存結果
    if cache_key and cache_key in cache["query_cache"]:
        print(f"使用緩存結果: {cache_key}")
        return cache["query_cache"][cache_key]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # 緩存結果（如果提供了緩存鍵）
        if cache_key:
            cache["query_cache"][cache_key] = results
            
        return results
    except Exception as e:
        print(f"執行查詢時出錯: {e}")
        if conn:
            conn.close()
        raise e

def check_database():
    """檢查資料庫結構並顯示基本信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 獲取資料表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("資料庫表結構:")
        for table in tables:
            table_name = table['name']
            print(f"- {table_name}")
            
            # 獲取表中的列信息
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col['name']} ({col['type']})")
                
            # 獲取記錄數
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
            count = cursor.fetchone()['count']
            print(f"  - 記錄數: {count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"檢查資料庫時出錯: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

@app.route("/", methods=["GET"])
def index():
    """提供聊天界面的 HTML 頁面"""
    return render_template("index.html")

@app.route("/api", methods=["GET"])
def api_home():
    """提供 API 文檔和測試界面的入口頁面"""
    return render_template("api.html")

@app.route("/api/reviews", methods=["GET"])
@swag_from({
    "tags": ["評論列表"],
    "summary": "獲取評論列表",
    "description": "獲取Amazon Fine Food評論列表，支持多種過濾條件",
    "parameters": [
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "default": 1,
            "description": "頁碼"
        },
        {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "default": 20,
            "description": "每頁結果數量"
        },
        {
            "name": "min_score",
            "in": "query",
            "type": "integer",
            "description": "最低評分 (1-5)"
        },
        {
            "name": "max_score",
            "in": "query",
            "type": "integer",
            "description": "最高評分 (1-5)"
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取評論列表"
        }
    }
})
def get_reviews():
    """獲取評論列表，支持分頁和評分過濾"""
    # 獲取查詢參數
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    min_score = request.args.get("min_score", type=int)
    max_score = request.args.get("max_score", type=int)

    # 構建查詢和參數
    query = "SELECT * FROM Reviews WHERE 1=1"
    params = []
    
    if min_score:
        query += " AND Score >= ?"
        params.append(min_score)
    
    if max_score:
        query += " AND Score <= ?"
        params.append(max_score)
    
    # 添加分頁
    offset = (page - 1) * limit
    query += f" ORDER BY Time DESC LIMIT {limit} OFFSET {offset}"
    
    # 緩存鍵
    cache_key = f"reviews:{page}:{limit}:{min_score}:{max_score}"
    
    # 執行查詢
    try:
        results = execute_query(query, tuple(params) if params else None, cache_key)
        
        # 獲取總記錄數（用於分頁）
        count_query = "SELECT COUNT(*) as total FROM Reviews WHERE 1=1"
        if min_score:
            count_query += " AND Score >= ?"
        if max_score:
            count_query += " AND Score <= ?"
        
        count_results = execute_query(count_query, tuple(params) if params else None)
        total = count_results[0]['total'] if count_results else 0
        
        return jsonify({
            "page": page,
            "limit": limit,
            "total_results": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1,
            "results": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reviews/<string:review_id>", methods=["GET"])
@swag_from({
    "tags": ["評論列表"],
    "summary": "獲取評論詳情",
    "description": "根據評論ID獲取詳細信息",
    "parameters": [
        {
            "name": "review_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "評論ID"
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取評論詳情"
        },
        "404": {
            "description": "找不到該評論"
        }
    }
})
def get_review_details(review_id):
    """獲取單條評論的詳細信息"""
    try:
        query = "SELECT * FROM Reviews WHERE Id = ?"
        results = execute_query(query, (review_id,))
        
        if not results:
            return jsonify({"error": "找不到該評論"}), 404
        
        review = results[0]
        
        # 獲取相關產品信息
        product_query = """
        SELECT ProductId, COUNT(*) as review_count, AVG(Score) as avg_score 
        FROM Reviews 
        WHERE ProductId = ? 
        GROUP BY ProductId
        """
        product_info = execute_query(product_query, (review['ProductId'],))
        
        # 構建完整回應
        response = {
            **review,
            "product_info": product_info[0] if product_info else None
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/product/<string:product_id>", methods=["GET"])
@swag_from({
    "tags": ["產品和用戶"],
    "summary": "獲取產品評論",
    "description": "獲取特定產品的所有評論",
    "parameters": [
        {
            "name": "product_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "產品ID"
        },
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "default": 1,
            "description": "頁碼"
        },
        {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "default": 20,
            "description": "每頁結果數量"
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取產品評論"
        }
    }
})
def get_product_reviews(product_id):
    """獲取特定產品的所有評論"""
    # 獲取查詢參數
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    offset = (page - 1) * limit
    
    try:
        # 獲取產品評論
        query = """
        SELECT * FROM Reviews 
        WHERE ProductId = ? 
        ORDER BY Time DESC 
        LIMIT ? OFFSET ?
        """
        reviews = execute_query(query, (product_id, limit, offset))
        
        # 獲取產品評論統計
        stats_query = """
        SELECT 
            ProductId, 
            COUNT(*) as review_count, 
            AVG(Score) as avg_score,
            SUM(CASE WHEN Score = 5 THEN 1 ELSE 0 END) as five_star,
            SUM(CASE WHEN Score = 4 THEN 1 ELSE 0 END) as four_star,
            SUM(CASE WHEN Score = 3 THEN 1 ELSE 0 END) as three_star,
            SUM(CASE WHEN Score = 2 THEN 1 ELSE 0 END) as two_star,
            SUM(CASE WHEN Score = 1 THEN 1 ELSE 0 END) as one_star
        FROM Reviews 
        WHERE ProductId = ?
        GROUP BY ProductId
        """
        stats = execute_query(stats_query, (product_id,))
        
        # 獲取總記錄數（用於分頁）
        count_query = "SELECT COUNT(*) as total FROM Reviews WHERE ProductId = ?"
        count_results = execute_query(count_query, (product_id,))
        total = count_results[0]['total'] if count_results else 0
        
        return jsonify({
            "product_id": product_id,
            "statistics": stats[0] if stats else None,
            "page": page,
            "limit": limit,
            "total_reviews": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1,
            "reviews": reviews
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/user/<string:user_id>", methods=["GET"])
@swag_from({
    "tags": ["產品和用戶"],
    "summary": "獲取用戶評論",
    "description": "獲取特定用戶的所有評論",
    "parameters": [
        {
            "name": "user_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "用戶ID"
        },
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "default": 1,
            "description": "頁碼"
        },
        {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "default": 20,
            "description": "每頁結果數量"
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取用戶評論"
        }
    }
})
def get_user_reviews(user_id):
    """獲取特定用戶的所有評論"""
    # 獲取查詢參數
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    offset = (page - 1) * limit
    
    try:
        # 獲取用戶評論
        query = """
        SELECT * FROM Reviews 
        WHERE UserId = ? 
        ORDER BY Time DESC 
        LIMIT ? OFFSET ?
        """
        reviews = execute_query(query, (user_id, limit, offset))
        
        # 獲取用戶評論統計
        stats_query = """
        SELECT 
            UserId, 
            ProfileName,
            COUNT(*) as review_count, 
            AVG(Score) as avg_score
        FROM Reviews 
        WHERE UserId = ?
        GROUP BY UserId, ProfileName
        """
        stats = execute_query(stats_query, (user_id,))
        
        # 獲取總記錄數（用於分頁）
        count_query = "SELECT COUNT(*) as total FROM Reviews WHERE UserId = ?"
        count_results = execute_query(count_query, (user_id,))
        total = count_results[0]['total'] if count_results else 0
        
        return jsonify({
            "user_id": user_id,
            "user_profile": stats[0] if stats else None,
            "page": page,
            "limit": limit,
            "total_reviews": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1,
            "reviews": reviews
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/search", methods=["GET"])
@swag_from({
    "tags": ["搜索"],
    "summary": "搜索評論",
    "description": "使用關鍵字搜索評論",
    "parameters": [
        {
            "name": "q",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "搜索關鍵詞"
        },
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "default": 1,
            "description": "頁碼"
        },
        {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "default": 20,
            "description": "每頁結果數量"
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取搜索結果"
        },
        "400": {
            "description": "搜索查詢不能為空"
        }
    }
})
def search_reviews():
    """使用關鍵字搜索評論"""
    query_text = request.args.get("q", "")
    if not query_text:
        return jsonify({"error": "必須提供搜索關鍵詞"}), 400
    
    # 獲取查詢參數
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    offset = (page - 1) * limit
    
    # 構建搜索查詢
    search_query = """
    SELECT * FROM Reviews 
    WHERE Text LIKE ? OR Summary LIKE ? 
    ORDER BY Time DESC 
    LIMIT ? OFFSET ?
    """
    search_params = (f"%{query_text}%", f"%{query_text}%", limit, offset)
    
    try:
        # 執行查詢
        results = execute_query(search_query, search_params)
        
        # 獲取總記錄數（用於分頁）
        count_query = "SELECT COUNT(*) as total FROM Reviews WHERE Text LIKE ? OR Summary LIKE ?"
        count_params = (f"%{query_text}%", f"%{query_text}%")
        count_results = execute_query(count_query, count_params)
        total = count_results[0]['total'] if count_results else 0
        
        return jsonify({
            "query": query_text,
            "page": page,
            "limit": limit,
            "total_results": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1,
            "results": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/query", methods=["POST"])
@swag_from({
    "tags": ["搜索"],
    "summary": "自然語言查詢評論",
    "description": "使用自然語言查詢評論，由 Gemini API 解析",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "自然語言查詢"
                    }
                },
                "required": ["query"]
            }
        }
    ],
    "responses": {
        "200": {
            "description": "成功獲取查詢結果"
        },
        "400": {
            "description": "查詢不能為空"
        },
        "500": {
            "description": "處理查詢時發生錯誤"
        }
    }
})
def query_reviews():
    """使用自然語言查詢評論（使用 Gemini API）"""
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "必須提供自然語言查詢"}), 400

    user_query = data["query"]

    # 使用 Gemini API 解析查詢
    prompt = f"""
    根據以下自然語言查詢，提取關於Amazon食品評論的搜索關鍵信息。
    請以JSON格式回傳以下欄位（如果有相關信息）：
    - keyword: 評論中的關鍵詞
    - min_score: 最低評分 (1-5)
    - max_score: 最高評分 (1-5)
    - product: 特定產品名稱或ID
    - user: 特定用戶名稱或ID
    - sentiment: 情感傾向 (positive, negative, neutral)

    例如：如果查詢是"找出評分是5星的巧克力評論"，應返回：{{"keyword": "巧克力", "min_score": 5, "max_score": 5}}

    查詢: {user_query}
    """

    try:
        print(f"正在處理查詢: {user_query}")
        gemini_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        print(f"Gemini API 原始回應: {gemini_response.text}")
        
        # 解析 Gemini 回應
        try:
            structured_query = json.loads(gemini_response.text)
            print(f"結構化查詢內容: {structured_query}")
        except json.JSONDecodeError as json_err:
            print(f"JSON解析錯誤: {json_err}. 原始回應: {gemini_response.text}")
            return jsonify({"error": f"無法解析模型回應為JSON: {str(json_err)}"}), 500

        # 根據結構化查詢搜索評論
        sql_query = "SELECT * FROM Reviews WHERE 1=1"
        params = []
        
        # 處理評分範圍
        if "min_score" in structured_query and structured_query["min_score"]:
            sql_query += " AND Score >= ?"
            params.append(structured_query["min_score"])
        
        if "max_score" in structured_query and structured_query["max_score"]:
            sql_query += " AND Score <= ?"
            params.append(structured_query["max_score"])
        
        # 處理關鍵詞
        if "keyword" in structured_query and structured_query["keyword"]:
            keyword = structured_query["keyword"]
            sql_query += " AND (Text LIKE ? OR Summary LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        # 處理特定產品
        if "product" in structured_query and structured_query["product"]:
            product = structured_query["product"]
            # 嘗試直接匹配產品ID或在文本中搜索
            sql_query += " AND (ProductId = ? OR Text LIKE ? OR Summary LIKE ?)"
            params.extend([product, f"%{product}%", f"%{product}%"])
        
        # 處理特定用戶
        if "user" in structured_query and structured_query["user"]:
            user = structured_query["user"]
            # 嘗試匹配用戶ID或名稱
            sql_query += " AND (UserId = ? OR ProfileName LIKE ?)"
            params.extend([user, f"%{user}%"])
            
        # 排序和限制結果
        sql_query += " ORDER BY Time DESC LIMIT 50"
        
        # 執行查詢
        results = execute_query(sql_query, tuple(params) if params else None)
        
        # 如果有情感分析要求，可以使用Gemini進行分析
        if "sentiment" in structured_query and structured_query["sentiment"] and results:
            sentiment = structured_query["sentiment"].lower()
            # 這裡可以實現更複雜的情感過濾邏輯
            # 目前只是簡單示例
            
        return jsonify({
            "query": user_query,
            "interpreted_as": structured_query,
            "results_count": len(results),
            "results": results
        })
        
    except Exception as e:
        print(f"查詢處理錯誤: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/debug", methods=["GET"])
@swag_from({
    "tags": ["系統"],
    "summary": "調試系統狀態",
    "description": "獲取系統數據加載狀態信息",
    "responses": {
        "200": {
            "description": "成功獲取系統狀態"
        }
    }
})
def debug():
    """調試端點，用於檢視數據庫狀態"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 獲取資料表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [dict(row) for row in cursor.fetchall()]
        
        # 獲取各表記錄數
        table_counts = {}
        for table in tables:
            table_name = table['name']
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
            count = cursor.fetchone()['count']
            table_counts[table_name] = count
        
        conn.close()
        
        return jsonify({
            "database_path": DB_PATH,
            "database_exists": os.path.exists(DB_PATH),
            "tables": tables,
            "record_counts": table_counts,
            "cache_status": {
                "query_cache_size": len(cache["query_cache"]),
                "last_load_time": cache["last_load_time"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """提供網站圖標"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("錯誤：未設置 GEMINI_API_KEY 環境變數")
        exit(1)

    print("初始化Amazon Fine Food Reviews系統...")
    
    if not os.path.exists(DB_PATH):
        print(f"警告：找不到資料庫文件: {DB_PATH}")
        print("請先運行 download_data.sh 下載數據")
    else:
        print(f"資料庫檔案已存在: {DB_PATH}")
        check_database()
    
    # 使用環境變數來控制 debug 模式，預設為 False（安全模式）
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    app.run(debug=debug_mode) 