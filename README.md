# 電影數據 RAG 系統

這是一個基於 Flask 的 API 系統，使用電影數據集和 Gemini API 實現自然語言查詢電影信息的功能。此系統旨在展示 LangChain (RAG) 在多步驟檢索上的優勢。

## 專案概述

此專案實現了以下流程：

1. 使用者以自然語言提出問題（例如：「找出克里斯托弗·諾蘭導演的所有電影」）
2. 系統使用 Gemini API 分析查詢並提取結構化信息
3. 使用提取的信息在電影數據集中查詢相關電影
4. 返回匹配的電影列表給使用者

## 數據集

本專案使用 [Kaggle 的 The Movies Dataset](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset) 中的數據。該數據集包含約 45,000 部電影的元數據，以及用戶對這些電影的評分數據。

原始數據集包含 7 個 CSV 文件，但我們只選擇了其中 3 個最有用的文件：

- `movies_metadata.csv` - 包含電影的基本信息（標題、類型、票房等）
- `credits.csv` - 包含演員和導演等工作人員信息
- `ratings_small.csv` - 包含用戶對電影的評分（縮小版，處理更高效）

我們沒有使用其他 4 個文件（keywords.csv, links.csv, links_small.csv, ratings.csv），因為它們對於我們的基本示範不是必需的，這樣可以減少數據處理的複雜性。

## 安裝與設置

### 前提條件

- Python 3.10 或更高版本
- Google Gemini API 密鑰

### 安裝步驟

1. 克隆此存儲庫
2. 安裝所需依賴項：
   ```
   pip install -r requirements.txt
   ```
3. 創建 `.env` 文件並添加您的 Gemini API 密鑰：
   ```
   GEMINI_API_KEY=your_gemini_api_key
   ```
4. 在專案根目錄下創建 `data` 目錄，並將以下數據文件放入其中：
   - `movies_metadata.csv`
   - `credits.csv`
   - `ratings_small.csv`

## 使用方法

1. 啟動 Flask 服務器：
   ```
   python app.py
   ```
2. 訪問 Web 界面：在瀏覽器中打開 `http://localhost:5000`

3. 訪問 API 文檔：在瀏覽器中打開 `http://localhost:5000/api` 或點擊 Web 界面上的「API 文檔」連結

4. 使用 Swagger UI 測試 API：瀏覽 `http://localhost:5000/api/docs/`

5. 或直接使用 API 端點：
   ```
   curl -X POST http://localhost:5000/api/query \
     -H "Content-Type: application/json" \
     -d '{"query": "找出克里斯托弗·諾蘭導演的所有電影"}'
   ```

## API 測試流程

以下是測試各個 API 端點的推薦流程：

### 1. 基本電影列表查詢

首先，獲取一個基本的電影列表：

```bash
curl "http://localhost:5000/api/movies?limit=5"
```

### 2. 帶過濾條件的查詢

嘗試使用不同的過濾條件：

```bash
# 獲取 2010 年發行的電影
curl "http://localhost:5000/api/movies?year=2010&limit=5"

# 獲取類型為 "Action" 的電影
curl "http://localhost:5000/api/movies?genre=Action&limit=5"

# 獲取平均評分大於 4.0 的電影
curl "http://localhost:5000/api/movies?min_rating=4.0&limit=5"
```

### 3. 查詢特定電影的詳細信息

使用從上一步獲得的電影 ID：

```bash
curl "http://localhost:5000/api/movies/550"  # 以《Fight Club》為例
```

### 4. 查詢特定演員或導演的電影

```bash
# 查詢特定演員的電影
curl "http://localhost:5000/api/actor/Tom%20Hanks"

# 查詢特定導演的電影
curl "http://localhost:5000/api/director/Christopher%20Nolan"
```

### 5. 文本搜索

使用關鍵字搜索電影：

```bash
curl "http://localhost:5000/api/search?q=matrix"
```

### 6. 自然語言查詢（使用 Gemini API）

嘗試使用自然語言提問：

