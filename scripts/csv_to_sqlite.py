import pandas as pd
import sqlite3
import sys
import os

# 建立資料目錄（如果不存在）
os.makedirs("data", exist_ok=True)

# 讀取 CSV 檔案
print("正在讀取 BBC News CSV 檔案...")
df = pd.read_csv("data/bbc-news.csv")

# 連接到 SQLite 資料庫
print("正在創建 SQLite 資料庫...")
con = sqlite3.connect("data/bbc_news.sqlite")

# 建立資料表（添加 id 自動遞增字段）
print("正在將資料轉換為 SQLite 資料表...")
cursor = con.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    title TEXT,
    text TEXT
)
''')
con.commit()

# 將資料存入資料表
df.to_sql("news_temp", con, if_exists="replace", index=False)

# 從臨時資料表複製數據到主資料表（用於保持 id 自增）
cursor.execute('''
INSERT INTO news (category, title, text)
SELECT category, title, text FROM news_temp
''')
con.commit()

# 刪除臨時資料表
cursor.execute("DROP TABLE news_temp")
con.commit()

# 關閉資料庫連接
con.close()

print("BBC News 資料已成功轉換為 SQLite 資料庫 (data/bbc_news.sqlite)")
print(f"總共轉換了 {len(df)} 筆新聞記錄") 