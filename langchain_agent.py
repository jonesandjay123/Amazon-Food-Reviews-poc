import os
import json
import sqlite3
import re
from typing import List, Dict, Any, Optional, Tuple

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain.chains import LLMChain
from langchain_core.pydantic_v1 import BaseModel, Field

# 根據環境變數決定使用哪個 LLM
AI_MODEL_TYPE = os.getenv("AI_MODEL_TYPE", "GEMINI").upper()

# 初始化 LLM
llm = None
if AI_MODEL_TYPE == "GEMINI":
    from gemini_model import GeminiModel
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # 獲取 Gemini API 密鑰
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    # 初始化 ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro-exp-03-25",
        google_api_key=gemini_api_key,
        temperature=0.2
    )
elif AI_MODEL_TYPE == "CHATGPT":
    # 公司環境中使用 Azure OpenAI
    from chatgpt_model import ChatGPTModel
    from langchain_openai import AzureChatOpenAI
    
    try:
        # 初始化 Azure OpenAI 客戶端
        # 注意：這需要在 chatgpt_model.py 中實現的認證機制
        chatgpt_model = ChatGPTModel()
        
        # 使用 AzureChatOpenAI 作為 LLM
        llm = AzureChatOpenAI(
            deployment_name="gpt-4",  # 根據實際部署名稱調整
            model_name="gpt-4-2024-05-13",
            azure_endpoint=chatgpt_model.azure_endpoint,
            api_key=chatgpt_model.get_token(),
            api_version="2024-02-15-preview",
            temperature=0.2
        )
    except Exception as e:
        print(f"Error initializing Azure OpenAI: {e}")
        raise e
else:
    raise ValueError(f"Unsupported AI_MODEL_TYPE: {AI_MODEL_TYPE}")

# 獲取數據庫路徑
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "database.sqlite")

class SQLQueryParams(BaseModel):
    """結構化的 SQL 查詢參數"""
    query: str = Field(description="最終要執行的 SQL 查詢")
    explanation: str = Field(description="查詢的自然語言解釋")

