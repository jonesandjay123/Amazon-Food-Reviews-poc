# Amazon Fine Food Reviews API

基於 Kaggle Amazon Fine Food Reviews 數據集的 RESTful API，支持食品評論查詢，以及使用 Gemini API 的自然語言查詢。

## 主要特點

- 🍕 使用 SQLite 資料庫存取 Amazon 食品評論數據
- 🔍 高效的查詢緩存機制，提升查詢速度
- 💬 集成 Google Gemini API 進行自然語言處理
- 📚 完整的 Swagger API 文檔
- 🧠 智能評論搜索與分析
- 🔗 LangChain 代理增強的複雜查詢和多步驟分析

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
   USE_LANGCHAIN=true  # 可選，設置為預設啟用 LangChain
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

2. **使用 LangChain 進行自然語言查詢**：
   
   ```bash
   curl -X POST http://localhost:5000/api/query \
     -H "Content-Type: application/json" \
     -d '{"query":"找出有兩極化評論的巧克力產品", "force_langchain": true}'
   ```

3. **獲取評論列表**：

   ```bash
   curl http://localhost:5000/api/reviews?limit=10&min_score=5
   ```

4. **獲取特定產品的評論**：

   ```bash
   curl http://localhost:5000/api/product/B001E4KFG0
   ```

5. **搜索評論**：

   ```bash
   curl http://localhost:5000/api/search?q=delicious
   ```

6. **檢查系統狀態**：
   ```bash
   curl http://localhost:5000/api/debug
   ```

7. **切換 LangChain 模式**：
   ```bash
   curl -X POST http://localhost:5000/api/toggle_langchain \
     -H "Content-Type: application/json" \
     -d '{"enable_langchain": true}'
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

4. **LangChain 相關錯誤**：
   - 確認已安裝所有必要的 LangChain 相關套件
   - 檢查 AI 模型 API 密鑰是否正確
   - 查看日誌中是否有與 LangChain 相關的具體錯誤訊息

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
- `GET /api/system_status` - 獲取詳細系統狀態，包括 LangChain 是否可用
- `POST /api/toggle_langchain` - 切換 LangChain 模式

## LangChain 增強功能

本項目現已通過 LangChain 集成提供進階功能，實現更複雜的自然語言處理和多步驟推理。LangChain 使用工具鏈將複雜查詢分解為一系列步驟。

### 啟用 LangChain

有三種方式可以啟用 LangChain：

1. **環境變量**：在環境或 `.env` 文件中設置 `USE_LANGCHAIN=true`
2. **界面切換**：使用聊天界面右上角的開關
3. **API 參數**：在 API 請求中添加 `"force_langchain": true`

```bash
# 通過 API 切換 LangChain 模式的示例
curl -X POST http://localhost:5000/api/toggle_langchain \
  -H "Content-Type: application/json" \
  -d '{"enable_langchain": true}'
