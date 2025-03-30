# Amazon Fine Food Reviews API

基於 Kaggle Amazon Fine Food Reviews 數據集的 RESTful API，支持食品評論查詢，以及使用 Gemini API 的自然語言查詢。

## 主要特點

- 🍕 使用 SQLite 資料庫存取 Amazon 食品評論數據
- 🔍 高效的查詢緩存機制，提升查詢速度
- 💬 集成 Google Gemini API 進行自然語言處理
- 📚 完整的 Swagger API 文檔
- 🧠 智能評論搜索與分析

## 運行環境設置

### 前置條件

- Python 3.9+
- Kaggle 帳號和 API 密鑰
- Google Gemini API 密鑰

### 安裝步驟

1. **克隆本倉庫**：

   ```bash
   git clone <repository-url>
   cd food-reviews-api
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
   - Kaggle API 密鑰通常存放在 `~/.kaggle/kaggle.json` 文件中
   - 如果尚未設置，請登錄 [Kaggle](https://www.kaggle.com/)，點擊右上角您的頭像 > Account > API > Create New API Token

### 下載數據

#### 選項1：使用提供的腳本（推薦）
執行以下命令下載並解壓 Amazon Fine Food Reviews 數據集：

```bash
chmod +x download_data.sh
./download_data.sh
```

這將下載數據庫文件並將其解壓到 `data` 目錄中。

#### 選項2：手動下載
如果您無法使用 Kaggle CLI 或遇到問題，可以手動下載數據：

1. 手動從 Kaggle 下載數據集：[Amazon Fine Food Reviews](https://www.kaggle.com/datasets/snap/amazon-fine-food-reviews)
2. 解壓縮下載的文件，獲取 `database.sqlite` 文件
3. 如果項目根目錄中沒有 `data` 目錄，請創建一個
4. 將 `database.sqlite` 文件放入 `data` 目錄中

## 運行應用

啟動 Flask 應用：

```bash
python app.py
```

應用會在 http://localhost:5000 運行。

## 使用 Gemini API 自然語言查詢

本系統集成了 Google Gemini API，可以用自然語言查詢食品評論數據。這些功能可以通過聊天界面 (http://localhost:5000/) 或 API 端點使用。

### 可用的自然語言查詢示例：

1. **基於關鍵詞搜索**：
   - "找出有關巧克力的評論"
   - "顯示包含'delicious'的評論"

2. **基於評分過濾**：
   - "找出五星評分的巧克力評論"
   - "顯示評分大於3星的食品評論"

3. **特定產品查詢**：
   - "找出產品ID為B001E4KFG0的所有評論"
   - "這個產品B000LQOCH0收到了哪些好評？"

4. **用戶評論分析**：
   - "顯示用戶A1RSDE90N6RSZF的所有評論"
   - "哪些用戶給出了最多的五星評價？"

5. **情感分析**：
   - "找出對巧克力最正面的評論"
   - "有哪些對這個產品B005IGVBPK的負面評論？"

6. **綜合查詢**：
   - "找出2010年發表的對巧克力的五星評論"
   - "顯示評分為1星且評論包含'disappointed'的食品評論"

### Gemini API 如何工作：

系統會將您的自然語言查詢發送到 Gemini API，Gemini 會解析查詢並提取關鍵參數：
- 關鍵詞 (keyword)
- 評分範圍 (min_score, max_score)
- 產品識別符 (product)
- 用戶識別符 (user)
- 情感傾向 (sentiment)

然後，系統使用這些參數構建 SQL 查詢，從數據庫中獲取相關評論。

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
     -d '{"query":"找出有關巧克力的五星評論"}'
   ```

2. **獲取評論列表**：

   ```bash
   curl http://localhost:5000/api/reviews?limit=10&min_score=5
   ```

3. **獲取特定產品的評論**：

   ```bash
   curl http://localhost:5000/api/product/B001E4KFG0
   ```

4. **搜索評論**：

   ```bash
   curl http://localhost:5000/api/search?q=delicious
   ```

5. **檢查系統狀態**：
   ```bash
   curl http://localhost:5000/api/debug
   ```

## 數據集信息

本項目使用 Kaggle 的 "Amazon Fine Food Reviews" 數據集，包含來自 Amazon 的約 568,454 條食品評論：
https://www.kaggle.com/datasets/snap/amazon-fine-food-reviews