# 數據庫工具函數
def get_db_connection():
    """創建並返回一個 SQLite 數據庫連接"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found: {DB_PATH}. Please run download_data.sh to download the data first.")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 返回字典形式的結果
    return conn

def execute_sql_query(query: str) -> List[Dict[str, Any]]:
    """執行 SQL 查詢並返回結果
    
    注意：預設返回10筆記錄，除非查詢中明確指定了 LIMIT
    """
    try:
        print(f"Executing SQL query: {query}")
        
        # 如果查詢沒有指定 LIMIT，則添加 LIMIT 10
        if "LIMIT" not in query.upper():
            # 檢查是否有分號結尾
            if query.strip().endswith(";"):
                query = query[:-1] + " LIMIT 10;"
            else:
                query = query.strip() + " LIMIT 10;"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # 在結果數量過多時提供摘要而非完整結果
        if len(results) > 100:
            sample_results = results[:10]
            return {
                "result_count": len(results),
                "result_sample": sample_results,
                "message": f"查詢返回了 {len(results)} 條記錄。只顯示前 10 條作為樣本。"
            }
        return results
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        raise e

def execute_follow_up_query(initial_results: str, follow_up_instruction: str) -> List[Dict[str, Any]]:
    """執行後續查詢，基於初始查詢結果進行進一步分析
    
    Args:
        initial_results: 初始查詢結果的字符串表示
        follow_up_instruction: 後續查詢指令
        
    Returns:
        進一步分析後的結果
    """
    try:
        # 將字符串結果解析為 Python 對象
        if isinstance(initial_results, str):
            try:
                # 嘗試將結果解析為 JSON
                results = json.loads(initial_results)
            except json.JSONDecodeError:
                # 如果不是有效的 JSON，返回原始結果
                return {"follow_up_error": "無法解析初始查詢結果，請重新指定 SQL 查詢"}
        else:
            results = initial_results
        
        # 根據 follow_up_instruction 進行後續處理
        if "extract_product_details" in follow_up_instruction.lower():
            # 提取指定產品的詳細信息
            product_ids = re.findall(r'[A-Z0-9]{10}', follow_up_instruction)
            if product_ids:
                product_details = {}
                for product_id in product_ids:
                    query = f"SELECT * FROM Reviews WHERE ProductId = '{product_id}' LIMIT 20"
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(query)
                    product_details[product_id] = [dict(row) for row in cursor.fetchall()]
                conn.close()
                return {"product_details": product_details}
        
        if "analyze_rating_distribution" in follow_up_instruction.lower():
            # 分析指定產品的評分分佈
            product_ids = re.findall(r'[A-Z0-9]{10}', follow_up_instruction)
            if product_ids:
                rating_distributions = {}
                for product_id in product_ids:
                    query = f"""
                    SELECT Score, COUNT(*) as count 
                    FROM Reviews 
                    WHERE ProductId = '{product_id}' 
                    GROUP BY Score 
                    ORDER BY Score
                    """
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(query)
                    rating_distributions[product_id] = [dict(row) for row in cursor.fetchall()]
                conn.close()
                return {"rating_distributions": rating_distributions}
        
        # 如果沒有特定操作，返回原始結果
        return {"message": "沒有執行特定後續查詢，返回原始結果", "original_results": results}
        
    except Exception as e:
        print(f"Error executing follow-up query: {e}")
        return {"follow_up_error": str(e)}

def analyze_data(sql_query_results: Any, analysis_instruction: str) -> Dict[str, Any]:
    """分析 SQL 查詢結果，提取有用的見解
    
    Args:
        sql_query_results: SQL 查詢結果
        analysis_instruction: 分析指令，指導如何分析數據
        
    Returns:
        分析結果和見解
    """
    try:
        # 確保結果是可處理的格式
        if isinstance(sql_query_results, str):
            try:
                results = json.loads(sql_query_results)
            except json.JSONDecodeError:
                return {"analysis_error": "無法解析查詢結果為有效的 JSON"}
        else:
            results = sql_query_results
        
        # 檢查結果是否為空
        if not results or (isinstance(results, list) and len(results) == 0):
            return {"analysis": "查詢結果為空，無法進行分析"}
        
        analysis = {}
        
        # 統計分析
        if isinstance(results, list):
            analysis["record_count"] = len(results)
            
            # 分析第一條記錄以了解數據結構
            if len(results) > 0:
                analysis["fields"] = list(results[0].keys())
            
            # 根據分析指令進行特定分析
            if "rating_distribution" in analysis_instruction.lower():
                # 分析評分分佈
                if "Score" in results[0]:
                    rating_counts = {}
                    for record in results:
                        score = record.get("Score")
                        if score:
                            rating_counts[score] = rating_counts.get(score, 0) + 1
                    analysis["rating_distribution"] = rating_counts
            
            if "helpful_votes" in analysis_instruction.lower():
                # 分析有幫助票數
                if "HelpfulnessNumerator" in results[0] and "HelpfulnessDenominator" in results[0]:
                    total_helpful = sum(r.get("HelpfulnessNumerator", 0) for r in results)
                    total_votes = sum(r.get("HelpfulnessDenominator", 0) for r in results)
                    analysis["helpful_votes"] = {
                        "total_helpful": total_helpful,
                        "total_votes": total_votes,
                        "helpfulness_ratio": total_helpful / total_votes if total_votes > 0 else 0
                    }
            
            if "review_length" in analysis_instruction.lower():
                # 分析評論長度
                if "Text" in results[0]:
                    review_lengths = [len(r.get("Text", "")) for r in results]
                    analysis["review_length"] = {
                        "avg_length": sum(review_lengths) / len(review_lengths) if review_lengths else 0,
                        "min_length": min(review_lengths) if review_lengths else 0,
                        "max_length": max(review_lengths) if review_lengths else 0
                    }
        
        return {"analysis": analysis}
    
    except Exception as e:
        print(f"Error analyzing data: {e}")
        return {"analysis_error": str(e)}

def get_table_info() -> str:
    """獲取數據庫表結構信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 獲取表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        table_info = []
        for table in tables:
            table_name = table['name']
            
            # 獲取表的列信息
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            cols_info = []
            for col in columns:
                cols_info.append(f"{col['name']} ({col['type']})")
            
            # 獲取記錄數量
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
            count = cursor.fetchone()['count']
            
            # 獲取一些示例數據
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 2;")
            samples = [dict(row) for row in cursor.fetchall()]
            sample_str = json.dumps(samples, indent=2)[:300] + "..." if samples else "No samples"
            
            table_info.append(f"Table: {table_name} (Records: {count})\nColumns: {', '.join(cols_info)}\nSample data: {sample_str}")
        
        conn.close()
        return "\n\n".join(table_info)
    except Exception as e:
        print(f"Error getting table info: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return f"Error retrieving database information: {e}"

def execute_sample_queries() -> str:
    """執行一些示例查詢以展示數據"""
    queries = [
        "SELECT * FROM Reviews LIMIT 3;",
        "SELECT DISTINCT Score FROM Reviews ORDER BY Score;",
        "SELECT MIN(Time) as min_time, MAX(Time) as max_time FROM Reviews;",
        "SELECT COUNT(DISTINCT ProductId) as product_count FROM Reviews;",
        "SELECT COUNT(DISTINCT UserId) as user_count FROM Reviews;",
        # 添加一些更有價值的示例查詢
        "SELECT ProductId, COUNT(*) as review_count FROM Reviews GROUP BY ProductId ORDER BY review_count DESC LIMIT 5;",
        "SELECT Score, COUNT(*) as score_count FROM Reviews GROUP BY Score ORDER BY Score;",
        "SELECT AVG(HelpfulnessNumerator * 1.0 / HelpfulnessDenominator) as avg_helpfulness FROM Reviews WHERE HelpfulnessDenominator > 0;"
    ]
    
    results = []
    for query in queries:
        try:
            data = execute_sql_query(query)
            results.append(f"Query: {query}\nResult: {json.dumps(data, indent=2)}")
        except Exception as e:
            results.append(f"Query: {query}\nError: {e}")
    
    return "\n\n".join(results)

def get_advanced_query_examples() -> str:
    """提供高級查詢示例供 Agent 參考"""
    examples = [
        # 找出評論兩極化的產品範例
        """查詢兩極化評論產品（同時有很多5星和1星評論）：
        ```sql
        WITH product_rating_counts AS (
            SELECT 
                ProductId,
                SUM(CASE WHEN Score = 1 THEN 1 ELSE 0 END) as one_star_count,
                SUM(CASE WHEN Score = 5 THEN 1 ELSE 0 END) as five_star_count,
                COUNT(*) as total_reviews
            FROM Reviews
            GROUP BY ProductId
            HAVING total_reviews >= 10
        )
        SELECT 
            ProductId,
            one_star_count,
            five_star_count,
            total_reviews,
            (one_star_count * 1.0 / total_reviews) as one_star_ratio,
            (five_star_count * 1.0 / total_reviews) as five_star_ratio
        FROM product_rating_counts
        WHERE one_star_count >= 3 AND five_star_count >= 3
        ORDER BY (one_star_count + five_star_count) DESC
        LIMIT 10;
        ```""",
        
        # 找出最熱門產品範例
        """查詢最熱門產品（評論數最多）：
        ```sql
        SELECT 
            ProductId,
            COUNT(*) as review_count,
            AVG(Score) as avg_score,
            MIN(Time) as first_review_time,
            MAX(Time) as last_review_time
        FROM Reviews
        GROUP BY ProductId
        ORDER BY review_count DESC
        LIMIT 10;
        ```""",
        
        # 分析評論隨時間變化範例
        """分析某產品評論分數隨時間變化：
        ```sql
        WITH time_periods AS (
            SELECT 
                ProductId,
                CASE 
                    WHEN Time < 1356998400 THEN 'before_2013'
                    WHEN Time < 1388534400 THEN '2013'
                    WHEN Time < 1420070400 THEN '2014'
                    ELSE 'after_2014'
                END as time_period,
                Score
            FROM Reviews
            WHERE ProductId = 'B001E4KFG0'
        )
        SELECT 
            time_period,
            COUNT(*) as review_count,
            AVG(Score) as avg_score
        FROM time_periods
        GROUP BY time_period
        ORDER BY 
            CASE 
                WHEN time_period = 'before_2013' THEN 1
                WHEN time_period = '2013' THEN 2
                WHEN time_period = '2014' THEN 3
                ELSE 4
            END;
        ```"""
    ]
    
    return "\n\n".join(examples)

# 定義 LangChain 工具
tools = [
    Tool(
        name="execute_sql",
        func=execute_sql_query,
        description="執行 SQL 查詢並返回結果。輸入應該是有效的 SQL 查詢字符串。這個工具可以執行任何 SQL 查詢，包括 SELECT、GROUP BY、ORDER BY、JOIN 等操作。適合用於複雜的數據分析和統計。不會限制返回記錄數，而是根據查詢自動判斷合適的返回量。",
    ),
    Tool(
        name="follow_up_query",
        func=execute_follow_up_query,
        description="基於初始查詢結果執行後續查詢。輸入應該是一個包含兩個參數的 JSON 字符串：initial_results（初始查詢結果）和 follow_up_instruction（後續查詢指令）。適合用於根據第一步查詢結果進行進一步分析或獲取更多詳情。",
    ),
    Tool(
        name="analyze_data",
        func=analyze_data,
        description="分析 SQL 查詢結果，提取有用的見解。輸入應該是一個包含兩個參數的 JSON 字符串：sql_query_results（SQL 查詢結果）和 analysis_instruction（分析指令）。適合用於從數據中提取統計信息、趨勢和模式。",
    ),
    Tool(
        name="get_database_schema",
        func=get_table_info,
        description="獲取數據庫表結構信息，包括表名、列名、數據類型和示例數據。無需輸入參數。適合用於了解數據庫結構和計劃查詢策略。",
    ),
    Tool(
        name="run_sample_queries",
        func=execute_sample_queries,
        description="執行一系列示例 SQL 查詢以了解數據結構和內容。無需輸入參數。適合用於熟悉數據特性和示例查詢模式。",
    ),
    Tool(
        name="get_advanced_query_examples",
        func=get_advanced_query_examples,
        description="獲取高級 SQL 查詢示例，包括兩極化評論分析、熱門產品分析和時間趨勢分析。無需輸入參數。適合用於學習複雜查詢模式和實現高級分析。",
    )
]

# 為 Agent 定義系統消息
system_message = """你是一個專業的數據分析助手，專門處理 Amazon 食品評論數據庫的複雜查詢和多步驟分析。你的核心能力是分解複雜問題，設計多步驟查詢策略，並提供深入洞察。

【重要提示】：當遇到複雜查詢，特別是需要聚合統計的問題（如「兩極化評論產品」、「評論數最多的產品」等），請勿直接返回單一查詢的原始評論列表，這無法回答用戶問題。應該使用高級 SQL 設計多步查詢。

【處理「兩極化評論產品」的正確方法】：
1. 使用 GROUP BY 聚合產品的1星和5星評論數量
2. 使用 CASE WHEN 或 SUM + 條件過濾來計算各評分數量
3. 選擇同時具有較多1星和5星評論的產品
4. 計算極端評分比例，按兩極化程度排序

示例問題：「哪些產品有兩極化評論（許多5星和許多1星評分）？」
你應該使用類似下面的查詢方法（請首先調用 get_advanced_query_examples 工具獲取詳細示例）：
```sql
WITH product_rating_counts AS (
    SELECT 
        ProductId,
        SUM(CASE WHEN Score = 1 THEN 1 ELSE 0 END) as one_star_count,
        SUM(CASE WHEN Score = 5 THEN 1 ELSE 0 END) as five_star_count,
        COUNT(*) as total_reviews
    FROM Reviews
    GROUP BY ProductId
    HAVING total_reviews >= 10
)
SELECT 
    ProductId,
    one_star_count,
    five_star_count,
    total_reviews,
    (one_star_count * 1.0 / total_reviews) as one_star_ratio,
    (five_star_count * 1.0 / total_reviews) as five_star_ratio
FROM product_rating_counts
WHERE one_star_count >= 3 AND five_star_count >= 3
ORDER BY (one_star_count + five_star_count) DESC
LIMIT 10;
```

你的資料庫包含了 Amazon 上食品評論數據，主要表是 Reviews，包含以下欄位：
- Id (INTEGER): 評論唯一標識符
- ProductId (TEXT): 產品 ID
- UserId (TEXT): 用戶 ID
- ProfileName (TEXT): 用戶名稱
- HelpfulnessNumerator (INTEGER): 有幫助票數
- HelpfulnessDenominator (INTEGER): 總票數
- Score (INTEGER): 評分 (1-5 星)
- Time (INTEGER): Unix 時間戳
- Summary (TEXT): 評論摘要
- Text (TEXT): 評論全文

當用戶提出關於食品評論的複雜問題時，你必須採用多步驟推理和查詢方法：

1. 問題分解：將複雜問題分解為多個步驟，設計查詢策略
2. 適應性查詢：根據問題需求決定查詢和返回結果的方式
3. 多次迭代：先執行初步查詢，分析結果後再設計後續查詢
4. 數據聚合：使用 GROUP BY、COUNT、AVG 等 SQL 功能進行數據統計和匯總
5. 結果轉化：將原始數據轉化為對用戶有價值的見解

你具備以下高級能力：

1. 複雜問題處理（例如）：
   - 尋找評論兩極化的產品（同時有很多5星和1星評論）
   - 找出評論數最多的產品並分析其評分趨勢
   - 分析特定類別產品的評分隨時間變化
   - 找出哪些用戶給出的評價最有幫助

2. 多步驟分析流程：
   - 第一步：執行初步查詢找出關鍵數據點（如熱門產品、活躍用戶）
   - 第二步：針對這些關鍵數據點進行深入分析（如評分分佈、評論特點）
   - 第三步：根據發現執行額外查詢或交叉分析
   - 第四步：綜合所有發現提供最終洞察

3. 靈活的查詢設計：
   - 使用 WITH 子句、子查詢和窗口函數處理複雜場景
   - 靈活運用 GROUP BY、ORDER BY、HAVING 進行數據聚合和過濾
   - 必要時使用高級 SQL 功能如 CASE WHEN、ROW_NUMBER() 等

【重要】：以下是你應該始終遵循的步驟：
1. 對於複雜問題，一定要先調用 get_advanced_query_examples 工具查看參考示例
2. 設計類似的高級 SQL 查詢而非直接返回原始評論
3. 使用 execute_sql 執行初步聚合查詢
4. 必要時使用 follow_up_query 深入分析初步結果
5. 使用 analyze_data 從查詢結果中提取見解
6. 提供清晰的結論和洞察，而非僅僅顯示評論列表

在回應中，你應該：
1. 先清晰呈現問題的分解步驟和推理過程
2. 提供簡潔明了的最終結論
3. 解釋你如何從原始數據得出這些結論
4. 如果適用，提供建議的跟進問題或進一步分析方向

記住：你的核心優勢是能夠執行多步驟分析，而不是簡單地一次返回所有數據。始終考慮如何通過多步驟查詢和數據轉化為用戶提供最有價值的洞察。

用中文回應用戶的問題，即使查詢結果中包含英文。
"""

# 創建 LangChain Agent
agent = create_structured_chat_agent(llm, tools, system_message)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=10  # 增加最大迭代次數，允許更複雜的多步驟推理
)