```

### LangChain 工作原理

LangChain 代理使用多個專業工具來處理複雜查詢：

1. **問題分解**：將用戶的自然語言問題分解為多個處理步驟
2. **動態查詢**：根據中間結果動態調整後續查詢策略
3. **數據聚合**：使用高級 SQL 功能（如 GROUP BY、HAVING、WITH 子句等）進行數據分析
4. **結果解釋**：提供詳細的分析和推理過程

LangChain 代理使用的主要工具包括：

- **SQL 查詢執行器**：執行複雜的 SQL 查詢並返回結果
- **數據分析器**：從查詢結果中提取統計信息和洞察
- **後續查詢處理器**：根據初步查詢結果進行進一步的分析
- **資料庫結構分析器**：獲取數據庫表結構信息
- **示例查詢運行器**：執行預設的樣本查詢以了解數據特性

### 比較標準 RAG 與 LangChain

下表顯示了標準 RAG 方法和 LangChain 增強查詢之間的主要差異：

| 功能 | 標準 RAG | LangChain 增強 |
|-----|---------|---------------|
| 查詢複雜度 | 單步驟，直接映射到 SQL | 多步驟推理，動態查詢構建 |
| 自我修正 | 無 | 有，可根據中間結果調整查詢 |
| 分析深度 | 基礎 | 深入，具備數據聚合能力 |
| 互動性 | 無 | 可以建議相關查詢 |
| 數據洞察 | 僅限直接結果 | 提供更廣泛的上下文和模式 |
| SQL 複雜性 | 簡單 WHERE 條件 | 支持高級 SQL 功能（WITH 子句、窗口函數等）|
| 多表操作 | 有限 | 完整支持多表關聯查詢 |
| 結果可視化 | 基礎 | 提供結構化數據和解釋性文本 |
| 推理透明度 | 不透明 | 顯示完整推理過程和中間步驟 |

### LangChain 適用的複雜查詢示例

LangChain 在需要多個步驟或更深入分析的複雜查詢中表現卓越。嘗試以下示例以體驗差異：

1. **多步驟聚合查詢**：
   - "最近3年中，哪5個產品有最多的評論？"
   - "顯示評分高於平均值且至少有10條評論的產品"

2. **趨勢分析**：
   - "巧克力產品的平均評分是否隨時間有所改善？"
   - "人們是否為高評分產品寫更長的評論？"

3. **複雜過濾與分析**：
   - "找出同時給出過5星和1星評分的用戶，並比較他們的評論風格"
   - "哪些產品有兩極化評論（許多5星和許多1星評分）？"

4. **比較分析**：
   - "比較產品 B001E4KFG0 和 B000LQOCH0 的評論，分析情感和常見關鍵詞"
   - "高評分產品的負面評論中最常見的抱怨是什麼？"

5. **數據深度分析**：
   - "哪些評論在有幫助性方面評分最高？分析這些評論的共同特徵"
   - "分析不同評分級別(1-5星)的評論長度分佈差異"
   - "找出評論數據中的季節性模式，如巧克力產品在節日期間評分是否更高"

6. **用戶行為分析**：
   - "哪些用戶發表的評論最多？他們的評論風格有何特點？"
   - "找出那些評論與大多數人意見不同的用戶（例如，他們給通常高評分的產品低評分）"

### 使用高級SQL功能

LangChain 能夠生成並執行包含以下高級 SQL 功能的查詢：

1. **WITH 子句**：用於複雜的多步驟查詢
   ```sql
   WITH product_stats AS (
     SELECT ProductId, AVG(Score) as avg_score, COUNT(*) as review_count
     FROM Reviews
     GROUP BY ProductId
     HAVING review_count >= 10
   )
   SELECT * FROM product_stats WHERE avg_score > 4
   ```

2. **窗口函數**：用於比較和排序
   ```sql
   SELECT ProductId, Score, 
          AVG(Score) OVER (PARTITION BY ProductId) as avg_product_score
   FROM Reviews
   WHERE ProductId IN ('B001E4KFG0', 'B000LQOCH0')
   ```

3. **複雜條件邏輯**：使用 CASE WHEN 進行條件處理
   ```sql
   SELECT ProductId,
          SUM(CASE WHEN Score = 5 THEN 1 ELSE 0 END) as five_star_count,
          SUM(CASE WHEN Score = 1 THEN 1 ELSE 0 END) as one_star_count
   FROM Reviews
   GROUP BY ProductId
   ```

### 測試差異

要體驗 LangChain 的全部功能，請嘗試使用和不使用 LangChain 運行相同的複雜查詢：

1. 關閉 LangChain 並提問："哪些巧克力產品的評分至少為4星，並且有最有幫助的評論？"
2. 開啟 LangChain 並提出相同問題。

注意 LangChain 版本如何提供：
- 更全面的結果
- 逐步推理過程
- 額外洞察
- 更好的結構化數據

### 查看 LangChain 的推理過程

使用啟用 LangChain 的界面時，您將看到"顯示推理步驟"下拉選項，展示 LangChain 如何分解您的查詢以及到達答案的中間步驟。這種透明度有助於理解系統的推理過程。

每個推理步驟包括：
1. **使用的工具**：如 SQL 查詢執行器、數據分析器等
2. **輸入**：傳遞給工具的參數或問題
3. **輸出**：工具返回的結果
4. **後續行動決策**：LangChain 如何基於已有結果決定下一步

### LangChain UI 功能

在聊天界面中使用 LangChain 時，您會看到以下專用功能：

1. **LangChain 開關**：右上角的切換按鈕，可立即切換查詢模式
2. **查詢方法標籤**：每個回應都會顯示使用的查詢方法（標準 RAG 或 LangChain）
3. **推理步驟展示**：可展開的區域，顯示 LangChain 的完整推理過程
4. **中間結果查看**：可查看每個步驟的詳細結果
5. **響應格式化**：增強的響應格式，包括評分、評論文本和統計數據的清晰展示

## 未來規劃

我們計劃通過以下方式增強 LangChain 集成：
1. 添加更多專門工具進行深度分析
2. 實現對話記憶功能，支持後續問題
3. 支持更複雜的數據可視化功能
4. 為所有查詢添加自動洞察生成
5. 開發更多特定於食品評論的分析模式
6. 提供自定義查詢模板功能，允許用戶保存和重用常用分析模式
7. 集成高級數據圖表生成功能
8. 擴展多語言支持，允許使用更多語言進行自然語言查詢
