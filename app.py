import os
import json
import time
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory

# 載入 .env 檔案中的環境變數
load_dotenv()

# 初始化 AI 模型 (可選)
AI_MODEL_TYPE = os.getenv("AI_MODEL_TYPE", "GEMINI").upper()
ai_model = None

try:
    if AI_MODEL_TYPE == "GEMINI":
        from gemini_model import GeminiModel
        ai_model = GeminiModel()
        print("使用 Gemini AI 模型")
    else:
        print(f"未知的 AI_MODEL_TYPE: {AI_MODEL_TYPE}")
except Exception as e:
    print(f"初始化 AI 模型時發生錯誤: {e}")
    # 在實際應用中，可能需要終止應用程式或提供備用方案

# 初始化 Flask app
app = Flask(__name__)

# 引入路由
from routes import api
app.register_blueprint(api, url_prefix='/api')

# 設定請求處理前的鉤子，記錄請求時間
@app.before_request
def before_request():
    request.environ['REQUEST_TIME'] = time.time()

@app.route("/", methods=["GET"])
def index():
    """提供聊天介面的 HTML 頁面"""
    return render_template("index.html")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# 全域錯誤處理
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "找不到資源"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "伺服器內部錯誤"}), 500

if __name__ == "__main__":
    # 初始化資料庫
    from db import check_database
    check_database()
    
    # 啟動 Flask 應用
    app.run(debug=True, host="0.0.0.0", port=5000) 