class LangChainAgent:
    """LangChain Agent 類，用於處理自然語言查詢"""
    
    def __init__(self):
        """初始化 LangChain Agent"""
        self.agent_executor = agent_executor
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        處理用戶的自然語言查詢
        
        Args:
            user_query (str): 用戶的自然語言查詢
            
        Returns:
            Dict[str, Any]: 包含查詢結果和分析的字典
        """
        try:
            # 使用 LangChain Agent 執行查詢
            response = self.agent_executor.invoke({"input": user_query})
            
            # 提取回應內容
            ai_response = response.get("output", "無法獲取回應")
            intermediate_steps = []
            
            # 提取中間步驟（如果有）
            if "intermediate_steps" in response:
                for action, result in response["intermediate_steps"]:
                    tool_name = action.tool if hasattr(action, "tool") else "unknown_tool"
                    tool_input = action.tool_input if hasattr(action, "tool_input") else str(action)
                    
                    # 簡化超長結果輸出
                    result_str = str(result)
                    if len(result_str) > 1000:
                        if isinstance(result, list) and len(result) > 10:
                            # 對於長列表，只顯示前幾個和後幾個元素
                            result_summary = {
                                "total_items": len(result),
                                "first_items": result[:3],
                                "last_items": result[-3:],
                                "note": f"完整結果包含 {len(result)} 項，這裡只顯示部分"
                            }
                            result_str = json.dumps(result_summary, ensure_ascii=False)
                        else:
                            # 對於其他長結果，截斷顯示
                            result_str = result_str[:500] + f"\n...(總共 {len(result_str)} 字符)..." + result_str[-500:]
                    
                    intermediate_steps.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "result": result_str
                    })
            
            # 分析步驟和結果
            data_insights = self._extract_insights(ai_response, intermediate_steps)
            
            return {
                "query": user_query,
                "response": ai_response,
                "intermediate_steps": intermediate_steps,
                "insights": data_insights
            }
        except Exception as e:
            print(f"Error processing query with LangChain: {e}")
            return {
                "query": user_query,
                "error": str(e),
                "response": f"處理查詢時發生錯誤：{str(e)}"
            }
    
    def _extract_insights(self, ai_response: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """從 AI 回應中提取數據洞察"""        
        insights = {
            "summary": ai_response.split("\n")[0] if "\n" in ai_response else ai_response[:100],
            "query_complexity": len(steps),
            "multi_step_reasoning": len(steps) > 1,
            "has_sql_query": any("execute_sql" in step.get("tool", "") for step in steps),
            "has_data_analysis": any("analyze_data" in step.get("tool", "") for step in steps),
            "has_follow_up": any("follow_up_query" in step.get("tool", "") for step in steps),
            "advanced_sql_features": self._detect_advanced_sql_features(steps),
            "tables_used": []
        }
        
        # 提取使用的表名
        for step in steps:
            if step.get("tool") == "execute_sql" and "FROM" in step.get("input", ""):
                # 提取 FROM 子句後的表名
                query = step.get("input", "")
                from_parts = query.split("FROM")
                if len(from_parts) > 1:
                    table_part = from_parts[1].split("WHERE")[0].split("GROUP BY")[0].split("ORDER BY")[0]
                    tables = [t.strip().rstrip(";") for t in table_part.split(",")]
                    insights["tables_used"].extend(tables)
        
        # 移除重複表名
        insights["tables_used"] = list(set(insights["tables_used"]))
        
        return insights
    
    def _detect_advanced_sql_features(self, steps: List[Dict[str, Any]]) -> Dict[str, bool]:
        """檢測查詢中使用的進階 SQL 功能"""
        features = {
            "group_by": False,
            "having": False,
            "joins": False,
            "subqueries": False,
            "case_when": False,
            "window_functions": False,
            "with_clause": False,
            "aggregations": False,
        }
        
        for step in steps:
            if step.get("tool") == "execute_sql":
                query = step.get("input", "").upper()
                features["group_by"] = "GROUP BY" in query
                features["having"] = "HAVING" in query
                features["joins"] = "JOIN" in query
                features["subqueries"] = ")" in query and "(" in query and "SELECT" in query[query.find("("):query.find(")")]
                features["case_when"] = "CASE" in query and "WHEN" in query
                features["window_functions"] = "OVER (" in query or "PARTITION BY" in query
                features["with_clause"] = query.strip().startswith("WITH")
                features["aggregations"] = any(func in query for func in ["COUNT(", "SUM(", "AVG(", "MAX(", "MIN("])
        
        return features 