```bash
curl -X POST "http://localhost:5000/api/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "找出克里斯托弗·諾蘭導演2010年之後的所有電影並按評分排序"}'
```

## Gemini API 的作用

在本系統中，Google Gemini API 發揮了關鍵作用：

1. **自然語言理解**：將用戶的自然語言問題轉換為結構化查詢參數

   - 例如，從「找出克里斯托弗·諾蘭導演 2010 年之後的所有電影」中提取出「director: Christopher Nolan」和「year: > 2010」

2. **查詢意圖識別**：識別用戶查詢的主要意圖（搜索演員、導演、特定類型等）

3. **複雜條件解析**：處理複合查詢條件，如同時指定多個過濾條件

Gemini API 讓我們的系統能夠以更自然的方式與用戶互動，而不需要用戶學習特定的查詢語法。用戶可以用日常語言提出問題，系統會自動理解並執行適當的查詢。

這種方法是 RAG（檢索增強生成）系統的前身，在下一階段我們將整合 LangChain 來實現完整的 RAG 功能，屆時 Gemini API 不僅會參與查詢解析，還會參與檢索後的內容生成和整合。

## API 端點

### 基本端點

#### GET /

提供聊天界面的 HTML 頁面。

#### POST /api/query

接受自然語言查詢，使用 Gemini API 解析查詢，並在電影數據集中查找相關電影。

**請求格式：**

```json
{
  "query": "找出克里斯托弗·諾蘭導演的所有電影"
}
```

**響應格式：**

```json
{
  "query": "找出克里斯托弗·諾蘭導演的所有電影",
  "interpreted_as": {
    "director": "Christopher Nolan"
  },
  "results_count": 10,
  "results": [
    {
      "id": 49026,
      "title": "The Dark Knight",
      "release_date": "2008-07-16",
      "genres": ["Action", "Crime", "Drama", "Thriller"],
      "vote_average": 8.4,
      "revenue": 1004558444
    }
    // ... 更多電影
  ]
}
```

### 特定數據查詢端點

#### GET /api/movies

獲取電影列表，支持多種過濾條件。

**查詢參數：**

- `page` - 頁碼（默認：1）
- `limit` - 每頁結果數量（默認：20）
- `year` - 發行年份
- `genre` - 電影類型
- `min_rating` - 最低評分
- `min_revenue` - 最低票房

#### GET /api/movies/{movie_id}

獲取特定電影的詳細信息。

#### GET /api/actor/{actor_name}

獲取特定演員參演的所有電影。

#### GET /api/director/{director_name}

獲取特定導演執導的所有電影。

#### GET /api/search

基於文本搜索電影。

**查詢參數：**

- `q` - 搜索查詢文本

#### GET /api/debug

調試端點，用於檢視數據加載狀態。

## 實現架構

本專案分為以下幾個層次：

1. **數據加載與處理層**

   - 加載 CSV 數據文件
   - 清理和預處理數據
   - 解析 JSON 格式的字段

2. **API 層**

   - 提供各種查詢端點
   - 處理請求參數和返回結果

3. **自然語言處理層**

   - 使用 Gemini API 解析自然語言查詢
   - 提取結構化查詢參數

4. **前端界面層**
   - 提供簡潔的聊天界面
   - 處理用戶輸入和查詢結果顯示

## 開發路線圖

1. **階段一：基礎功能實現** ✓

   - 數據加載和處理
   - 基本 API 端點
   - 簡單的前端界面

2. **階段二：增強查詢能力**

   - 整合 LangChain 框架
   - 實現 RAG（檢索增強生成）
   - 改進查詢解析和結果排序

3. **階段三：高級功能**
   - 實現電影推薦系統
   - 添加用戶歷史記錄和個性化查詢
   - 改進前端界面，添加視覺化組件

## 注意事項

- 此示例應用使用直接加載 CSV 文件的方式處理數據。在實際生產環境中，應考慮使用數據庫存儲數據。
- 請確保您的 Gemini API 帳戶有足夠的配額和權限。
- 此應用僅用於演示目的，可能需要根據您的具體需求進行調整。
