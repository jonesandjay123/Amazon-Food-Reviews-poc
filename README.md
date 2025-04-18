# BBC News Mini Corpus API

一個基於 BBC News Dataset 的 RESTful API，支持各類別的新聞查詢和自然語言查詢。

## 主要特點

- 📰 使用 SQLite 資料庫存取 BBC News 文章數據
- 🔍 高效的查詢緩存機制，提升查詢速度
- 💬 支持自然語言查詢處理
- 🗄️ 簡潔、模塊化的代碼結構
- 🚀 輕量級設計，易於擴展

## 資料集資訊

本項目使用 BBC News Dataset，包含五個主要類別的新聞文章：
- **business**: 商業新聞
- **entertainment**: 娛樂新聞
- **politics**: 政治新聞
- **sport**: 體育新聞
- **tech**: 科技新聞

數據來源：`https://storage.googleapis.com/ztm_tf_course/bbc-text.csv`

## 環境設置

### 前置條件

- Python 3.8+
- 網絡連接（用於下載數據集）

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
   pip install -r requirements.txt
   ```

4. **下載數據並創建 SQLite 數據庫**：

   ```bash
   chmod +x scripts/download_data.sh
   ./scripts/download_data.sh
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
- `GET /api/news/{news_id}` - 獲取特定新聞詳情

### 搜索

- `GET /api/search?q={query}` - 基本文字搜索
- `POST /api/query` - 自然語言查詢

### 系統

- `GET /api/debug` - 除錯信息
- `GET /api/system_status` - 獲取系統狀態

## 項目結構

```
bbc-news-api/
├── app.py          # Flask 主應用
├── db.py           # 數據庫連接和查詢模塊
├── routes.py       # API 路由處理
├── requirements.txt # 依賴列表
├── scripts/        # 輔助腳本
│   ├── download_data.sh    # 下載數據腳本
│   └── csv_to_sqlite.py    # 轉換 CSV 到 SQLite
├── static/         # 靜態資源
│   ├── css/        # 樣式表
│   └── js/         # JavaScript 文件
├── templates/      # HTML 模板
└── data/           # 數據文件夾
    ├── bbc-news.csv       # 原始 CSV 數據
    └── bbc_news.sqlite    # SQLite 數據庫
```

## 擴展建議

1. 添加更多 NLP 功能，如文章摘要或情感分析
2. 實現更高級的搜索功能，如相似度搜索
3. 添加用戶認證和授權
4. 增加對更多新聞源的支持

## 故障排除

1. **數據庫文件不存在**：
   - 執行 `./scripts/download_data.sh` 確保已下載並轉換數據
   - 確認 `data/bbc_news.sqlite` 文件存在

2. **應用啟動錯誤**：
   - 檢查所有依賴是否已正確安裝
   - 查看日誌以獲取詳細錯誤信息