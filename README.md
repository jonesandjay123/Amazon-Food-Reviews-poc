# 電影推薦 API

基於 Kaggle 電影數據集的 RESTful API，支持電影查詢、演員/導演作品搜索，以及使用 Gemini API 的自然語言查詢。

## 主要特點

- 📊 從 Kaggle 直接獲取電影數據，無需下載本地 CSV 文件
- 🔍 高效的內存緩存機制，顯著提升查詢速度
- 🔄 SQL 查詢優化，僅獲取所需數據，降低傳輸負載
- 💬 集成 Google Gemini API 進行自然語言處理
- 📚 完整的 Swagger API 文檔
- 🧠 智能導演/演員名稱匹配（支持精確和模糊匹配）

## 運行環境設置

### 前置條件

- Python 3.9+
- Kaggle 帳號和 API 密鑰
- Google Gemini API 密鑰

### 安裝步驟

1. **克隆本倉庫**：

   ```bash
   git clone <repository-url>
   cd movie-recommendation-poc
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

4. **設置環境變數**：
   建立 `.env` 文件並添加以下內容：
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

### Kaggle API 設置

1. **獲取 Kaggle API 密鑰**：

   - 登錄到 [Kaggle](https://www.kaggle.com/)
   - 點擊右上角您的頭像 > Account
   - 滾動到 API 區塊，點擊 "Create New API Token"
   - 這會下載 `kaggle.json` 文件

2. **配置 Kaggle API**：
   - 將 `kaggle.json` 文件放在 `~/.kaggle/` 目錄下（Windows：`C:\Users\<YourUsername>\.kaggle\`）
   - 設置適當的權限：
     ```bash
     mkdir -p ~/.kaggle
     cp kaggle.json ~/.kaggle/
     chmod 600 ~/.kaggle/kaggle.json
     ```

## 運行應用

啟動 Flask 應用：

```bash
python app.py
```

應用會在 http://localhost:5000 運行，首次啟動時會從 Kaggle 加載數據到內存緩存。

## 測試 API

可以通過以下方式測試 API：

### 使用瀏覽器

1. 訪問 API 文檔：http://localhost:5000/api/docs/
2. 使用聊天界面：http://localhost:5000/

### 使用 curl

1. **測試自然語言查詢**：

   ```bash
   curl -X POST http://localhost:5000/api/query \
     -H "Content-Type: application/json" \
     -d '{"query":"Find movies directed by Christopher Nolan"}'
   ```

2. **測試導演電影列表**：

   ```bash
   curl http://localhost:5000/api/director/Christopher%20Nolan
   ```

3. **測試演員電影列表**：

   ```bash
   curl http://localhost:5000/api/actor/Leonardo%20DiCaprio
   ```

4. **搜索電影**：

   ```bash
   curl http://localhost:5000/api/search?q=inception
   ```

5. **檢查系統狀態**：
   ```bash
   curl http://localhost:5000/api/debug
   ```

## 數據集信息

本項目使用 Kaggle 的 "The Movies Dataset"，包含來自 TMDB 的約 45,000 部電影信息：
https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset

## 故障排除

1. **Kaggle API 驗證錯誤**：

   - 確認 `kaggle.json` 文件位置正確
   - 檢查文件權限設置

2. **數據加載緩慢**：

   - 首次加載需從 Kaggle 獲取數據，可能需要幾分鐘
   - 之後的請求將使用內存緩存，速度會顯著提升

3. **Gemini API 錯誤**：
   - 確認 `.env` 文件中 `GEMINI_API_KEY` 設置正確
   - 檢查 API 密鑰是否有效，以及使用限制是否達到上限

## API 端點列表

### 電影查詢

- `GET /api/movies` - 獲取電影列表（支持分頁和過濾）
- `GET /api/movies/{movie_id}` - 獲取特定電影詳情

### 演員和導演

- `GET /api/actor/{actor_name}` - 獲取演員參演的電影
- `GET /api/director/{director_name}` - 獲取導演執導的電影

### 搜索

- `GET /api/search?q={query}` - 基本電影搜索
- `POST /api/query` - 自然語言查詢（使用 Gemini API）

### 系統

- `GET /api/debug` - 檢查系統狀態
- `GET /api/debug/directors` - 列出導演名稱（用於調試）
