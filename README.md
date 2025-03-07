# Place Recommender with Gemini API

這是一個使用 Google Places API 和 Google Gemini API 的地點推薦系統。該系統模擬了一個簡單的 Retrieval-Augmented Generation (RAG) 架構，但是使用公開的 Google Places API 來代替傳統的向量數據庫。

## 專案概述

此專案實現了以下流程：

1. 使用者以自然語言提出問題（例如：「推薦台北市最好的五家咖啡廳」）
2. 系統使用 Gemini API 分析查詢並提取結構化信息
3. 使用提取的信息通過 Google Places API 查詢相關場所
4. 使用 Gemini API 將 API 返回的 JSON 數據轉換為易讀的文本格式
5. 將處理後的結果返回給使用者

## 安裝與設置

### 前提條件

- Python 3.10.9 或更高版本
- Google Places API 密鑰
- Google Gemini API 密鑰

### 安裝步驟

1. 克隆此存儲庫
2. 安裝所需依賴項：
   ```
   pip install -r requirements.txt
   ```
3. 創建 `.env` 文件（參考 `.env.example`）並添加您的 API 密鑰：
   ```
   GOOGLE_PLACES_API_KEY=your_google_places_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

## 使用方法

1. 啟動 Flask 服務器：
   ```
   python app.py
   ```
2. 向 `/query` 端點發送 POST 請求以提交查詢：

   ```
   curl -X POST http://localhost:5000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "推薦台北市最好的五家咖啡廳"}'
   ```

3. 收到成功響應後，向 `/results` 端點發送 GET 請求以獲取處理後的結果：
   ```
   curl http://localhost:5000/results
   ```

## API 端點

### POST /query

接受自然語言查詢，並使用 Google Places API 獲取相關數據。

**請求格式：**

```json
{
  "query": "推薦台北市最好的五家咖啡廳"
}
```

**響應格式：**

```json
{
  "query": "推薦台北市最好的五家咖啡廳",
  "status": "success",
  "message": "查詢成功，請使用 /results 端點查看整理後的結果"
}
```

### GET /results

獲取經 Gemini API 處理後的場所推薦列表。

**響應格式：**

```json
{
  "query": "推薦台北市最好的五家咖啡廳",
  "results": [
    "1. 小藝咖啡 (Arthere Café) - 評分：4.8",
    "2. 富錦街咖啡 Fujin Tree Café - 評分：4.6",
    "..."
  ]
}
```

## 注意事項

- 此示例應用使用全局變量來存儲查詢結果。在實際生產環境中，應考慮使用數據庫或緩存系統。
- 請確保您的 Google Places API 和 Gemini API 帳戶有足夠的配額和權限。
- 此應用僅用於演示目的，可能需要根據您的具體需求進行調整。
