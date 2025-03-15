# 電影推薦系統 API 示例

## 基本查詢

1. 獲取所有電影列表（分頁展示，每頁 10 條）

```
GET /api/movies?page=1&limit=10
```

2. 搜索特定電影（根據標題）

```
GET /api/movies?query=Titanic
```

3. 根據類型過濾電影

```
GET /api/movies?genre=Action&page=1&limit=20
```

4. 獲取電影詳情

```
GET /api/movies/5726
```

## 演員和導演查詢

1. 獲取特定演員的電影

```
GET /api/actor/Tom%20Hanks
```

2. 獲取特定導演的電影

```
GET /api/director/Christopher%20Nolan
```

## 自然語言查詢

使用自然語言搜索電影（需要 Gemini API 支持）:

```
POST /api/search-ai
Content-Type: application/json

{
  "query": "推薦一些90年代的經典動作電影"
}
```

## 調試端點

1. 檢查全局變量狀態

```
GET /debug/use_global
```

2. 列出導演數據

```
GET /debug/directors
```

## 使用說明

1. 先確保執行環境已設置好 Kaggle API 憑證和 Gemini API 密鑰
2. 第一次訪問時系統會自動從 Kaggle 下載數據或使用本地數據（如果存在）
3. 查詢結果會自動緩存以提升性能
4. 使用自然語言查詢時，請提供明確的、包含足夠上下文的問題

## 錯誤處理

所有 API 端點在出現錯誤時會返回標準錯誤格式：

```json
{
  "error": "錯誤描述信息"
}
```

錯誤碼使用標準 HTTP 狀態碼：

- 400: 請求無效
- 404: 資源不存在
- 500: 服務器內部錯誤
