import os
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Set database path
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "bbc_news.sqlite")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Query result cache
cache = {
    "query_cache": {},  # Query result cache
    "last_load_time": 0  # Timestamp of last data load
}

def get_db_connection():
    """Establish and return a SQLite database connection"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found: {DB_PATH}. Please run scripts/download_data.sh to download and convert data first.")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return results as dictionaries
    return conn

def execute_query(query: str, params: tuple = None, cache_key: str = None) -> List[Dict[str, Any]]:
    """Execute SQLite query, supporting result caching"""
    # If a cache key is provided and the query result is already cached, return cached result
    if cache_key and cache_key in cache["query_cache"]:
        print(f"Using cached result: {cache_key}")
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
        
        # Cache result (if cache key is provided)
        if cache_key:
            cache["query_cache"][cache_key] = results
            
        return results
    except Exception as e:
        print(f"Error executing query: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        raise e

def check_database() -> bool:
    """Check database structure and display basic information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("Database table structure:")
        for table in tables:
            table_name = table['name']
            print(f"- {table_name}")
            
            # Get table column information
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col['name']} ({col['type']})")
                
            # Get record count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name};")
            count = cursor.fetchone()['count']
            print(f"  - Record count: {count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error checking database: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False 