數據庫文件（`database.sqlite`）包含以下信息：
- 產品評論文本和評分 (1-5 星)
- 產品信息
- 用戶信息
- 評論時間和摘要

## 故障排除

1. **Kaggle API 驗證錯誤**：
   - 確認 `~/.kaggle/kaggle.json` 文件存在並有正確的權限
   - 如果使用手動下載方法，可以忽略此錯誤

2. **數據庫文件不存在**：
   - 執行 `./download_data.sh` 下載數據庫文件
   - 或按照「選項2：手動下載」中的步驟手動下載
   - 確認 `data/database.sqlite` 文件存在

3. **Gemini API 錯誤**：
   - 確認 `.env` 文件中 `GEMINI_API_KEY` 設置正確
   - 檢查 API 密鑰是否有效，以及使用限制是否達到上限

## API 端點列表

### 評論查詢

- `GET /api/reviews` - 獲取評論列表（支持分頁和評分過濾）
- `GET /api/reviews/{review_id}` - 獲取特定評論詳情

### 產品和用戶

- `GET /api/product/{product_id}` - 獲取特定產品的評論
- `GET /api/user/{user_id}` - 獲取特定用戶的評論

### 搜索

- `GET /api/search?q={query}` - 基本評論搜索
- `POST /api/query` - 自然語言查詢（使用 Gemini API）

### 系統

- `GET /api/debug` - 檢查系統狀態

## 未來優化方向：引入 LangChain（Agentic RAG）

目前系統已經具備豐富功能，包括：
- 關鍵字搜尋
- 評分篩選
- 特定產品或使用者查詢
- 情緒分析相關查詢
- 複合條件查詢

當前系統已實現了標準的 RAG（Retrieval-Augmented Generation）架構，可將自然語言轉換成單一步驟的結構化查詢（SQL）。雖然這種方法非常實用，但仍有一些潛在限制。

### 現有方案的限制

- **單一步驟查詢**：一次只能產生一個查詢條件組合，無法根據第一次結果再動態決定下一步。
- **缺乏「推理性」(Reasoning)**：系統無法依照使用者問題背後的深層意圖，自動進行「多步驟」的探索、交互查詢。
- **沒有智能重試機制**：若第一次查詢資料不足，無法自動重新組合條件、修改或擴充查詢範圍。

### 透過 LangChain Agent 可實現的具體改進

#### 1. 多步推理查詢 (Multi-Step Reasoning)

使用者問題：「給我最近5年來，平均評分超過4.5，評論人數最多的前5個產品是什麼？」

LangChain 可以：
- 第一步查詢最近五年評分 > 4.5 的所有產品。
- 第二步計算各產品的評論數量。
- 第三步依照結果取前五名。
- 最後回傳結論。

#### 2. 自動化的資料不足調整 (Intelligent Retry)

當查詢結果過少（例如少於10筆）時，LangChain 可以自動擴大搜尋範圍，例如降低評分標準或改變搜尋關鍵字，直到回傳足夠的資料給用戶。

#### 3. 交互式對話 (Conversational Queries)

用戶問題：「巧克力的評價如何？」→ LangChain Agent 提示：「你想看高評價還是低評價？」

這種交互模式可持續與使用者確認需求，而非單一輸入單一輸出。

#### 4. 智慧聚合 (Aggregation) 與分析

問題：「有哪些用戶最常給負評？」
→ LangChain 主動聚合每個用戶的負評次數後提供給用戶。

#### 5. 主動提出資料洞察 (Proactive Insights)

若查詢為：「巧克力的好評」
→ 除了回傳好評外，主動提供附加的分析：「巧克力在最近幾年評分有提升趨勢，特別是在品牌A和品牌B之間。」

### 實施計劃

未來我們計劃透過以下步驟實現 LangChain 整合：

1. 引入 LangChain 框架，建立智能代理（Agent）
2. 設計多步驟、可迭代的查詢流程
3. 開發適用於資料庫操作的自定義工具集
4. 實作對話記憶機制，支持連續性對話
5. 增強資料分析與洞察能力

透過 LangChain 的引入，我們將顯著提升系統的智能與互動能力，使其不僅能回答使用者的直接問題，還能理解並滿足其背後的深層次資訊需求。
