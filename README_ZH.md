# BBC News Mini Corpus API

一個基於 BBC News Dataset 的 RESTful API，支持各類別的新聞查詢和自然語言查詢處理系統。

## 主要特點

- 📰 使用 SQLite 資料庫存取 BBC News 文章數據
- 🔍 高效的查詢緩存機制，提升查詢速度
- 💬 支持自然語言查詢處理（使用Gemini AI模型）
- 🗄️ 簡潔、模塊化的代碼結構
- 🚀 輕量級設計，易於擴展
- 🌐 提供網頁界面進行直觀查詢

## 資料集資訊

本項目使用 BBC News Dataset，包含五個主要類別的新聞文章：
- **business**: 商業新聞
- **entertainment**: 娛樂新聞
- **politics**: 政治新聞
- **sport**: 體育新聞
- **tech**: 科技新聞

數據來源：`https://huggingface.co/datasets/hf-internal/bbc-text/resolve/main/bbc-text.csv`

## 專案架構圖

```
bbc-news-api/
├── app.py              # Flask 主應用入口點
├── routes.py           # API 路由處理邏輯
├── db.py               # 數據庫連接和查詢模塊
├── chatgpt_model.py    # ChatGPT AI 模型整合
├── gemini_model.py     # Gemini AI 模型整合
├── requirements.txt    # 依賴套件列表
├── .env                # 環境變數配置文件
├── template.env        # 環境變數範本
├── README.md           # 英文說明文件
├── README_ZH.md        # 中文說明文件
│
├── scripts/            # 輔助腳本
│   └── csv_to_sqlite.py    # 轉換 CSV 到 SQLite
│
├── static/             # 靜態資源
│   ├── css/
│   │   └── style.css       # 樣式表
│   └── js/
│       └── script.js       # 前端交互脚本
│
├── templates/          # HTML 模板
│   ├── index.html          # 主頁面/聊天界面
│   └── api.html            # API 文檔頁面
│
└── data/               # 數據文件夾 (自動創建)
    ├── bbc-news.csv        # 原始 CSV 數據
    └── bbc_news.sqlite     # SQLite 數據庫
```

## 系統流程圖

```
用户請求 → Flask 應用 (app.py)
    ↓
路由處理 (routes.py) → 數據庫查詢 (db.py) → SQLite 數據庫
    ↓                     ↑
自然語言解析 ← Gemini AI 模型 (gemini_model.py)
    ↓
JSON 響應 → 前端顯示
```

## 環境設置

### 前置條件

- Python 3.8+
- 網絡連接（用於下載數據集）
- Gemini API Key（可選，用於自然語言查詢功能）

### 安裝步驟

1. **克隆本倉庫**：

   ```bash
   git clone <repository-url>
   cd bbc-news-api
   ```

2. **建立並啟用虛擬環境**：

   ```bash
   python -m venv venv
   source venv/bin/activate  # 在 Windows 上使用 venv\Scripts\activate
   ```

3. **安裝依賴**：

   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

4. **配置環境變數**：

   將 `template.env` 複製為 `.env` 並設定你的 Gemini API Key（如果需要自然語言查詢功能）：

   ```bash
   cp template.env .env
   # 然後編輯 .env 文件添加你的 API 密鑰
   ```

5. **準備資料**：

   ```bash
   # Step 5: 準備資料
   1. 下載 CSV：https://huggingface.co/datasets/hf-internal/bbc-text/resolve/main/bbc-text.csv
   2. 將檔案重新命名為 bbc-news.csv 放到 data/ 資料夾
   3. 轉檔
      python scripts/csv_to_sqlite.py
   ```

## 運行應用

啟動 Flask 應用：

```bash
python app.py
```

應用會在 http://localhost:5000 運行。

## 使用自然語言查詢

本系統支持使用自然語言查詢 BBC 新聞文章。這些功能可以通過聊天界面 (http://localhost:5000/) 或 API 端點使用。

### 可用的自然語言查詢示例：

1. **基於類別查詢**：
   - "尋找商業新聞"
   - "顯示最新的政治報導"

2. **基於關鍵詞查詢**：
   - "查找有關蘋果公司的科技新聞"
   - "找出提到足球的體育新聞"

3. **綜合查詢**：
   - "尋找討論市場的商業新聞"
   - "有哪些關於電影的娛樂新聞？"

## 測試 API

可以通過以下方式測試 API：

### 使用瀏覽器

訪問聊天界面：http://localhost:5000/

### 使用 curl

1. **測試自然語言查詢**：

   ```bash
   curl -X POST http://localhost:5000/api/query \
     -H "Content-Type: application/json" \
     -d '{"query":"尋找科技類別中關於蘋果的新聞"}'
   ```

2. **獲取新聞列表**：

   ```bash
   curl http://localhost:5000/api/news?category=tech&limit=10
   ```

3. **獲取特定新聞詳情**：

   ```bash
   curl http://localhost:5000/api/news/1
   ```

4. **搜索新聞**：

   ```bash
   curl http://localhost:5000/api/search?q=market
   ```

5. **檢查系統狀態**：
   ```bash
   curl http://localhost:5000/api/system_status
   ```

## API 端點列表

### 新聞查詢

- `GET /api/news` - 獲取新聞列表（支持分頁和類別過濾）
  - 參數: `page`, `limit`, `category`, `keyword`
- `GET /api/news/{news_id}` - 獲取特定新聞詳情

### 搜索

- `GET /api/search?q={query}` - 基本文字搜索
  - 參數: `q`, `page`, `limit`
- `POST /api/query` - 自然語言查詢
  - 請求體: `{"query": "自然語言查詢文本"}`

### 系統

- `GET /api/debug` - 除錯信息
- `GET /api/system_status` - 獲取系統狀態

## 主要模塊功能

- **app.py**: Flask 應用入口點，初始化服務和路由
- **routes.py**: 處理所有 API 路由和請求邏輯
- **db.py**: 數據庫連接和查詢處理，包含緩存機制
- **gemini_model.py**: 與 Gemini AI 模型整合，處理自然語言查詢解析

## 擴展建議

1. 添加更多 NLP 功能，如文章摘要或情感分析
2. 實現更高級的搜索功能，如相似度搜索
3. 添加用戶認證和授權
4. 增加對更多新聞源的支持
5. 添加定期數據更新機制

## 故障排除

1. **數據庫文件不存在**：
   - 確保已下載 CSV 文件並放置在 data/ 文件夾中
   - 執行 `python scripts/csv_to_sqlite.py` 轉換 CSV 到 SQLite
   - 確認 `data/bbc_news.sqlite` 文件存在

2. **自然語言查詢功能不可用**：
   - 確認 `.env` 文件存在並包含有效的 `GEMINI_API_KEY`
   - 檢查 API 密鑰限制和網絡連接

3. **應用啟動錯誤**：
   - 檢查所有依賴是否已正確安裝
   - 查看日誌以獲取詳細錯誤信息
   
4. **查詢返回空結果**：
   - 確認數據庫已正確創建且包含數據
   - 使用 `api/system_status` 端點檢查系統狀態
