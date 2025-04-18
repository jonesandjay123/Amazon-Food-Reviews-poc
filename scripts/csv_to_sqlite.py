import pandas as pd, sqlite3, os

CSV_PATH = "data/bbc-news.csv"
DB_PATH  = "data/bbc_news.sqlite"

print("Reading BBC News CSV file…")
df = pd.read_csv(CSV_PATH)

assert {"category", "text"}.issubset(df.columns), "CSV 欄位不符！"

print("Creating SQLite database…")
con = sqlite3.connect(DB_PATH)
df.to_sql("news", con, if_exists="replace", index=False)
con.close()
print("SQLite table [news] created with", len(df), "rows.")
