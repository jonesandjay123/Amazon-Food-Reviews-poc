import pandas as pd, sqlite3, os

# CSV 路徑及資料庫路徑設定 (若檔案不存在就提示下載連結)
CSV_PATH = "data/bbc-news.csv"
DB_PATH  = "data/bbc_news.sqlite"

# 檢查資料庫是否已存在
if os.path.exists(DB_PATH):
    print("DB already exists, skipping.")
    exit(0)

# 確保 data 資料夾存在
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

# 檢查 CSV 檔案是否存在
if not os.path.exists(CSV_PATH):
    print("Error: CSV file not found at", CSV_PATH)
    print("Please download the dataset manually from:")
    print("https://huggingface.co/datasets/hf-internal/bbc-text/resolve/main/bbc-text.csv")
    print("Then rename it to 'bbc-news.csv' and place it in the 'data/' folder.")
    exit(1)

print("Reading BBC News CSV file…")
df = pd.read_csv(CSV_PATH)

assert {"category", "text"}.issubset(df.columns), "CSV 欄位不符！"

print("Creating SQLite database…")
con = sqlite3.connect(DB_PATH)
df.to_sql("news", con, if_exists="replace", index=False)
con.close()
print("SQLite table [news] created with", len(df), "rows.")
