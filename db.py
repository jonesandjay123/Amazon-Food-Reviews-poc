import os
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# 設定資料庫路徑
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "bbc_news.sqlite")

# 確保資料目錄存在
os.makedirs(DATA_DIR, exist_ok=True)

# 查詢結果快取
cache = {
    "query_cache": {},  # 查詢結果快取
    "last_load_time": 0  # 最後一次加載資料的時間戳
}

def get_db_connection():
    """建立並回傳一個 SQLite 資料庫連線"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"找不到資料庫檔案：{DB_PATH}。請先執行 scripts/download_data.sh 下載並轉換資料。")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 以字典形式回傳結果
    return conn

def execute_query(query: str, params: tuple = None, cache_key: str = None) -> List[Dict[str, Any]]:
    """執行 SQLite 查詢，支援快取結果"""
    # 如果提供了快取鍵且查詢結果已被快取，則回傳快取結果
    if cache_key and cache_key in cache["query_cache"]:
        print(f"使用快取結果：{cache_key}")
        return cache["query_cache"][cache_key]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # 快取結果（如果提供了快取鍵）
        if cache_key:
            cache["query_cache"][cache_key] = results
            
        return results
    except Exception as e:
        print(f"執行查詢時發生錯誤：{e}")
        if 'conn' in locals() and conn:
            conn.close()
        raise e

def check_database() -> bool:
    """檢查資料庫結構並顯示基本資訊"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 獲取表格列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("資料庫表格結構：")
        for table in tables:
            table_name = table['name']
            print(f"- {table_name}")
            
            # 獲取表格的欄位資訊
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col['name']} ({col['type']})")
                
            # 獲取記錄數量
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
            count = cursor.fetchone()['count']
            print(f"  - 記錄數量：{count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"檢查資料庫時發生錯誤：{e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False 